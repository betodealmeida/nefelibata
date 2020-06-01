# -*- coding: utf-8 -*-
"""
Nefelibata weblog engine.

Usage:
  nb init [DIRECTORY] [--loglevel=INFO]
  nb new POST [DIRECTORY] [--loglevel=INFO]
  nb build [DIRECTORY] [-f] [--no-collect] [--loglevel=INFO]
  nb preview [-p PORT] [DIRECTORY] [--loglevel=INFO]
  nb publish [DIRECTORY] [-f] [--loglevel=INFO]

Actions:
  init              Create a new weblog skeleton.
  new               Create a new post.
  build             Build weblog from Markdown and social media interactions.
  preview           Run SimpleHTTPServer.
  publish           Publish weblog to configured locations and announce new posts.

Options:
  -h --help         Show this screen.
  --version         Show version.
  -p PORT           Port to run the web server for preview. [default: 8000]
  -f --force        Force build/publishing of up-to-date resources.
  --no-collect      Do not collect replies when building.
  --loglevel=LEVEL  Level for logging. [default: INFO]

Released under the MIT license.
(c) 2013-2020 Beto Dealmeida <roberto@dealmeida.net>

"""
import os
from pathlib import Path

from docopt import docopt
from nefelibata import __version__
from nefelibata.cli import build
from nefelibata.cli import init
from nefelibata.cli import new
from nefelibata.cli import preview
from nefelibata.cli import publish
from nefelibata.utils import find_directory
from nefelibata.utils import setup_logging

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


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
        init.run(root)
    elif arguments["new"]:
        new.run(root, arguments["POST"])
    elif arguments["build"]:
        build.run(root, arguments["--force"], not arguments["--no-collect"])
    elif arguments["preview"]:
        preview.run(root, int(arguments["-p"]))
    elif arguments["publish"]:
        publish.run(root, arguments["--force"])


if __name__ == "__main__":
    main()
