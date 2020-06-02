from enum import Enum
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from nefelibata.post import Post
from pkg_resources import iter_entry_points


class Scope(Enum):
    POST = "post"
    SITE = "site"


class Builder:

    scopes: List[Scope] = []

    def __init__(self, root: Path, config: Dict[str, Any], *args: Any, **kwargs: Any):
        self.root = root
        self.config = config

    def process_post(self, post: Post, force: bool = False) -> None:
        if Scope.POST not in self.scopes:
            raise Exception(f'Scope "post" not supported by {self.__class__.__name__}')

        raise NotImplementedError("Subclasses MUST implement `process_post`")

    def process_site(self, force: bool = False) -> None:
        if Scope.SITE not in self.scopes:
            raise Exception(f'Scope "site" not supported by {self.__class__.__name__}')

        raise NotImplementedError("Subclasses MUST implement `process_site`")


def get_builders(
    root: Path, config: Dict[str, Any], scope: Optional[Scope] = None,
) -> List[Builder]:
    names = config["builders"] or []

    builders = {a.name: a.load() for a in iter_entry_points("nefelibata.builder")}

    return [
        builders[name](root, config, **config.get(name, {}))
        for name in names
        if scope in builders[name].scopes or scope is None
    ]
