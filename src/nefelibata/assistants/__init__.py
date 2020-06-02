from enum import Enum
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from nefelibata.builders import Builder
from nefelibata.builders import Scope
from nefelibata.post import Post
from pkg_resources import iter_entry_points


class Assistant(Builder):

    pass


def get_assistants(
    root: Path, config: Dict[str, Any], scope: Optional[Scope] = None,
) -> List[Assistant]:
    names = config["assistants"] or []

    assistants = {a.name: a.load() for a in iter_entry_points("nefelibata.assistant")}

    return [
        assistants[name](root, config, **config.get(name, {}))
        for name in names
        if scope in assistants[name].scopes or scope is None
    ]
