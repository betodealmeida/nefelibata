import json
import logging
import re
import urllib.parse
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any
from typing import cast
from typing import Dict
from typing import List

import requests
from bs4 import BeautifulSoup
from nefelibata.announcers import Announcer
from nefelibata.announcers import Response
from nefelibata.post import Post

_logger = logging.getLogger(__name__)


def get_responses_from_payload(payload: Dict[str, Any]) -> List[Response]:
    responses: List[Response] = []
    for comment in payload["value"]:
        user_id = comment["creatorId"]
        user_attributes = payload["references"]["User"][user_id]

        responses.append(
            {
                "source": comment["title"],
                "url": f'https://medium.com/p/{comment["inResponseToPostId"]}/responses/show',
                "color": "#333333",
                "id": f'medium:{comment["id"]}',
                "timestamp": datetime.fromtimestamp(comment["createdAt"] / 1000.0)
                .astimezone(timezone.utc)
                .isoformat(),
                "user": {
                    "name": user_attributes["name"],
                    "image": f'https://miro.medium.com/fit/c/128/128/{user_attributes["imageId"]}',
                    "url": f'https://medium.com/@{user_attributes["username"]}',
                    "description": user_attributes["bio"],
                },
                "comment": {
                    "text": comment["previewContent"]["bodyModel"]["paragraphs"][0][
                        "text"
                    ],
                    "url": f'https://medium.com/@{user_attributes["username"]}/{comment["uniqueSlug"]}',
                },
            },
        )

    return responses


class MediumAnnouncer(Announcer):

    id = "medium"
    name = "Medium"
    url_header = "medium-url"

    def __init__(
        self,
        root: Path,
        config: Dict[str, Any],
        access_token: str,
        publish_status: str,
    ):
        super().__init__(root, config)

        self.access_token = access_token
        self.publish_status = publish_status

    def announce(self, post: Post) -> str:
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
            "title": post.title,
            "contentFormat": "html",
            "content": self._get_html_with_absolute_links(post),
            "tags": [tag.strip() for tag in post.parsed.get("keywords", "").split(",")],
            "canonicalUrl": urllib.parse.urljoin(self.config["url"], post.url),
            "publishStatus": self.publish_status or "draft",
        }
        response = requests.post(url, data=payload, headers=headers)
        return cast(str, response.json()["data"]["url"])

    def collect(self, post: Post) -> List[Response]:
        _logger.info("Collecting comments from Medium")

        post_url = post.parsed[self.url_header]
        post_id = post_url.rsplit("/", 1)[1]
        comments_url = f"https://medium.com/p/{post_id}/responses/?format=json"

        response = requests.get(comments_url)
        payload = json.loads(response.text[16:])

        responses = get_responses_from_payload(payload["payload"])

        _logger.info("Success!")

        return responses

    def _get_html_with_absolute_links(self, post: Post) -> str:
        """
        Convert links to absolute URLs.

        Since we upload the whole HTML response to Medium, we need to convert
        relative liks to absolute ones, to prevent them from breaking.
        """
        soup = BeautifulSoup(post.html, "html.parser")
        for el in soup.find_all("a", href=re.compile("^(?!https?://)")):
            relative_url = el.attrs["href"]
            if relative_url.startswith("/"):
                absolute_url = urllib.parse.urljoin(self.config["url"], relative_url)
            else:
                directory_name = post.file_path.parent.relative_to(self.root / "posts")
                absolute_url = urllib.parse.urljoin(
                    self.config["url"], f"{directory_name}/{relative_url}",
                )
            el.attrs["href"] = absolute_url

        return str(soup)
