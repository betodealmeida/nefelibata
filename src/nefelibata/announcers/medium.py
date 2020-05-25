import logging
import requests
import json
import urllib.parse
from typing import Any, Dict, List

import requests

from nefelibata.announcers import Announcer, Response
from nefelibata.post import Post

_logger = logging.getLogger("nefelibata")


class MediumAnnouncer(Announcer):

    name = "Medium"
    url_header = "medium-url"

    def __init__(self, post: Post, config: Dict[str, Any], access_token: str):
        super().__init__(post, config)

        self.access_token = access_token

    def announce(self) -> str:
        _logger.info("Posting to Medium")

        headers = {
            "Authorization": "Bearer " + self.access_token,
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 6.3; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/63.0.3239.84 Safari/537.36"
            ),
        }

        # get user ID
        url = "https://api.medium.com/v1/me"
        response = requests.get(url, headers=headers)
        user_id = response.json()["data"]["id"]

        url = f"https://api.medium.com/v1/users/{user_id}/posts"
        # TODO: add license
        payload = {
            "title": self.post.title,
            "contentFormat": "html",
            "content": self.post.html,
            "tags": [
                tag.strip() for tag in self.post.parsed.get("keywords", "").split(",")
            ],
            "canonicalUrl": urllib.parse.urljoin(self.config["url"], self.post.url),
            "publishStatus": self.config["medium"]["publish_status"] or "draft",
        }
        response = requests.post(url, data=payload, headers=headers)
        return response.json()["data"]["url"]

    def collect(self) -> List[Response]:
        _logger.info("Skipping Medium, since there are not replies")
        return []
