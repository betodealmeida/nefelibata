import json
import logging
import re
import textwrap
import urllib.parse
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import dateutil.parser
import requests
from bs4 import BeautifulSoup
from bs4 import NavigableString
from bs4.element import Tag
from dateutil.parser._parser import ParserError
from nefelibata.announcers import Announcer
from nefelibata.announcers import Comment
from nefelibata.announcers import Response
from nefelibata.announcers import User
from nefelibata.post import Post

_logger = logging.getLogger(__name__)


def get_session(username: str, password: str) -> requests.Session:
    session = requests.Session()

    response = session.get("http://fiftyninety.fawmers.org/")
    soup = BeautifulSoup(response.text, "html.parser")
    form = soup.find("form", id="user-login-form")
    el = form.find("input", {"name": "form_build_id"})
    form_build_id = el.attrs["value"]

    # get authentication cookie
    url = "http://fiftyninety.fawmers.org/node"
    params = {
        "name": username,
        "pass": password,
        "form_build_id": form_build_id,
        "form_id": "user_login_block",
        "feed_me": "",
        "op": "Log+in",
    }
    session.post(url, params={"destination": "node"}, data=params)

    return session


def get_fid(session, options: str, demo: str) -> str:
    url = "http://fiftyninety.fawmers.org/media/browser"
    params = {
        "options": options,
        "plugins": "undefined",
        "render": "media-popup",
    }
    response = session.get(url, params=params)
    form_build_id, form_token = get_form_params_from_input(
        response.text, "remote-stream-wrapper-file-add-form",
    )

    data = {
        "form_build_id": form_build_id,
        "form_id": "remote_stream_wrapper_file_add_form",
        "form_token": form_token,
        "op": "Submit",
        "url": demo,
    }
    response = session.post(url, params=params, data=data, allow_redirects=False)
    url = response.headers["Location"]
    qs = urllib.parse.urlparse(url).query
    parsed = urllib.parse.parse_qs(qs)
    return parsed["fid"][0]


def get_form_params_from_input(html: str, form_id: str) -> Tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form", id=form_id)

    el = form.find("input", {"name": "form_build_id"})
    form_build_id = el.attrs["value"]
    el = form.find("input", {"name": "form_token"})
    form_token = el.attrs["value"]

    return form_build_id, form_token


def extract_params(
    session: requests.Session, post: Post, root: Path, config: Dict[str, Any],
) -> Dict[str, Any]:
    """Extract params from a standard FiftyNinety post.
    """
    soup = BeautifulSoup(post.html, "html.parser")

    # liner notes are between <h1>s
    notes_h1 = soup.find("h1", text="Liner Notes")
    lines = []
    next_sibling = notes_h1.next_sibling
    while next_sibling and next_sibling.name != "h1":
        try:
            content = next_sibling.get_text()
        except AttributeError:
            content = next_sibling.string
        lines.append(content)
        if next_sibling.name == "p":
            lines.append("\n")
        next_sibling = next_sibling.next_sibling
    notes = "".join(lines).strip()

    # lyrics are inside a <pre> element
    try:
        pre = soup.find("pre")
        lyrics = textwrap.dedent(pre.text).strip()
    except Exception:
        lyrics = "N/A"

    # search for a single MP3 in the post directory to use as demo
    post_directory = post.file_path.parent
    mp3s = list(post_directory.glob("**/*.mp3"))
    if len(mp3s) == 1:
        mp3_path = mp3s[0].relative_to(root / "posts")
        demo = f'{config["url"]}{mp3_path}'
    elif len(mp3s) > 1:
        _logger.error("Multiple MP3s found, aborting!")
        raise Exception("Only posts with a single MP3 can be announced on FiftyNinety")
    else:
        demo = ""

    # get tokens used in POST
    response = session.get("http://fiftyninety.fawmers.org/node/add/song")
    form_build_id, form_token = get_form_params_from_input(
        response.text, "song-node-form",
    )

    # get additional params for file upload; these are encoded in the JS
    soup = BeautifulSoup(response.text, "html.parser")
    el = soup.find("script", text=re.compile(r"^jQuery\.extend"))
    if not el:
        raise Exception("Unable to find options from Javascript")
    match = re.search("{.*}", el.contents[0])
    if not match:
        raise Exception("Unable to parse options from Javascript")
    payload = match.group(0)
    arg = json.loads(payload)
    options = arg["media"]["elements"][
        ".js-media-element-edit-field-demo-und-0-upload"
    ]["global"]["options"]

    # get an ID referencing the demo
    fid = get_fid(session, options, demo) if demo else ""

    return {
        "body[und][0][value]": notes,
        "field_collab[und][0][_weight]": "0",
        "field_demo[und][0][display]": "1",
        "field_demo[und][0][fid]": fid,
        "field_downloadable[und]": "1" if demo else "0",
        "field_lyrics[und][0][value]": lyrics,
        "field_tags[und]": post.parsed["keywords"],
        "form_build_id": form_build_id,
        "form_id": "song_node_form",
        "form_token": form_token,
        "op": "Save",
        "title": post.title,
        "changed": "",
    }


def get_comments_from_fiftyninety_page(
    session: requests.Session, url: str, username: str, password: str,
) -> List[Response]:
    """Extract comments from a given FiftyNinety page.
    """
    base_url = "http://fiftyninety.fawmers.org"

    response = session.get(url)
    response.encoding = "UTF-8"
    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    responses: List[Response] = []

    # the HTML is so broken that we can't rely on relationship between nodes
    # first, we extract comment IDs
    ids = [
        int(el.attrs["id"].split("-", 1)[1])
        for el in soup.find_all("a", {"id": re.compile(r"comment-\d+")})
    ]

    # now we extract usernames and time of the comment
    users: List[User] = []
    timestamps = []
    for el in soup.find_all("p", {"class": "author-datetime"}):
        fuzzy_timestamp = el.text.split(" - ")[1]
        timestamps.append(parse_fuzzy_timestamp(fuzzy_timestamp))

        anchor = el.find("a")
        users.append({"name": anchor.text, "url": f"{base_url}{anchor.attrs['href']}"})

    # extract comments and user images
    comments: List[Comment] = []
    for i, el in enumerate(soup.find_all("div", {"class": "comment-content"})):
        if el.find("img"):
            # the linked image is low resolution, but we can replace it with a
            # higher resolution version
            users[i]["image"] = (
                el.find("img").attrs["src"].replace("/smallthumb/", "/medium/")
            )
        comments.append(
            {
                "text": "\n\n".join(p.text for p in el.find_all("p")),
                "url": f"{url}#comment-{ids[i]}",
            },
        )

    for id_, user, timestamp, comment, in zip(ids, users, timestamps, comments):
        responses.append(
            {
                "source": "50/90",
                "url": url,
                "color": "#284ead",
                "id": f"fiftyninety:{id_}",
                "timestamp": timestamp.isoformat(),
                "user": user,
                "comment": comment,
            },
        )

    return responses


def parse_fuzzy_timestamp(timestamp: str) -> datetime:
    """Parse fuzzy timestamps.

    FiftyNinety annotates comments with relative timestamps:

        - 0 sec
        - 3 min 50 sec
        - 20 hours 38 min
        - 1 hour 52 min
        - 1 day 16 hours

    """
    now = datetime.now(tz=timezone.utc)

    timedelta_units = {
        "sec": "seconds",
        "secs": "seconds",
        "min": "minutes",
        "mins": "minutes",
        "hour": "hours",
        "hours": "hours",
        "day": "days",
        "days": "days",
        "week": "weeks",
        "weeks": "weeks",
    }

    kwargs = {}
    parts = timestamp.strip().split(" ")
    for number, units in zip(parts[::2], parts[1::2]):
        value = int(number)

        if units in ["month", "months"]:
            units = "days"
            value *= 30

        kwargs = {timedelta_units[units]: value}
        now -= timedelta(**kwargs)

    return now


class FiftyNinetyAnnouncer(Announcer):

    """FiftyNinety Announcer

    FiftyNinety  is a website where every year of people participate in a
    challenge to write 50 songs in 90 days during the northern hemisphere summer.

    Every year the website reboots, and comments are lost, making it particularly
    suited for Nefelibata.

    In order to publish a song, the post should be structured like this:

        # Liner Notes

        <notes about the song>

        # Lyrics

        <pre>
            <lyrics go here>
        </pre>

    Lyrics are optional. Everything else is ignored, so you can add an audio
    player outside of those sections.

    You also need to have an MP3 in your post directory, if you want to have it
    published as a demo.

    """

    id = "fiftyninety"
    name = "FiftyNinety"
    url_header = "fiftyninety-url"

    def __init__(
        self, root: Path, config: Dict[str, Any], username: str, password: str,
    ):
        super().__init__(root, config)

        self.username = username
        self.password = password

    def announce(self, post: Post) -> str:
        """Publish the song to FiftyNinety.
        """
        _logger.info("Creating new song on FiftyNinety")

        # login and store auth cookie
        session = get_session(self.username, self.password)

        params = extract_params(session, post, self.root, self.config)
        response = session.post(
            "http://fiftyninety.fawmers.org/node/add/song",
            data=params,
            allow_redirects=False,
        )
        url = response.headers["Location"]

        _logger.info("Success!")

        return url

    def collect(self, post: Post) -> List[Response]:
        _logger.info("Collecting comments from FiftyNinety")

        # login and store auth cookie
        session = get_session(self.username, self.password)

        url = post.parsed[self.url_header]
        responses = get_comments_from_fiftyninety_page(
            session, url, self.username, self.password,
        )

        _logger.info("Success!")

        return responses
