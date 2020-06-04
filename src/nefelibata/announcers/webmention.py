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

_logger = logging.getLogger(__name__)


# languages supported by IndieNews
SUPPORTED_LANGUAGES = ["en", "sv", "de", "fr", "nl", "ru"]

# URL to send users to comment on posts via webmention
COMMENT_URL = "https://commentpara.de/"


def get_webmention_endpoint(url) -> Optional[str]:
    # start with a HEAD request
    r = requests.head(url)
    if "Link" in r.headers:
        header = r.headers["Link"]
        links = requests.utils.parse_header_links(header)
        for link in links:
            if link["rel"] == "webmention":
                return cast(str, urllib.parse.urljoin(url, link["url"]))

    r = requests.get(url)
    html = r.content
    soup = BeautifulSoup(html, "html.parser")
    link = soup.find(rel="webmention")
    if link:
        return cast(str, urllib.parse.urljoin(url, link["href"]))

    return None


def get_response_from_child(child: Dict[str, Any]) -> Response:
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

    text = child["content"].get("text", "") if "content" in child else ""
    comment: Comment = {"text": text}

    return {
        "source": source,
        "url": url,
        "id": id_,
        "timestamp": timestamp,
        "user": user,
        "comment": comment,
    }


class WebmentionAnnouncer(Announcer):

    id = "webmention"
    name = "Webmention"
    url_header = "webmention-url"

    def __init__(
        self,
        root: Path,
        config: Dict[str, Any],
        endpoint: str,
        post_to_indienews: bool,
    ):
        super().__init__(root, config)

        self.endpoint = endpoint  # used only in template
        self.post_to_indienews = post_to_indienews

    def announce(self, post: Post) -> str:
        _logger.info("Discovering links supporting webmention...")

        source = urllib.parse.urljoin(self.config["url"], post.url)

        soup = BeautifulSoup(post.html, "html.parser")
        for el in soup.find_all("a", href=re.compile("http")):
            target = el.attrs.get("href")
            _logger.info(f"Checking {target}")
            self._send_mention(source, target)

        if self.post_to_indienews:
            language = post.parsed.get("language") or self.config["language"]
            if language not in SUPPORTED_LANGUAGES:
                _logger.error(
                    f'Currently IndieNews supports only the following languages: {", ".join(SUPPORTED_LANGUAGES)}',
                )
            else:
                target = f"https://news.indieweb.org/{language}"
                _logger.info(f"Checking {target}")
                self._send_mention(source, target)
                with open(post.file_path.parent / "indienews.json", "w") as fp:
                    fp.write(json.dumps({"posted": True}))

        _logger.info("Success!")

        return COMMENT_URL

    def _send_mention(self, source: str, target: str) -> None:
        endpoint = get_webmention_endpoint(target)
        if endpoint:
            _logger.info(f"Sending mention to {endpoint}")
            payload = {
                "source": source,
                "target": target,
            }
            requests.post(endpoint, data=payload)

    def collect(self, post: Post) -> List[Response]:
        _logger.info("Collecting webmentions")

        target = urllib.parse.urljoin(self.config["url"], post.url)
        url = "https://webmention.io/api/mentions.jf2"
        payload = {"target": target}
        r = requests.get(url, params=payload)
        feed = json.loads(r.content)

        _logger.info("Success!")

        return [get_response_from_child(child) for child in feed["children"]]
