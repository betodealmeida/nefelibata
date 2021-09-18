"""
Base class for publishers.
"""

from datetime import datetime
from pathlib import Path
from pprint import pformat
from typing import Any, Dict, Iterator, Optional

from pkg_resources import iter_entry_points
from pydantic import BaseModel

from nefelibata.typing import Config


class Publishing(BaseModel):  # pylint: disable=too-few-public-methods
    """
    Model for publishings.
    """

    timestamp: datetime


class Publisher:

    """
    A blog publisher.
    """

    name = ""

    def __init__(self, root: Path, config: Config, **kwargs: Any):
        self.root = root
        self.config = config
        self.kwargs = kwargs

    async def publish(
        self,
        since: Optional[datetime] = None,
        force: bool = False,
    ) -> Optional[Publishing]:
        """
        Publish the site to a given location.
        """
        raise NotImplementedError("Subclasses MUST implement `publish`")

    def find_modified_files(
        self,
        force: bool,
        since: Optional[datetime],
    ) -> Iterator[Path]:
        """
        Return modified files since ``since``.
        """
        # convert to timestamp to compare with ``st_mtime``
        last_published = since.timestamp() if since else 0

        build = self.root / "build"
        queue = [build]
        while queue:
            current = queue.pop()
            for path in current.glob("*"):
                if path.is_dir():
                    queue.append(path)
                elif force or path.stat().st_mtime > last_published:
                    yield path


def get_publishers(root: Path, config: Config) -> Dict[str, Publisher]:
    """
    Return all the publishers.
    """
    classes = {
        entry_point.name: entry_point.load()
        for entry_point in iter_entry_points("nefelibata.publisher")
    }

    publishers = {}
    for name, parameters in config["publishers"].items():
        if "plugin" not in parameters:
            raise Exception(
                f'Invalid configuration, missing "plugin": {pformat(parameters)}',
            )
        plugin = parameters["plugin"]
        class_ = classes[plugin]
        kwargs = {k: v for k, v in parameters.items() if k != "plugin"}

        publishers[name] = class_(root, config, **kwargs)

    return publishers
