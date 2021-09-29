"""
Base class for announcers.
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pkg_resources import iter_entry_points
from pydantic import BaseModel

from nefelibata.builders.base import Builder, Scope, get_builders
from nefelibata.post import Post
from nefelibata.typing import Config

_logger = logging.getLogger(__name__)


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

    def __init__(
        self, root: Path, config: Config, builders: List[Builder], **kwargs: Any
    ):
        self.root = root
        self.config = config
        self.builders = builders
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

    async def collect_post(self, post: Post) -> Dict[str, Interaction]:
        """
        Collect interactions on a post.
        """
        raise NotImplementedError("Subclasses must implement ``collect_post``")

    async def collect_site(self) -> Dict[Path, Dict[str, Interaction]]:
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
    Return configured announcers.
    """
    builders = get_builders(root, config, scope)

    classes = {
        announcer.name: announcer.load()
        for announcer in iter_entry_points("nefelibata.announcer")
    }

    announcers = {}
    for name, parameters in config["announcers"].items():
        plugin = parameters["plugin"]
        class_ = classes[plugin]

        # find all builders that the announcer should handle
        announcer_builders = [
            builders[builder_name]
            for builder_name, builder_parameters in config["builders"].items()
            if name in builder_parameters["announce-on"]
        ]

        if scope is None or scope in class_.scopes:
            announcers[name] = class_(root, config, announcer_builders, **parameters)

    return announcers
