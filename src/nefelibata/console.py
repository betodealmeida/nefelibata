# -*- coding: utf-8 -*-
"""
Nefelibata weblog engine.

Usage:
  nb init [ROOT_DIR] [--loglevel=INFO]
  nb new POST [ROOT_DIR] [--loglevel=INFO]
  nb build [ROOT_DIR] [-f] [-s POST_DIR] [--no-collect] [--loglevel=INFO]
  nb preview [-p PORT] [ROOT_DIR] [--loglevel=INFO]
  nb publish [ROOT_DIR] [-f] [-s POST_DIR] [--loglevel=INFO]

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
  -s POST_DIR       Build/publish a single post by specifying its directory
  --no-collect      Do not collect replies when building.
  --loglevel=LEVEL  Level for logging. [default: INFO]

Released under the MIT license.
(c) 2013-2020 Beto Dealmeida <roberto@dealmeida.net>

"""
import os
from pathlib import Path
from typing import Optional

from docopt import docopt
from nefelibata import __version__
from nefelibata.cli import build
from nefelibata.cli import init
from nefelibata.cli import new
from nefelibata.cli import preview
from nefelibata.cli import publish
from nefelibata.post import Post
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

    if arguments["ROOT_DIR"] is None:
        if arguments["init"]:
            root = Path(".")
        else:
            root = find_directory(Path(os.getcwd()))
    else:
        root = Path(arguments["ROOT_DIR"])

    post: Optional[Post]
    if arguments["-s"] is None:
        post = None
    elif arguments["-s"].endswith("index.mkd"):
        post = Post(Path(arguments["-s"]).resolve())
    else:
        post = Post(Path(arguments["-s"]).resolve() / "index.mkd")

    if arguments["init"]:
        init.run(root)
    elif arguments["new"]:
        new.run(root, arguments["POST"])
    elif arguments["build"]:
        build.run(root, post, arguments["--force"], not arguments["--no-collect"])
    elif arguments["preview"]:
        preview.run(root, int(arguments["-p"]))
    elif arguments["publish"]:
        publish.run(root, post, arguments["--force"])


if __name__ == "__main__":
    main()
