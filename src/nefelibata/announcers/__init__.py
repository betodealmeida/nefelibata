import json
import logging
import operator
from typing import Any
from typing import Dict
from typing import List

import mf2py
from nefelibata.post import Post
from pkg_resources import iter_entry_points
from typing_extensions import TypedDict

_logger = logging.getLogger("nefelibata")


User = TypedDict(
    "User", {"name": str, "image": str, "url": str, "description": str}, total=False,
)

Comment = TypedDict("Comment", {"text": str, "url": str}, total=False)

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
    obj = mf2py.parse(url=user["url"])
    for item in obj["items"]:
        if "h-card" in item["type"]:
            user["name"] = item["properties"]["name"][0]
            user["image"] = item["properties"]["photo"][0]
            break

    return user


class Announcer:

    name = "base"
    url_header = "base-url"

    def __init__(self, post: Post, config: Dict[str, Any], *args: Any, **kwargs: Any):
        self.post = post
        self.config = config

    def update_links(self) -> None:
        """Update links.json with link to where the post is announced.
        """
        post_directory = self.post.file_path.parent
        storage = post_directory / "links.json"
        if storage.exists():
            with open(storage) as fp:
                links = json.load(fp)
        else:
            links = {}

        if self.name not in links:
            link = self.announce()
            if not link:
                return

            # store URL in links.json for template
            links[self.name] = link
            with open(storage, "w") as fp:
                json.dump(links, fp)

            # also store in post header
            self.post.parsed[self.url_header] = link
            self.post.save()

    def announce(self) -> str:
        """Publish a post in a service and return the URL.
        """
        raise NotImplementedError("Subclasses must implement announce")

    def update_replies(self) -> None:
        """Update replies.json with new replies, if any.
        """
        if self.url_header not in self.post.parsed:
            return

        post_directory = self.post.file_path.parent
        storage = post_directory / "replies.json"
        if storage.exists():
            with open(storage) as fp:
                replies = json.load(fp)
        else:
            replies = []
        count = len(replies)

        ids = {reply["id"] for reply in replies}
        replies.extend(reply for reply in self.collect() if reply["id"] not in ids)

        for reply in replies:
            user = reply["user"]

            # if the user has an URL, but no name or image, try to read their h-card
            # from the URL
            if user["url"] and (not user["name"] or not user["url"]):
                print("FETCHING USER INFO")
                user = fetch_hcard(user)

        if len(replies) > count:
            _logger.info(
                f'Found new replies in post {self.config["url"]}{self.post.url}',
            )
            replies.sort(key=operator.itemgetter("timestamp"))
            with open(storage, "w") as fp:
                json.dump(replies, fp)
            self.post.save()

    def collect(self) -> List[Response]:
        """Collect responses.
        """
        raise NotImplementedError("Subclasses must implement collect")


def get_announcers(post: Post, config: Dict[str, Any]) -> List[Announcer]:
    """Return all announcers associated with a post.

    Args:
      post (Post): the post object.
    """
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

    announcers = {a.name: a.load() for a in iter_entry_points("nefelibata.announcer")}
    return [
        announcers[name](post, config, **config[name]) for name in selected_announcers
    ]
