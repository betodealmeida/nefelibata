# -*- coding: utf-8 -*-
"""
Nefelibata weblog engine.

Usage:
  nb init [DIRECTORY] [--loglevel=INFO]
  nb build [DIRECTORY] [-f] [--loglevel=INFO]
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
  -f --force        Force rebuild of HTML.
  --loglevel=LEVEL  Level for logging. [default: INFO]

Released under the MIT license.
(c) 2013-2019 Beto Dealmeida <roberto@dealmeida.net>

"""

from http.server import SimpleHTTPRequestHandler
import logging
import os
import shutil
import socketserver
import sys
from pathlib import Path

from docopt import docopt
from pkg_resources import iter_entry_points, resource_filename, resource_listdir

from nefelibata import __version__, config_filename
from nefelibata.index import create_index
from nefelibata.post import Post
from nefelibata.utils import get_config, get_posts

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"

_logger = logging.getLogger(__name__)


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
    while not (cwd / config_filename).exists():
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


def build(root: Path, force: bool = False) -> None:
    """Build weblog from Markdown posts and social media interactions.

    Args:
      root (str): directory where the weblog lives
    """
    _logger.info("Building weblog")

    config = get_config(root)
    _logger.debug(config)

    build = root / "build"
    if not build.exists():
        _logger.info("Creating build/ directory")
        build.mkdir()

    _logger.info("Syncing resources")
    resources = ["css", "js", "img"]
    for resource in resources:
        resource_directory = root / "templates" / config["theme"] / resource
        target = build / resource
        if resource_directory.exists() and not target.exists():
            target.symlink_to(resource_directory, target_is_directory=True)

    _logger.info("Processing posts")
    posts = get_posts(root)
    for post in posts:
        if force or not post.up_to_date:
            post.create()

        # symlink build -> posts
        post_directory = post.file_path.parent
        relative_directory = post_directory.relative_to(root / "posts")
        target = root / "build" / relative_directory
        if not target.exists():
            target.symlink_to(post_directory, target_is_directory=True)

    _logger.info("Creating index")
    create_index(root)


def preview(root: Path, port: int = 8000) -> None:
    """Run a local HTTP server and open browser.

    Args:
      root (str): directory where the weblog lives
    """
    build = root / "build"
    os.chdir(build)

    with socketserver.TCPServer(("", port), SimpleHTTPRequestHandler) as httpd:
        _logger.info(f"Running HTTP server on port {port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            _logger.info("Exiting")
            httpd.shutdown()


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
        build(root, arguments["--force"])
    elif arguments["preview"]:
        preview(root, int(arguments["-p"]))


if __name__ == "__main__":
    main()
