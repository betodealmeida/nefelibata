import json
import operator
from typing import Any, Dict, List

from pkg_resources import iter_entry_points

from nefelibata.post import Post


class Announcer:
    def announce(self) -> None:
        raise NotImplementedError("Subclasses must implement announce")

    def update_replies(self) -> None:
        """Update replies.json with new replies, if any.
        """
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
