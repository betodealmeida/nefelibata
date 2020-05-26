import logging
import re
import textwrap
from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Dict
from typing import List

import dateutil.parser
import requests
from bs4 import BeautifulSoup
from bs4 import NavigableString
from bs4.element import Tag
from dateutil.parser._parser import ParserError
from nefelibata.announcers import Announcer
from nefelibata.announcers import Response
from nefelibata.post import Post

_logger = logging.getLogger("nefelibata")


def extract_params(post: Post, config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract params from a standard FAWM post.
    """
    soup = BeautifulSoup(post.html, "html.parser")

    # liner notes are between <h1>s
    notes_h1 = soup.find("h1", text="Liner Notes")
    els = []
    next_sibling = notes_h1.next_sibling
    while next_sibling and next_sibling.name != "h1":
        els.append(next_sibling)
        if next_sibling.name == "p":
            els.append(NavigableString("\n"))
        next_sibling = next_sibling.next_sibling
    notes = "".join(el.string for el in els).strip()

    # lyrics are inside a <pre> element
    try:
        pre = soup.find("pre")
        lyrics = textwrap.dedent(pre.text).strip()
    except Exception:
        lyrics = "N/A"

    # tags are separated by space, not comma
    tags = re.sub(r",\s?", " ", post.parsed["keywords"])

    # search for a single MP3 in the post directory to use as demo
    post_directory = post.file_path.parent
    mp3s = list(post_directory.glob("*.mp3"))
    if len(mp3s) == 1:
        mp3_path = mp3s[0].relative_to(post.root / "posts")
        demo = f'{config["url"]}{mp3_path}'
    elif len(mp3s) > 1:
        _logger.error("Multiple MP3s found, aborting!")
        raise Exception("Only posts with a single MP3 can be announced on FAWM")
    else:
        demo = ""

    return {
        "id": "",
        "title": post.title,
        "tags": tags,
        "demo": demo,
        "notes": notes,
        "lyrics": lyrics,
        "status": "public",
        "collab": 0,
        "downloadable": 1,
        "submit": "Save+It!",
    }


def get_response_from_li(song_id: int, url: str, el: Tag) -> Response:
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
        timestamp = str(dateutil.parser.parse(fuzzy_timestamp).timestamp())
    except ParserError:
        # parse "1 day", etc.
        value, unit = fuzzy_timestamp.split()
        unit = unit.rstrip("s")
        delta = timedelta(**{f"{unit}s": int(value)})
        timestamp = str((datetime.now() - delta).timestamp())

    user_ref = el.find("a", {"class": "user-ref"})
    user_name = user_ref.text.strip()
    relative_url = user_ref.attrs["href"]
    user_url = f"{base_url}{relative_url}"

    relative_image = el.find("img", {"class": "comment-avatar"}).attrs["src"]
    user_image = f"{base_url}{relative_image}"

    # the actual comment is in a <p> with an id that starts with `q`
    comment = el.find("p", {"id": f"q{comment_id}"}).text

    return {
        "source": "FAWM",
        "url": url,
        "color": "#cc6600",
        "id": f"fawm:{comment_id}",
        "timestamp": timestamp,
        "user": {"name": user_name, "image": user_image, "url": user_url},
        "comment": {
            "text": comment,
            "url": f"{base_url}/songs/{song_id}/#c{comment_id}",
        },
    }


def get_comments_from_fawm_page(
    url: str, username: str, password: str,
) -> List[Response]:
    """Extract replies from a given FAWM page.
    """
    response = requests.get(url, auth=(username, password))
    response.encoding = "UTF-8"
    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    replies = []
    song_id = int(url.rstrip("/").rsplit("/", 1)[1])
    # there are non-comments with the class "comment-item", so we need to narrow down
    for el in soup.find_all("li", {"class": "comment-item", "id": re.compile(r"c\d+")}):
        replies.append(get_response_from_li(song_id, url, el))

    return replies


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

    name = "FAWM"
    url_header = "fawm-url"

    def __init__(
        self, post: Post, config: Dict[str, Any], username: str, password: str,
    ):
        super().__init__(post, config)

        self.username = username
        self.password = password

    def announce(self) -> str:
        """Publish the song to FAWM.
        """
        _logger.info("Creating new song on FAWM")

        params = extract_params(self.post, self.config)
        response = requests.post(
            "https://fawm.org/songs/add",
            data=params,
            auth=(self.username, self.password),
        )
        url = response.headers["Location"]

        _logger.info("Success!")

        return url

    def collect(self) -> List[Response]:
        _logger.info("Collecting replies from FAWM")

        url = self.post.parsed[self.url_header]
        print("BETO", url)
        replies = get_comments_from_fawm_page(url, self.username, self.password)

        _logger.info("Success!")

        return replies
