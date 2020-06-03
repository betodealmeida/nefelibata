from pathlib import Path
from typing import Any
from typing import Dict
from typing import List

from pkg_resources import iter_entry_points


class Publisher:
    def __init__(self, root: Path, config: Dict[str, Any], *args: Any, **kwargs: Any):
        self.root = root
        self.config = config

    def find_modified_files(self, force: bool, since: float) -> List[Path]:
        build = self.root / "build"
        queue = [build]
        # manually walk, since `glob("**/*")` doesn't follow symlinks
        paths: List[Path] = []
        while queue:
            current = queue.pop()
            for path in current.glob("*"):
                if not path.exists():
                    # broken symlink
                    continue
                if path.is_dir():
                    queue.append(path)
                elif force or path.stat().st_mtime > since:
                    paths.append(path)

        return paths

    def publish(self, force: bool = False) -> None:
        raise NotImplementedError("Subclasses must implement publish")


def get_publishers(root: Path, config: Dict[str, Any]) -> List[Publisher]:
    """Return all publishers.
    """
    names = config["publish-to"] or []
    if isinstance(names, str):
        names = [names]

    publishers = {p.name: p.load() for p in iter_entry_points("nefelibata.publisher")}
    return [publishers[name](root, config, **config.get(name, {})) for name in names]
