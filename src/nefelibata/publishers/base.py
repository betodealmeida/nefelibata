"""
Base class for publishers.
"""

from datetime import datetime
from pathlib import Path
from pprint import pformat
from typing import Any, Iterator, List

from pkg_resources import iter_entry_points

from nefelibata.typing import Config


class Publisher:

    """
    A blog publisher.
    """

    name = ""

    def __init__(self, root: Path, config: Config, **kwargs: Any):
        self.root = root
        self.config = config
        self.kwargs = kwargs

    async def publish(self, force: bool = False) -> None:
        """
        Publish the site to a given location.
        """
        raise NotImplementedError("Subclasses MUST implement `publish`")

    def find_modified_files(self, force: bool, since: datetime) -> Iterator[Path]:
        """
        Return modified files since ``since``.
        """
        # convert to timestamp to compare with ``st_mtime``
        last_published = since.timestamp()

        build = self.root / "build"
        queue = [build]
        while queue:
            current = queue.pop()
            for path in current.glob("*"):
                if path.is_dir():
                    queue.append(path)
                elif force or path.stat().st_mtime > last_published:
                    yield path


def get_publishers(root: Path, config: Config) -> List[Publisher]:
    """
    Return all the publishers.
    """
    classes = {
        entry_point.name: entry_point.load()
        for entry_point in iter_entry_points("nefelibata.publisher")
    }

    publishers = []
    for parameters in config["publishers"]:
        if "plugin" not in parameters:
            raise Exception(
                f'Invalid configuration, missing "plugin": {pformat(parameters)}',
            )
        name = parameters["plugin"]
        class_ = classes[name]
        kwargs = {k: v for k, v in parameters.items() if k != "plugin"}

        publishers.append(class_(root, config, **kwargs))

    return publishers
