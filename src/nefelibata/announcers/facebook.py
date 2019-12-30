import logging
from typing import Any, Dict, List
from urllib.parse import urlencode
import webbrowser

import dateutil.parser
import requests

from nefelibata.announcers import Announcer
from nefelibata.post import Post

_logger = logging.getLogger("nefelibata")


class FacebookAnnouncer(Announcer):

    name = "Facebook"
    url_header = "facebook-url"

    def __init__(
        self, post: Post, config: Dict[str, Any], app_id: int, access_token: str
    ):
        self.post = post
        self.config = config
        self.app_id = app_id
        self.access_token = access_token

    def announce(self) -> str:
        """Publish the summary of a post to Facebook.
        """
        _logger.info("Announcing post on Facebook")

        baseurl = "https://www.facebook.com/dialog/feed?"
        params = {
            "app_id": self.app_id,
            "display": "page",
            "link": f'{self.config["url"]}{self.post.url}',
        }
        url = f"{baseurl}{urlencode(params)}"
        webbrowser.open_new_tab(url)

        _logger.info("Please post to Facebook manually")
        _logger.info(self.post.summary)
        url = input("Enter full URL of the post created: ")

        _logger.info("Success!")

        return url

    def collect(self) -> List[Dict[str, Any]]:
        _logger.info("Collecting replies from Facebook")

        # params for requests
        params = {
            "access_token": self.access_token,
        }

        # get userid
        url = "https://graph.facebook.com/v5.0/me"
        response = requests.get(url, params=params)
        payload = response.json()
        user_id = payload["id"]

        # get post replies
        post_url = self.post.parsed[self.url_header]
        post_id = post_url.rsplit("/", 1)[1]
        url = f"https://graph.facebook.com/v5.0/{user_id}_{post_id}/comments"
        response = requests.get(url, params=params)
        payload = response.json()

        replies = []
        for comment in payload["data"]:
            reply = {
                "source": "Facebook",
                "url": post_url,
                "color": "#3b5998",
                "id": f'facebook:{comment["id"]}',
                "timestamp": dateutil.parser.parse(comment["created_time"]).timestamp(),
                "user": {
                    "name": comment["from"]["name"],
                    "image": f'https://graph.facebook.com/{comment["from"]["id"]}/picture',
                    "url": None,
                    "description": None,
                },
                "comment": {"text": comment["message"], "url": None,},
            }
            replies.append(reply)

        return replies


# https://developers.facebook.com/tools/explorer/?method=GET&path=10162755483755182_10162754684945182&version=v5.0
# https://developers.facebook.com/tools/explorer/?method=GET&path=10162755483755182_10162766235210182%2Fcomments&version=v5.0 (works)
# https://developers.facebook.com/tools/explorer/?method=GET&path=10162755483755182_10162754684945182%2Fcomments&version=v5.0 (does not)
