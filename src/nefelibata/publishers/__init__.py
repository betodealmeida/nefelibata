from pathlib import Path
from typing import Any, Dict, List

from pkg_resources import iter_entry_points


class Publisher:
    def publish(root: Path, force: bool = False) -> None:
        raise NotImplementedError("Subclasses must implement publish")


def get_publishers(config: Dict[str, Any]) -> List[Publisher]:
    """Return all publishers.
    """
    names = config["publish-to"] or []
    if isinstance(names, str):
        names = [names]

    publishers = {p.name: p.load() for p in iter_entry_points("nefelibata.publisher")}
    return [publishers[name](**config[name]) for name in names]
