import sqlite3
from enum import Enum
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List

from pkg_resources import iter_entry_points

from nefelibata.builders import Builder
from nefelibata.builders import Scope
from nefelibata.post import Post


# should the assistant run before or after the builders?
class Order(Enum):
    BEFORE = "BEFORE"
    AFTER = "AFTER"


class Assistant(Builder):

    order = Order.AFTER


def get_assistants(
    root: Path,
    config: Dict[str, Any],
    scope: Scope,
    connection: sqlite3.Connection,
) -> List[Assistant]:
    names = config["assistants"] or []

    assistants = {a.name: a.load() for a in iter_entry_points("nefelibata.assistant")}

    return [
        assistants[name](root, config, connection, **config.get(name, {}))
        for name in names
        if scope in assistants[name].scopes or scope is None
    ]
