"""
Base class for assistants.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from pkg_resources import iter_entry_points

from nefelibata.announcers.base import Scope
from nefelibata.post import Post
from nefelibata.typing import Config

_logger = logging.getLogger(__name__)


class Assistant:

    """
    A post assistant.

    Assistants run before builders, getting extra metadata and storing it in YAML
    files alongside the post.
    """

    scopes: List[Scope] = []

    def __init__(self, root: Path, config: Config, **kwargs: Any):
        self.root = root
        self.config = config
        self.kwargs = kwargs

    async def process_post(self, post: Post) -> None:
        """
        Publish a post externally.
        """

    async def process_site(self) -> None:
        """
        Publish a site externally.
        """


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
    for name, parameters in config["assistants"].items():
        plugin = parameters["plugin"]
        class_ = classes[plugin]

        if scope is None or scope in class_.scopes:
            assistants[name] = class_(root, config, **parameters)

    return assistants
