from datetime import datetime, timedelta
import logging
import re
from typing import Any, Dict

from bs4 import BeautifulSoup
import dateutil.parser
import requests

from nefelibata.announcers import Announcer
from nefelibata.post import Post

_logger = logging.getLogger("nefelibata")


def reply_from_li(song_id: int, el: Any) -> Dict[str, Any]:
    """Generate a standard reply from a <li> element in the FAWM song page.

    Args:
      el (BeautifulSoup element): <li> with a comment
    """
    base_url = "https://fawm.org"

    # the <li> has an id that starts with a `c`, followed by numbers
    comment_id = el.attrs["id"][1:]

    # the timestamp is a fuzzy date :(
    fuzzy_timestamp = el.find("small", {"class": "text-muted"}).text
    try:
        timestamp = dateutil.parser.parse(fuzzy_timestamp).timestamp()
    except dateutil.parser.ParserError:
        # parse "1 day", etc.
        value, unit = fuzzy_timestamp.split()
        delta = timedelta(**{f"{unit}s": float(value)})
        timestamp = (datetime.now() - delta).timestamp()

    user_ref = el.find("a", {"class": "user-ref"})
    user_name = user_ref.text
    relative_url = user_ref.attrs["href"]
    user_url = f"{base_url}{relative_url}"

    relative_image = el.find("img", {"class": "comment-avatar"}).attrs["src"]
    user_image = f"{base_url}{relative_image}"

    return {
        "source": "FAWM",
        "color": "#cc6600",
        "id": f"fawm:{comment_id}",
        "timestamp": timestamp,
        "user": {"name": user_name, "image": user_image, "url": user_url},
        "comment": {
            "text": el.find("p", {"id": f"q{comment_id}"}).text,
            "url": f"{base_url}/songs/{song_id}/#c{comment_id}",
        },
    }


class FAWMAnnouncer(Announcer):

    """FAWM Announcer

    FAWM (February Album Writing Month) is a website where every year thousands
    of people participate in a challenge to write 14 songs in 28 days during the
    month of February.

    Every year the website reboots, and comments are lost, making it particularly
    suited for Nefelibata.

    In order to publish a song, the post should be structured like this:

        # Liner Notes

        <notes about the song>

        # Lyrics

        <pre>
            <lyrics go here>
        </pre>

    Everything else is ignored, so you can add an audio player outside of those
    sections.

    You also need to have an MP3 in your post directory, if you want to have it
    published as a demo.

    """

    def __init__(
        self, post: Post, config: Dict[str, Any], username: str, password: str,
    ):
        self.post = post
        self.config = config
        self.username = username
        self.password = password

    def announce(self) -> None:
        """Publish the song to FAWM.
        """
        if "fawm-url" not in self.post.parsed:
            _logger.info("Publishing to FAWM")

            soup = BeautifulSoup(self.post.html, "html.parser")

            params = {
                "title": "Some+title",
                "tags": "silly+singer-songwriter",
                "demo": "http://",
                "notes": "Liner Notes",
                "lyrics": "Lyrics",
                "status": "public",
                "collab": 0,
                "downloadable": 1,
                "submit": "Save+It!",
            }

            # TODO: implement in February
            url = post_to_fawm(params)

            self.post.parsed["fawm-url"] = url
            self.post.save()
            _logger.info("Success!")

    def collect(self) -> None:
        if "fawm-url" not in self.post.parsed:
            return []

        _logger.info("Collecting replies from FAWM")

        url = self.post.parsed["fawm-url"]
        song_id = int(url.rstrip("/").rsplit("/", 1)[1])

        response = requests.get(url)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        replies = []
        for el in soup.find_all("li", {"class": "comment-item", "id": re.compile("c")}):
            replies.append(reply_from_li(song_id, el))

        return replies
