"""
Nefelibata blog engine.

Usage:
  nb init [ROOT_DIR] [-f] [--loglevel=INFO]
  nb new POST [ROOT_DIR] [-t TYPE] [--loglevel=INFO]
  nb build [ROOT_DIR] [-f] [--loglevel=INFO]
  nb publish [ROOT_DIR] [-f] [--loglevel=INFO]

Actions:
  init              Create a new blog skeleton.
  new               Create a new post.
  build             Build blog from Markdown files and online interactions.
  publish           Publish weblog to configured locations.

Options:
  -h --help         Show this screen.
  --version         Show version.
  -f --force        Force operation (eg, building up-to-date resources).
  -t TYPE           Custom template to use on the post. [default: post]
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
from nefelibata.cli import build, init, new, publish
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
        if arguments["init"]:
            await init.run(root, arguments["--force"])
        elif arguments["new"]:
            await new.run(root, arguments["POST"], arguments["-t"])
        elif arguments["build"]:
            await build.run(root, arguments["--force"])
        elif arguments["publish"]:
            await publish.run(root, arguments["--force"])
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
