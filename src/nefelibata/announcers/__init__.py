from typing import Any, Dict, List

from pkg_resources import iter_entry_points

from nefelibata.post import Post


class Announcer:
    def announce(self) -> None:
        raise NotImplementedError("Subclasses must implement announce")

    def collect(self) -> None:
        """Collect responses.

        The responses should be stored as JSON in the post directory, with the
        following structure:

            [{
                source
                id
                timestamp
                user:
                    image
                    url
                    description
                    username
                comment:
                    text
                    url


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
