import copy
import json
import logging
import re
import sys
import unicodedata
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Iterator

import yaml
from bs4 import BeautifulSoup
from libgravatar import Gravatar
from nefelibata import config_filename
from rich.logging import RichHandler


def get_config(root: Path) -> Dict[str, Any]:
    """Return the configuration file for a weblog.
    """
    with open(root / config_filename) as fp:
        config: Dict[str, Any] = yaml.full_load(fp)

    # add gravatar as the default profile picture
    if "profile_picture" not in config["author"]:
        config["author"]["profile_picture"] = Gravatar(
            config["author"]["email"],
        ).get_image()

    return config


def setup_logging(loglevel: str) -> None:
    """Setup basic logging
    """
    level = getattr(logging, loglevel.upper(), None)
    if not isinstance(level, int):
        raise ValueError("Invalid log level: %s" % loglevel)

    logformat = "[%(asctime)s] %(levelname)s: %(name)s: %(message)s"
    logging.basicConfig(
        level=level,
        format=logformat,
        datefmt="[%X]",
        handlers=[RichHandler()],
        force=True,
    )


def find_directory(cwd: Path) -> Path:
    """Find root of blog, starting from `cwd`.

    The function will traverse up trying to find a configuration file.
    """
    while not (cwd / config_filename).exists():
        if cwd == cwd.parent:
            raise SystemExit("No configuration found!")
        cwd = cwd.parent

    return cwd


def strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("utf-8")

    return str(text)


def sanitize(directory: str) -> str:
    """Sanitize a post title into a directory name.
    """
    directory = directory.lower().replace(" ", "_")
    directory = re.sub(r"[^\w]", "", directory)
    directory = strip_accents(directory)

    return directory


@contextmanager
def json_storage(file_path: Path) -> Iterator[Dict[str, Any]]:
    """
    Open a file and load it as JSON. Save back if modified.
    """
    if file_path.exists():
        with open(file_path) as fp:
            storage = json.load(fp)
    else:
        storage = {}

    original = copy.deepcopy(storage)
    try:
        yield storage
    finally:
        if storage != original:
            with open(file_path, "w") as fp:
                json.dump(storage, fp)


@contextmanager
def modify_html(file_path: Path) -> Iterator[BeautifulSoup]:
    """
    Parse an HTML file to BeautifulSoup. Save back if modified.
    """
    with open(file_path) as fp:
        html = fp.read()
    soup = BeautifulSoup(html, "html.parser")

    original = str(soup)
    try:
        yield soup
    finally:
        html = str(soup)
        if html != original:
            with open(file_path, "w") as fp:
                fp.write(html)
