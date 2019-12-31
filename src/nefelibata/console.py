# -*- coding: utf-8 -*-
"""
Nefelibata weblog engine.

Usage:
  nb init [DIRECTORY] [--loglevel=INFO]
  nb new POST [DIRECTORY] [--loglevel=INFO]
  nb build [DIRECTORY] [-f] [--no-collect] [--loglevel=INFO]
  nb preview [-p PORT] [DIRECTORY] [--loglevel=INFO]
  nb publish [DIRECTORY] [-f] [--loglevel=INFO]
  nb facebook [DIRECTORY] [--loglevel=INFO]

Actions:
  init              Create a new weblog skeleton.
  new               Create a new post.
  build             Build weblog from Markdown and social media interactions.
  preview           Run SimpleHTTPServer and open browser.
  publish           Publish weblog to configured locations and announce new posts.
  facebook          Get a 60-day access token for Facebook announcer.

Options:
  -h --help         Show this screen.
  --version         Show version.
  -p PORT           Port to run the web server for preview. [default: 8000]
  -f --force        Force rebuild of HTML.
  --no-collect      Do not collect replies when building.
  --loglevel=LEVEL  Level for logging. [default: INFO]

Released under the MIT license.
(c) 2013-2019 Beto Dealmeida <roberto@dealmeida.net>

"""

import logging
import os
import re
import shutil
import socketserver
import sys
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from subprocess import call

from docopt import docopt
from pkg_resources import resource_filename, resource_listdir

from nefelibata import __version__, config_filename, new_post
from nefelibata.announcers import get_announcers
from nefelibata.announcers.facebook import generate_access_token
from nefelibata.index import create_categories, create_feed, create_index
from nefelibata.post import Post, get_posts
from nefelibata.publishers import get_publishers
from nefelibata.utils import get_config

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"

_logger = logging.getLogger("nefelibata")


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


def sanitize(directory: str) -> str:
    """Sanitize a psot title into a directory name.

    Args:
      directory (str): a string representing the post title
    """
    directory = directory.lower().replace(" ", "_")
    directory = re.sub("[^\w]", "", directory)

    return directory


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


def new(root: Path, directory: str) -> None:
    """Create a new post and open editor.

    Args:
      root (str): directory where the weblog lives
      directory (str): name of directory for the post
    """
    _logger.info("Creating new directory")
    title = directory
    directory = sanitize(directory)
    target = root / "posts" / directory
    if target.exists():
        raise IOError("Directory already exists!")
    target.mkdir()
    os.chdir(target)

    _logger.info("Adding resource files")
    resources = ["css", "js", "img"]
    for resource in resources:
        (target / resource).mkdir()

    filepath = target / "index.mkd"
    with open(filepath, "w") as fp:
        fp.write(new_post.format(title=title))

    editor = os.environ.get("EDITOR")
    if not editor:
        _logger.info("No EDITOR found, exiting")
        return

    call([editor, filepath])


def build(root: Path, force: bool = False, collect_replies: bool = True) -> None:
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
    for post in get_posts(root):
        if collect_replies:
            for announcer in get_announcers(post, config):
                announcer.update_replies()

        if force or not post.up_to_date:
            post.create()

        # symlink build -> posts
        post_directory = post.file_path.parent
        relative_directory = post_directory.relative_to(root / "posts")
        target = root / "build" / relative_directory
        if post_directory.exists() and not target.exists():
            target.symlink_to(post_directory, target_is_directory=True)

    _logger.info("Creating index")
    create_index(root)

    _logger.info("Creating category pages")
    create_categories(root)

    _logger.info("Creating Atom feed")
    create_feed(root)


def preview(root: Path, port: int = 8000) -> None:
    """Run a local HTTP server and open browser.

    Args:
      root (str): directory where the weblog lives
    """
    _logger.info("Previewing weblog")

    build = root / "build"
    os.chdir(build)

    with socketserver.TCPServer(("", port), SimpleHTTPRequestHandler) as httpd:
        _logger.info(f"Running HTTP server on port {port}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            _logger.info("Exiting")
            httpd.shutdown()


def publish(root: Path, force: bool = False) -> None:
    """Publish weblog.

    Args:
      root (str): directory where the weblog lives
    """
    _logger.info("Publishing weblog")

    config = get_config(root)
    _logger.debug(config)

    for publisher in get_publishers(config):
        publisher.publish(root, force)

    # announce posts
    for post in get_posts(root):
        for announcer in get_announcers(post, config):
            announcer.update_links()


def facebook(root: Path) -> None:
    """Get 60-day FB access token for announcer.

    Args:
      root (str): directory where the weblog lives
    """
    _logger.info("Getting long-lived FB token.")

    config = get_config(root)
    _logger.debug(config)

    section = config["facebook"]
    token = generate_access_token(
        section["app_id"], section["app_secret"], section["short_lived_token"]
    )

    sys.stdout.write(f"Long-lived FB access token: {token}\n")
    _logger.info("Success!")


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
    elif arguments["new"]:
        new(root, arguments["POST"])
    elif arguments["build"]:
        build(root, arguments["--force"], not arguments["--no-collect"])
    elif arguments["preview"]:
        preview(root, int(arguments["-p"]))
    elif arguments["publish"]:
        publish(root, arguments["--force"])
    elif arguments["facebook"]:
        facebook(root)


if __name__ == "__main__":
    main()
