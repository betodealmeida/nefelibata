import json
import logging
import operator
from typing import Any, Dict, List

from pkg_resources import iter_entry_points

from nefelibata.post import Post

_logger = logging.getLogger("nefelibata")


class Announcer:
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

        if len(replies) > count:
            _logger.info(
                f'Found new replies in post {self.config["url"]}{self.post.url}'
            )
            replies.sort(key=operator.itemgetter("timestamp"))
            with open(storage, "w") as fp:
                json.dump(replies, fp)
            self.post.save()

    def collect(self) -> List[Dict[str, Any]]:
        """Collect responses.

        The responses should be stored as JSON in the post directory, with the
        following structure:

            [{
                source
                url
                [color]
                id
                timestamp
                user
                    name
                    [image]
                    [url]
                    [description]
                comment
                    text
                    [url]
            }]

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
