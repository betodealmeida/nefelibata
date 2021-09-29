"""
Base class for publishers.
"""

from datetime import datetime
from pathlib import Path
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

    def __init__(self, root: Path, config: Config, path: str, **kwargs: Any):
        self.root = root
        self.config = config
        self.path = path
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

        build = self.root / "build" / self.path
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
    Return configured publishers.

    Publishers are defined for each build, eg:

        builders:
          ...
          gemini:
            publish-to:
              - vsftp

        publishers:
          vsftp:
            ...

    """
    classes = {
        entry_point.name: entry_point.load()
        for entry_point in iter_entry_points("nefelibata.publisher")
    }

    publishers = {}
    for builder_name, builder_parameters in config["builders"].items():
        for publisher_name in builder_parameters["publish-to"]:
            publisher_parameters = config["publishers"][publisher_name]
            plugin = publisher_parameters["plugin"]
            class_ = classes[plugin]
            path = builder_parameters["path"]

            name = f"{builder_name} => {publisher_name}"
            publishers[name] = class_(root, config, path, **publisher_parameters)

    return publishers
