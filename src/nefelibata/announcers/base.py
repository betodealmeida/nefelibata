"""
Base class for announcers.
"""
from datetime import datetime
from pathlib import Path
from pprint import pformat
from typing import Any, Dict, List, Literal, Optional

from pkg_resources import iter_entry_points
from pydantic import BaseModel

from nefelibata.builders.base import Scope
from nefelibata.post import Post
from nefelibata.typing import Config


class Announcement(BaseModel):  # pylint: disable=too-few-public-methods
    """
    Model representing an announcement.
    """

    uri: str
    timestamp: datetime


class Interaction(BaseModel):  # pylint: disable=too-few-public-methods
    """
    Model representing an interaction (comment, like, reply, etc.).
    """

    id: str
    name: str
    uri: str
    type: Literal["reply", "backlink", "like"]
    timestamp: Optional[datetime] = None


class Announcer:

    """
    A post announcer.

    Announcers run after and before builders. They run after builders in order
    to publish the post, and before the builders in order to collect replies and
    other interactions.
    """

    scopes: List[Scope] = []

    def __init__(self, root: Path, config: Config, **kwargs: Any):
        self.root = root
        self.config = config
        self.kwargs = kwargs

    async def announce_post(self, post: Post) -> Optional[Announcement]:
        """
        Publish a post externally.
        """
        raise NotImplementedError("Subclasses must implement ``announce_post``")

    async def announce_site(self) -> Optional[Announcement]:
        """
        Publish a site externally.
        """
        raise NotImplementedError("Subclasses must implement ``announce_site``")

    async def collect_post(self, post: Post) -> List[str]:
        """
        Collect interactions on a post.
        """
        raise NotImplementedError("Subclasses must implement ``collect_post``")

    async def collect_site(self) -> List[str]:
        """
        Collect interactions on a site.
        """
        raise NotImplementedError("Subclasses must implement ``collect_site``")


def get_announcers(
    root: Path,
    config: Config,
    scope: Optional[Scope] = None,
) -> Dict[str, Announcer]:
    """
    Return a dictionary of announcers.
    """
    classes = {
        announcer.name: announcer.load()
        for announcer in iter_entry_points("nefelibata.announcer")
    }

    announcers = {}
    for name, parameters in config["announcers"].items():
        if "plugin" not in parameters:
            raise Exception(
                f'Invalid configuration, missing "plugin": {pformat(parameters)}',
            )
        plugin = parameters["plugin"]
        class_ = classes[plugin]
        kwargs = {k: v for k, v in parameters.items() if k != "plugin"}

        if scope is None or scope in class_.scopes:
            announcers[name] = class_(root, config, **kwargs)

    return announcers
