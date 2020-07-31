import json
import logging
import re
import urllib.parse
from pathlib import Path
from typing import Any
from typing import cast
from typing import Dict
from typing import List
from typing import Optional

import dateutil.parser
import requests
from bs4 import BeautifulSoup
from nefelibata.announcers import Announcer
from nefelibata.announcers import Comment
from nefelibata.announcers import Response
from nefelibata.announcers import User
from nefelibata.post import Post
from nefelibata.utils import json_storage

_logger = logging.getLogger(__name__)


# languages supported by IndieNews
SUPPORTED_LANGUAGES = ["en", "sv", "de", "fr", "nl", "ru"]

# URL to send users to comment on posts via webmention
COMMENT_URL = "https://commentpara.de/"


def get_webmention_endpoint(url) -> Optional[str]:
    # start with a HEAD request
    response = requests.head(url)
    if "Link" in response.headers:
        header = response.headers["Link"]
        links = requests.utils.parse_header_links(header)
        for link in links:
            if link["rel"] == "webmention":
                return cast(str, urllib.parse.urljoin(url, link["url"]))
    elif "text/html" not in response.headers.get("Content-Type", ""):
        return None

    response = requests.get(url)
    html = response.content
    soup = BeautifulSoup(html, "html.parser")
    link = soup.find(rel="webmention")
    if link:
        return cast(str, urllib.parse.urljoin(url, link["href"]))

    return None


def get_response_from_child(child: Dict[str, Any], target: str) -> Response:
    # for the source, let's try to find a name, else fall back to URL
    source = child.get("name") or child.get("url") or "Unknown"

    url = child.get("url") or "#"
    id_ = f'webmention:{child["wm-id"]}'

    # for timestamp we fall back to when the response was received
    timestamp = child.get("published") or child["wm-received"]
    timestamp = dateutil.parser.parse(timestamp).isoformat()

    user: User = {
        "name": child["author"]["name"],
        "image": child["author"]["photo"],
        "url": child["author"]["url"],
    }

    if "content" in child:
        text = child["content"].get("text", "")
        html = child["content"].get("html", "")
        summary = summarize(html or text, target)
    else:
        text = html = summary = ""

    comment: Comment = {"text": text, "summary": summary, "html": html}

    return {
        "source": source,
        "url": url,
        "id": id_,
        "timestamp": timestamp,
        "user": user,
        "comment": comment,
    }


def summarize(text: str, target: Optional[str] = None) -> str:
    soup = BeautifulSoup(text, "html.parser")

    # search for a paragraph containing the link
    if target:
        anchor = soup.find("a", href=target)
        if anchor:
            p = anchor.find_parent("p")
            if p:
                # what should we do with really long paragraphs? is that
                # even a problem?
                return str(p.get_text())

    # return the first line
    text = soup.get_text()
    lines = text.split("\n")

    return lines[0]


class WebmentionAnnouncer(Announcer):

    id = "webmention"
    name = "Webmention"
    url_header = "webmention-url"

    def __init__(
        self, root: Path, config: Dict[str, Any], endpoint: str,
    ):
        super().__init__(root, config)

        self.endpoint = endpoint  # used only in template

    def should_announce(self, post: Post) -> bool:
        # Since the plugin can announce to multiple places, and new places can be added
        # after a post has been published, we always try to find new links to which we
        # should send mentions.
        return True

    def announce(self, post: Post) -> str:
        _logger.info("Discovering links supporting webmention...")

        # store successful mentions and their responses in a JSON file
        post_directory = post.file_path.parent
        storage = post_directory / "webmentions.json"
        with json_storage(storage) as webmentions:
            source = urllib.parse.urljoin(self.config["url"], post.url)

            soup = BeautifulSoup(post.html, "html.parser")
            for el in soup.find_all("a", href=re.compile("http")):
                target = el.attrs.get("href")
                if target not in webmentions:
                    webmentions[target] = self._send_mention(source, target)
                elif (
                    webmentions[target]["success"]
                    and isinstance(webmentions[target]["content"], dict)
                    and webmentions[target]["content"].get("status") == "queued"
                ):
                    webmentions[target] = self._update_webmention(webmentions[target])

            keywords = [
                keyword.strip()
                for keyword in post.parsed.get("keywords", "").split(",")
            ]
            if "indieweb" in keywords or "indienews" in keywords:
                language = post.parsed.get("language") or self.config["language"]
                if language not in SUPPORTED_LANGUAGES:
                    _logger.error(
                        f'Currently IndieNews supports only the following languages: {", ".join(SUPPORTED_LANGUAGES)}',
                    )
                else:
                    target = f"https://news.indieweb.org/{language}"
                    if target not in webmentions:
                        webmentions[target] = self._send_mention(source, target)
                    elif (
                        webmentions[target]["success"]
                        and isinstance(webmentions[target]["content"], dict)
                        and webmentions[target]["content"].get("status") == "queued"
                    ):
                        webmentions[target] = self._update_webmention(
                            webmentions[target],
                        )

        _logger.info("Success!")

        return COMMENT_URL

    def _send_mention(self, source: str, target: str) -> Dict[str, Any]:
        _logger.info(f"Checking {target}")

        endpoint = get_webmention_endpoint(target)
        if not endpoint:
            _logger.info("No endpoint found")
            return {"success": False}

        _logger.info(f"Sending mention to {endpoint}")
        payload = {
            "source": source,
            "target": target,
        }
        response = requests.post(endpoint, data=payload)
        webmention: Dict[str, Any] = {"success": response.ok}
        if response.ok:
            try:
                webmention["content"] = response.json()
            except ValueError:
                webmention["content"] = response.text

        return webmention

    def _update_webmention(self, webmention: Dict[str, Any]) -> Dict[str, Any]:
        _logger.info("Found queued webmention response, checking for update")

        location = webmention["content"]["location"]
        try:
            response = requests.get(location)
        except Exception:
            return webmention

        if response.ok:
            try:
                webmention["content"] = response.json()
            except ValueError:
                webmention["content"] = response.text

        return webmention

    def collect(self, post: Post) -> List[Response]:
        _logger.info("Collecting webmentions")

        target = urllib.parse.urljoin(self.config["url"], post.url)
        url = "https://webmention.io/api/mentions.jf2"
        payload = {"target": target}
        response = requests.get(url, params=payload)
        try:
            response.raise_for_status()
        except Exception:
            _logger.exception(f"Failed to load webmentions for {target}")
            return []

        feed = response.json()

        _logger.info("Success!")

        return [get_response_from_child(child, target) for child in feed["children"]]
