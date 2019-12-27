# -*- coding: utf-8 -*-
"""
Nefelibata weblog engine.

Usage:
  nb init [DIRECTORY] [--loglevel=INFO]
  nb build [DIRECTORY] [--loglevel=INFO]
  nb preview [-p PORT] [DIRECTORY] [--loglevel=INFO]
  nb publish [DIRECTORY] [--loglevel=INFO]
  nb facebook <short_access_token> <app_id> <app_secret> [--loglevel=INFO]

Actions:
  init              Create a new weblog skeleton.
  build             Build weblog from Markdown and social media interactions.
  preview           Run SimpleHTTPServer and open browser.
  publish           Publish weblog to configured locations and announce new posts.
  facebook          Create a long term token for Facebook Graph API.

Options:
  -h --help         Show this screen.
  --version         Show version.
  -p PORT           Port to run the web server for preview. [default: 8000]
  --loglevel=LEVEL  Level for logging. [default: INFO]

Released under the MIT license.
(c) 2013-2019 Beto Dealmeida <roberto@dealmeida.net>

"""

import logging
import os
import shutil
import sys
from pathlib import Path

from docopt import docopt
from pkg_resources import iter_entry_points, resource_filename, resource_listdir

from nefelibata import __version__

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"

_logger = logging.getLogger(__name__)


config = "nefelibata.yaml"


def setup_logging(loglevel: str) -> None:
    """Setup basic logging

    Args:
      loglevel (str): minimum loglevel for emitting messages
    """
    level = getattr(logging, loglevel.upper(), None)
    if not isinstance(level, int):
        raise ValueError("Invalid log level: %s" % loglevel)

    logformat = "[%(asctime)s] %(levelname)s: %(name)s: %(message)s"
    logging.basicConfig(
        level=level, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )


def find_directory(cwd: Path) -> Path:
    """Find root of blog, starting from `cwd`.

    The function will traverse up trying to find a configuration file.

    Args:
      cwd (str): starting directory
    """
    while not (cwd / config).exists():
        if cwd == cwd.parent:
            raise SystemExit("No configuration found!")
        cwd = cwd.parent

    return cwd


def init(root: Path) -> None:
    """Create initial structure for weblog.

    Args:
      root (str): directory where the weblog should be initialized
    """
    resources = resource_listdir("nefelibata", "skeleton")

    for resource in resources:
        origin = Path(
            resource_filename("nefelibata", os.path.join("skeleton", resource))
        )
        target = root / resource
        # good guy Greg does not overwrite existing files
        if target.exists():
            raise IOError("File already exists!")
        if origin.is_dir():
            shutil.copytree(origin, target)
        else:
            shutil.copy(origin, target)

    _logger.info("Weblog created!")


def main() -> None:
    """Main entry point allowing external calls
    """
    arguments = docopt(__doc__, version=__version__)

    setup_logging(arguments["--loglevel"])

    if arguments["DIRECTORY"] is None:
        if arguments["init"]:
            root = Path(".")
        else:
            root = find_directory(Path(os.getcwd()))
    else:
        root = Path(arguments["DIRECTORY"])

    if arguments["init"]:
        init(root)
    elif arguments["build"]:
        build(root)
    elif arguments["preview"]:
        preview(root, int(arguments["-p"]))


if __name__ == "__main__":
    run()
