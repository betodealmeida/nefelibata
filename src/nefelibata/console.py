"""
Nefelibata blog engine.

Usage:
  nb init [ROOT_DIR] [-f] [--loglevel=INFO]
  nb build [ROOT_DIR] [-f] [--loglevel=INFO]

Actions:
  init              Create a new blog skeleton.
  build             Build blog from Markdown files and online interactions.

Options:
  -h --help         Show this screen.
  --version         Show version.
  -f --force        Force building up-to-date resources.
  --loglevel=LEVEL  Level for logging. [default: INFO]

Released under the MIT license.
(c) 2013 Beto Dealmeida <roberto@dealmeida.net>
"""
import asyncio
import logging
import os
from pathlib import Path

from docopt import docopt

from nefelibata import __version__
from nefelibata.cli import build, init
from nefelibata.utils import find_directory, setup_logging

_logger = logging.getLogger(__name__)


async def main() -> None:
    """
    Dispatch command.
    """
    arguments = docopt(__doc__, version=__version__)

    setup_logging(arguments["--loglevel"])

    if arguments["ROOT_DIR"] is None:
        root = find_directory(Path(os.getcwd()))
    else:
        root = Path(arguments["ROOT_DIR"])

    try:
        if arguments["build"]:
            await build.run(root, arguments["--force"])
        elif arguments["init"]:
            await init.run(root, arguments["--force"])
    except asyncio.CancelledError:
        _logger.info("Canceled")


def run() -> None:
    """
    Run Nefelibata.

    This is also an entry point for the CLI.
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _logger.info("Stopping Nefelibata")


if __name__ == "__main__":
    run()
