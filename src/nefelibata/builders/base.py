"""
Base class for builders.
"""

from enum import Enum
from pathlib import Path
from pprint import pformat
from typing import Any
from typing import List
from typing import Optional

from pkg_resources import iter_entry_points

from nefelibata.post import Post
from nefelibata.typing import Config


class Scope(Enum):
    """
    The scope of a given builder.

    Builders can process a single post, the entire site, or both.
    """

    POST = "POST"
    SITE = "SITE"


class Builder:

    """
    A post builder.
    """

    scopes: List[Scope] = []

    def __init__(self, root: Path, config: Config, **kwargs: Any):
        self.root = root
        self.config = config
        self.kwargs = kwargs

    async def process_post(self, post: Post, force: bool = False) -> None:
        """
        Process a single post.
        """
        raise NotImplementedError("Subclasses MUST implement `process_post`")

    async def process_site(self, force: bool = False) -> None:
        """
        Process the entire site.
        """
        raise NotImplementedError("Subclasses MUST implement `process_site`")


def get_builders(
    root: Path, config: Config, scope: Optional[Scope] = None
) -> List[Builder]:
    """
    Return all the builders for a given scope.
    """
    classes = {
        entry_point.name: entry_point.load()
        for entry_point in iter_entry_points("nefelibata.builder")
    }

    builders = []
    for parameters in config["builders"]:
        if "plugin" not in parameters:
            raise Exception(
                f'Invalid configuration, missing "plugin": {pformat(parameters)}'
            )
        name = parameters["plugin"]
        class_ = classes[name]
        kwargs = {k: v for k, v in parameters.items() if k != "plugin"}

        if scope in class_.scopes or scope is None:
            builders.append(class_(root, config, **kwargs))

    return builders
