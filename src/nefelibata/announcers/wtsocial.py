import logging
import re
from typing import Any, Dict, List, Optional

import dateutil.parser
import requests

from bs4 import BeautifulSoup
from nefelibata.announcers import Announcer
from nefelibata.post import Post

_logger = logging.getLogger("nefelibata")


def get_user_image(username: str) -> Optional[str]:
    """Return URL of the profile picture of a given user.
    """
    url = f"https://wt.social/u/{username}"
    response = requests.get(url)
    match = re.search("(https.*?--profile_pic\.\w+)", response.text)
    return match.group(1).replace("\\", "") if match else None


def get_reply_from_comment(comment: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a standar reply from a comment.

    Args:
      comment (Dict[str, Any]): The comment response from the WT.Social API.
    """
    comment_url = (
        f'https://wt.social{comment["parentUrl"]}#comment-{comment["comment_id"]}'
    )
    return {
        "source": "WT.Social",
        "color": "#1e1e1e",
        "id": f'wtsocial:{comment["comment_id"]}',
        "timestamp": dateutil.parser.parse(
            comment["formatted"]["created_at"]
        ).timestamp(),
        "user": {
            "name": comment["users_name"],
            "image": get_user_image(comment["user_uri"]),
            "url": f'https://wt.social{comment["UURI"]}',
            "description": "",
        },
        "comment": {"text": comment["formatted"]["comment_body"], "url": comment_url},
    }


def get_csrf_token(html: str) -> str:
    """Extract CSRF token from a page.

    The token is stored in a meta tag:

        <meta name="csrf-token" content="PZ2AHyOSbUSRjaMNFLISKXPdghG8NPn0TZnjtteJ">

    """
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("meta", attrs={"name": "csrf-token"})
    return tag.attrs["content"]


def do_login(session: requests.Session, email: str, password: str) -> str:
    """Perform login and return HTML page.
    """
    url = "https://wt.social/login"
    response = session.get(url)
    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("input", attrs={"name": "_token"})
    token = tag.attrs["value"]

    params = {"email": email, "password": password, "_token": token, "remember": 1}
    response = session.post(url, params=params)

    return response.text


class WTSocialAnnouncer(Announcer):

    name = "WT.Social"
    url_header = "wtsocial-url"

    def __init__(self, post: Post, config: Dict[str, Any], email: str, password: str):
        self.post = post
        self.config = config
        self.email = email
        self.password = password

    def announce(self) -> str:
        """Publish the summary of a post to WT.Social.
        """
        _logger.info("Posting to WT.Social")

        session = requests.Session()
        html = do_login(session, self.email, self.password)
        csrf_token = get_csrf_token(html)

        url = "https://wt.social/api/new-article"
        params = {
            "collaborative": False,
            "article_title": self.post.title,
            "article_body": self.post.summary,
            "edit-summary": "",
            # "to-user": "beto-dealmeida",
        }
        headers = {"X-CSRF-TOKEN": csrf_token}
        response = session.post(url, params=params, headers=headers)
        payload = response.json()
        url = f'https://wt.social{payload["0"]["URI"]}'

        _logger.info("Success!")

        return url

    def collect(self) -> List[Dict[str, Any]]:
        """Collect responses to a given post.
        """
        _logger.info("Collecting replies from WT.Social")

        session = requests.Session()
        html = do_login(session, self.email, self.password)
        csrf_token = get_csrf_token(html)

        post_url = self.post.parsed[self.url_header]
        post_id = post_url.rsplit("/", 1)[1]
        url = f"https://wt.social/api/post/{post_id}"
        response = session.get(url)
        payload = response.json()

        replies = []
        for comment in payload["comment_list"]:
            reply = get_reply_from_comment(comment)
            reply["url"] = post_url
            replies.append(reply)

        _logger.info("Success!")

        return replies
