# -*- coding: utf-8 -*-
import logging
from pathlib import Path

from nefelibata.announcers import get_announcers
from nefelibata.assistants import get_assistants
from nefelibata.builders import Scope
from nefelibata.builders.categories import CategoriesBuilder
from nefelibata.builders.feed import FeedBuilder
from nefelibata.builders.index import IndexBuilder
from nefelibata.post import get_posts
from nefelibata.utils import get_config

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


def run(root: Path, force: bool = False, collect_replies: bool = True) -> None:
    """Build weblog from Markdown posts and social media interactions.
    """
    logging.info("Building weblog")

    config = get_config(root)
    logging.debug(config)

    build = root / "build"
    if not build.exists():
        logging.info("Creating build/ directory")
        build.mkdir()

    logging.info("Syncing resources")
    resources = ["css", "js", "img"]
    for resource in resources:
        resource_directory = root / "templates" / config["theme"] / resource
        target = build / resource
        if resource_directory.exists() and not target.exists():
            target.symlink_to(resource_directory, target_is_directory=True)

    logging.info("Processing posts")
    post_assistants = get_assistants(root, config, Scope.POST)
    for post in get_posts(root):
        if collect_replies:
            for announcer in get_announcers(post, config):
                announcer.update_replies()

        # TODO use post_builders here
        if force or not post.up_to_date:
            # post.create()

            for assistant in post_assistants:
                assistant.process_post(post)

        # symlink build -> posts
        post_directory = post.file_path.parent
        relative_directory = post_directory.relative_to(root / "posts")
        target = root / "build" / relative_directory
        if post_directory.exists() and not target.exists():
            target.symlink_to(post_directory, target_is_directory=True)

    # TODO use entry points; dont pass root
    IndexBuilder(root, config).process_site()
    CategoriesBuilder(root, config).process_site()
    FeedBuilder(root, config).process_site()

    # TODO call site_assistants after
