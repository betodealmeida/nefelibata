from datetime import datetime
import logging
import re
import sys
import time
from typing import Any, Dict, List
from urllib.parse import urlencode
import webbrowser

import dateutil.parser
import pyperclip
import requests

from nefelibata.announcers import Announcer
from nefelibata.post import Post

_logger = logging.getLogger("nefelibata")


def generate_access_token(app_id: int, app_secret: str, short_lived_token: str) -> str:
    """Generate a 60-day access token for the FB Graph API.

    https://developers.facebook.com/docs/facebook-login/access-tokens/refreshing/

    """
    url = "https://graph.facebook.com/v5.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_lived_token,
    }
    response = requests.get(url, params=params)
    payload = response.json()
    print(payload)

    return payload["access_token"]


def get_token_expiration(access_token: str) -> datetime:
    """Return the expiration token of a give token.
    """
    url = "https://graph.facebook.com/v5.0/debug_token"
    params = {
        "access_token": access_token,
        "input_token": access_token,
    }
    response = requests.get(url, params=params)
    payload = response.json()

    return datetime.fromtimestamp(payload["data"]["expires_at"])


class FacebookAnnouncer(Announcer):

    name = "Facebook"
    url_header = "facebook-url"

    def __init__(
        self,
        post: Post,
        config: Dict[str, Any],
        app_id: int,
        app_secret: int,
        short_lived_token: str,
        access_token: str,
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

        pyperclip.copy(self.post.summary)
        sys.stdout.write(
            "Please post to Facebook manually. "
            "The post summary has been copied to your clipboard. "
            "Copy the URL of the new post when done.\n"
        )
        _logger.info("Waiting for URL to be copied to clipboard...")
        while True:
            url = pyperclip.paste()
            if re.match("https://www.facebook.com/.+/posts/\d+", url):
                _logger.info("Found URL!")
                break
            time.sleep(1)

        _logger.info("Success!")

        return url

    def collect(self) -> List[Dict[str, Any]]:
        _logger.info("Collecting replies from Facebook")

        expiration = get_token_expiration(self.access_token)
        days_to_expiration = (expiration - datetime.now()).days
        if days_to_expiration > 7:
            _logger.info(f"Token expires on {expiration}")
        elif days_to_expiration > 0:
            _logger.warning(f"Token expires on {expiration}")
        else:
            _logger.error("Token expired!")
            return []

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
