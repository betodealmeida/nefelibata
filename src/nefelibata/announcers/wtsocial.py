import logging
import re
import urllib.parse
from datetime import timezone
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
from nefelibata.announcers import Response
from nefelibata.post import Post

_logger = logging.getLogger(__name__)


def get_user_image(username: str) -> Optional[str]:
    """Return URL of the profile picture of a given user.
    """
    url = f"https://wt.social/u/{username}"
    response = requests.get(url)
    match = re.search(r"(https.*?--profile_pic\.\w+)", response.text)
    return match.group(1).replace("\\", "") if match else None


def get_response_from_comment(comment: Dict[str, Any]) -> Response:
    """Generate a standard reply from a comment.
    """
    comment_url = (
        f'https://wt.social{comment["parentUrl"]}#comment-{comment["comment_id"]}'
    )
    return {
        "source": "WT.Social",
        "color": "#1e1e1e",
        "id": f'wtsocial:{comment["comment_id"]}',
        "timestamp": dateutil.parser.parse(comment["formatted"]["created_at"])
        .astimezone(timezone.utc)
        .isoformat(),
        "user": {
            "name": comment["users_name"],
            "image": get_user_image(comment["user_uri"]) or "",
            "url": f'https://wt.social{comment["UURI"]}',
            "description": "",
        },
        "comment": {"text": comment["formatted"]["comment_body"], "url": comment_url},
    }


def get_csrf_token(html: str) -> Optional[str]:
    """Extract CSRF token from a page.

    The token is stored in a meta tag:

        <meta name="csrf-token" content="PZ2AHyOSbUSRjaMNFLISKXPdghG8NPn0TZnjtteJ">

    """
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("meta", attrs={"name": "csrf-token"})
    return cast(str, tag.attrs["content"]) if tag else None


def do_login(session: requests.Session, email: str, password: str) -> str:
    """Perform login and return HTML page.
    """
    url = "https://wt.social/login"
    response = session.get(url)
    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("input", attrs={"name": "_token"})
    token = tag.attrs["value"]

    params = {
        "email": email,
        "password": password,
        "_token": token,
        "remember": 1,
    }
    response = session.post(url, params=params)

    return response.text


class WTSocialAnnouncer(Announcer):

    id = "wtsocial"
    name = "WT.Social"
    url_header = "wtsocial-url"

    def __init__(self, root: Path, config: Dict[str, Any], email: str, password: str):
        super().__init__(root, config)

        self.email = email
        self.password = password

    def announce(self, post: Post) -> Optional[str]:
        """Publish the summary of a post to WT.Social.
        """
        _logger.info("Posting to WT.Social")

        session = requests.Session()
        html = do_login(session, self.email, self.password)
        csrf_token = get_csrf_token(html)
        if csrf_token is None:
            _logger.error("Couldn't find a CSRF token, exiting...")
            return None

        post_url = urllib.parse.urljoin(self.config["url"], post.url)

        url = "https://wt.social/api/new-article"
        params = {
            "collaborative": False,
            "article_title": post.title,
            "article_body": f"{post.summary}\n\n{post_url}",
            "edit-summary": "",
            # "to-user": "beto-dealmeida",
        }
        headers = {"X-CSRF-TOKEN": csrf_token}
        response = session.post(url, params=params, headers=headers)
        payload = response.json()
        url = f'https://wt.social{payload["0"]["URI"]}'

        _logger.info("Success!")

        return url

    def collect(self, post: Post) -> List[Response]:
        """Collect responses to a given post.
        """
        _logger.info("Collecting replies from WT.Social")

        session = requests.Session()
        html = do_login(session, self.email, self.password)
        csrf_token = get_csrf_token(html)
        if csrf_token is None:
            _logger.error("Couldn't find a CSRF token, exiting...")
            return []

        post_url = post.parsed[self.url_header]
        post_id = post_url.rsplit("/", 1)[1]
        url = f"https://wt.social/api/post/{post_id}"
        headers = {"X-CSRF-TOKEN": csrf_token}
        response = session.get(url, headers=headers)
        payload = response.json()

        responses = []
        for comment in payload["comment_list"]:
            replies = get_response_from_comment(comment)
            replies["url"] = post_url
            responses.append(replies)

        _logger.info("Success!")

        return responses
