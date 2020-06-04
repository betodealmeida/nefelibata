import logging
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any
from typing import Dict

import yaml
from libgravatar import Gravatar
from nefelibata import config_filename


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
        stream=sys.stdout,
        format=logformat,
        datefmt="%Y-%m-%d %H:%M:%S",
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
