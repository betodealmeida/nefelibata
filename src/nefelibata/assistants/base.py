"""
Base class for assistants.
"""
# pylint: disable=unused-argument, no-self-use

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pkg_resources import iter_entry_points

from nefelibata.announcers.base import Scope
from nefelibata.config import Config
from nefelibata.post import Post

_logger = logging.getLogger(__name__)


class Assistant:

    """
    A post assistant.

    Assistants run before builders, getting extra metadata and storing it in YAML
    files alongside the post.
    """

    name = ""
    scopes: List[Scope] = []

    def __init__(self, root: Path, config: Config, **kwargs: Any):
        self.root = root
        self.config = config
        self.kwargs = kwargs

    async def process_post(self, post: Post, force: bool = False) -> None:
        """
        Pre-process a post before it's built.
        """
        path = post.path.parent / f"{self.name}.yaml"
        if path.exists() and not force:
            return

        metadata = await self.get_post_metadata(post)
        if not metadata:
            return

        with open(path, "w", encoding="utf-8") as output:
            output.write(yaml.dump(metadata))

    async def get_post_metadata(self, post: Post) -> Dict[str, Any]:
        """
        Compute the metadata for a given post.
        """
        return {}

    async def process_site(self, force: bool = False) -> None:
        """
        Pre-process a site before it's built.
        """
        path = self.root / f"{self.name}.yaml"
        if path.exists() and not force:
            return

        metadata = await self.get_site_metadata()
        if not metadata:
            return

        with open(path, "w", encoding="utf-8") as output:
            output.write(yaml.dump(metadata))

    async def get_site_metadata(self) -> Dict[str, Any]:
        """
        Compute the metadata for the site.
        """
        return {}


def get_assistants(
    root: Path,
    config: Config,
    scope: Optional[Scope] = None,
) -> Dict[str, Assistant]:
    """
    Return configured assistants.
    """
    classes = {
        assistant.name: assistant.load()
        for assistant in iter_entry_points("nefelibata.assistant")
    }

    assistants = {}
    for assistant_name, assistant_config in config.assistants.items():
        class_ = classes[assistant_config.plugin]

        if scope is None or scope in class_.scopes:
            assistants[assistant_name] = class_(root, config, **assistant_config.dict())

    return assistants
