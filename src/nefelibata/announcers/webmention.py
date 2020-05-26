import json
import logging
import re
import urllib.parse
from typing import Any
from typing import cast
from typing import Dict
from typing import List
from typing import Optional

import dateutil.parser
import requests
from bs4 import BeautifulSoup
from nefelibata.announcers import Announcer
from nefelibata.announcers import Response
from nefelibata.post import Post

_logger = logging.getLogger("nefelibata")


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


class WebmentionAnnouncer(Announcer):

    name = "Webmention"
    url_header = "webmention-url"

    def __init__(
        self,
        post: Post,
        config: Dict[str, Any],
        endpoint: str,
        post_to_indienews: bool,
    ):
        super().__init__(post, config)

        self.endpoint = endpoint  # used only in template
        self.post_to_indienews = post_to_indienews

    def announce(self) -> str:
        _logger.info("Discovering links supporting webmention...")

        soup = BeautifulSoup(self.post.render(), "html.parser")
        for el in soup.find_all("a", href=re.compile("http")):
            target = el.attrs.get("href")
            _logger.info(f"Checking {target}")
            self._send_mention(target)

        if self.post_to_indienews:
            target = f'https://news.indieweb.org/{self.config["language"]}'
            _logger.info(f"Checking {target}")
            self._send_mention(target)

        _logger.info("Success!")

        return "https://webmention.net/implementations/"

    def _send_mention(self, target: str) -> None:
        endpoint = get_webmention_endpoint(target)
        if endpoint:
            _logger.info(f"Sending mention to {endpoint}")
            payload = {
                "source": urllib.parse.urljoin(self.config["url"], self.post.url),
                "target": target,
            }
            requests.post(endpoint, data=payload)

    def collect(self) -> List[Response]:
        _logger.info("Collecting webmentions")

        target = urllib.parse.urljoin(self.config["url"], self.post.url)
        url = "https://webmention.io/api/mentions.jf2"
        payload = {"target": target}
        r = requests.get(url, params=payload)
        feed = json.loads(r.content)

        return [
            {
                "source": child.get("name", child["url"]),
                "url": child["url"],
                "id": f'webmention:{child["wm-id"]}',
                "timestamp": (
                    str(dateutil.parser.parse(child["published"]).timestamp())
                    if child.get("published")
                    else ""
                ),
                "user": {
                    "name": child["author"]["name"],
                    "image": child["author"]["photo"],
                    "url": child["author"]["url"],
                },
                "comment": {"text": child.get("content", {}).get("text", "")},
            }
            for child in feed["children"]
        ]
