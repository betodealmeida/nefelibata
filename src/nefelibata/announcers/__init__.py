import json
import logging
import operator
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set

import mf2py
from nefelibata.post import Post
from nefelibata.utils import json_storage
from pkg_resources import iter_entry_points
from typing_extensions import TypedDict

_logger = logging.getLogger(__name__)


User = TypedDict(
    "User", {"name": str, "image": str, "url": str, "description": str}, total=False,
)

Comment = TypedDict(
    "Comment", {"text": str, "url": str, "summary": str, "html": str}, total=False,
)

Response = TypedDict(
    "Response",
    {
        "source": str,
        "url": str,
        "color": str,
        "id": str,
        "timestamp": str,
        "user": User,
        "comment": Comment,
    },
    total=False,
)


def fetch_hcard(user: User) -> User:
    user = user.copy()
    obj = mf2py.parse(url=user["url"])
    for item in obj["items"]:
        if "h-card" in item["type"]:
            user["name"] = item["properties"]["name"][0]
            user["image"] = item["properties"]["photo"][0]
            break

    return user


class Announcer:

    id = "base"
    name = "Base"
    url_header = "base-url"

    def __init__(self, root: Path, config: Dict[str, Any], *args: Any, **kwargs: Any):
        self.root = root
        self.config = config

    def match(self, post: Post):
        return self.id in get_post_announcers(self.config, post)

    def should_announce(self, post: Post) -> bool:
        return self.url_header not in post.parsed

    def update_links(self, post: Post) -> None:
        """Update links.json with link to where the post is announced.
        """
        if not self.should_announce(post):
            return

        post_directory = post.file_path.parent
        storage = post_directory / "links.json"
        with json_storage(storage) as links:
            link = self.announce(post)
            if not link or links.get(self.name) == link:
                return

            # store URL in links.json for template
            links[self.name] = link

            # also store in post header
            post.parsed[self.url_header] = link
            post.save()

    def announce(self, post: Post) -> Optional[str]:
        """Publish a post in a service and return the URL.
        """
        raise NotImplementedError("Subclasses must implement announce")

    def update_replies(self, post: Post) -> None:
        """Update replies.json with new replies, if any.
        """
        if self.url_header not in post.parsed:
            return

        post_directory = post.file_path.parent
        storage = post_directory / "replies.json"
        if storage.exists():
            with open(storage) as fp:
                replies = json.load(fp)
        else:
            replies = []

        ids = {reply["id"] for reply in replies}
        new_replies = [reply for reply in self.collect(post) if reply["id"] not in ids]
        for reply in new_replies:
            user = reply["user"]

            # if the user has an URL, but no name or image, try to read their h-card
            # from the URL
            if user["url"] and (not user["name"] or not user["url"]):
                reply["user"] = fetch_hcard(user)

        if new_replies:
            _logger.info(f'Found new replies in post {self.config["url"]}{post.url}')
            replies.extend(new_replies)
            replies.sort(key=operator.itemgetter("timestamp"))
            with open(storage, "w") as fp:
                json.dump(replies, fp)

            # save file so that it's marked as stale
            post.save()

    def collect(self, post: Post) -> List[Response]:
        """Collect responses.
        """
        raise NotImplementedError("Subclasses must implement collect")


def get_post_announcers(config: Dict[str, Any], post: Post) -> Set[str]:
    if "announce-on" in post.parsed:
        selected_announcers = {
            announcer.strip() for announcer in post.parsed["announce-on"].split(",")
        }
    else:
        names = config["announce-on"] or []
        if isinstance(names, str):
            names = [names]
        selected_announcers = set(names)

    if "announce-on-extra" in post.parsed:
        selected_announcers.update(
            announcer.strip()
            for announcer in post.parsed["announce-on-extra"].split(",")
        )

    if "announce-on-skip" in post.parsed:
        excluded_announcers = {
            announcer.strip()
            for announcer in post.parsed["announce-on-skip"].split(",")
        }
        selected_announcers = selected_announcers - excluded_announcers

    return selected_announcers


def get_announcers(root: Path, config: Dict[str, Any]) -> List[Announcer]:
    announcers = {a.name: a.load() for a in iter_entry_points("nefelibata.announcer")}

    return [
        announcers[name](root, config, **config.get(name, {})) for name in announcers
    ]
