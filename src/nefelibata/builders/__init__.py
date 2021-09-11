import sqlite3
from datetime import datetime
from datetime import timezone
from enum import Enum
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List

from pkg_resources import iter_entry_points

from nefelibata.post import Post


class Scope(Enum):
    POST = "POST"
    SITE = "SITE"


class Builder:

    scopes: List[Scope] = []

    def __init__(
        self,
        root: Path,
        config: Dict[str, Any],
        connection: sqlite3.Connection,
        *args: Any,
        **kwargs: Any,
    ):
        self.root = root
        self.config = config
        self.connection = connection

    def is_path_up_to_date(self, path: Path) -> bool:
        cursor = self.connection.cursor()
        results = cursor.execute(
            """
                SELECT last_updated
                FROM updates
                WHERE plugin = ? AND path = ?
                ORDER BY last_updated DESC;
            """,
            (self.__class__.__name__, str(path.resolve())),
        )
        row = results.fetchone()
        if row is None:
            return False
        return row[0].timestamp() > path.stat().st_mtime

    def update_path(self, path: Path) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
                INSERT INTO updates (plugin, path, last_updated)
                VALUES (?, ?, ?)
                ON CONFLICT (plugin, path) DO UPDATE SET
                  last_updated = ?;
            """,
            (
                self.__class__.__name__,
                str(path.resolve()),
                datetime.now(tz=timezone.utc),
                datetime.now(tz=timezone.utc),
            ),
        )

    def process_post(self, post: Post, force: bool = False) -> None:
        if Scope.POST not in self.scopes:
            raise Exception(f'Scope "post" not supported by {self.__class__.__name__}')

        raise NotImplementedError("Subclasses MUST implement `process_post`")

    def process_site(self, force: bool = False) -> None:
        if Scope.SITE not in self.scopes:
            raise Exception(f'Scope "site" not supported by {self.__class__.__name__}')

        raise NotImplementedError("Subclasses MUST implement `process_site`")


def get_builders(
    root: Path,
    config: Dict[str, Any],
    scope: Scope,
    connection: sqlite3.Connection,
) -> List[Builder]:
    names = config["builders"] or []

    builders = {a.name: a.load() for a in iter_entry_points("nefelibata.builder")}

    return [
        builders[name](root, config, connection, **config.get(name, {}))
        for name in names
        if scope in builders[name].scopes or scope is None
    ]
