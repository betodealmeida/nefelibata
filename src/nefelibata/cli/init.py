# -*- coding: utf-8 -*-
import logging
import os
import shutil
import sqlite3
import textwrap
from pathlib import Path

from pkg_resources import resource_filename
from pkg_resources import resource_listdir

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


_logger = logging.getLogger(__name__)


def create_tables(root: Path) -> None:
    """
    Create support tables.
    """
    connection = sqlite3.connect(str(root / "nefelibata.db"))
    cursor = connection.cursor()

    cursor.execute(
        textwrap.dedent(
            """
        CREATE TABLE IF NOT EXISTS updates (
            plugin TEXT,
            path TEXT,
            last_updated TIMESTAMP,
            PRIMARY KEY (plugin, path)
        );
            """
        )
    )


def run(root: Path) -> None:
    """
    Create initial structure for weblog.
    """
    resources = resource_listdir("nefelibata", "skeleton")

    for resource in resources:
        origin = Path(
            resource_filename("nefelibata", os.path.join("skeleton", resource)),
        )
        target = root / resource

        # good guy Greg does not overwrite existing files
        if target.exists():
            resource_type = "Directory" if origin.is_dir() else "File"
            raise IOError(f"{resource_type} {target} already exists!")
        if origin.is_dir():
            shutil.copytree(origin, target)
        else:
            shutil.copy(origin, target)

    create_tables(root)

    _logger.info("Weblog created!")
