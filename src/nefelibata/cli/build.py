# -*- coding: utf-8 -*-
import logging
from pathlib import Path
from typing import Optional

from nefelibata.announcers import get_announcers
from nefelibata.assistants import get_assistants
from nefelibata.builders import get_builders
from nefelibata.builders import Scope
from nefelibata.post import get_posts
from nefelibata.post import Post
from nefelibata.utils import get_config

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"

_logger = logging.getLogger(__name__)


def run(
    root: Path,
    post: Optional[Post] = None,
    force: bool = False,
    collect_replies: bool = True,
) -> None:
    """Build weblog from Markdown posts and social media interactions.
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
    post_builders = get_builders(root, config, Scope.POST)
    post_assistants = get_assistants(root, config, Scope.POST)
    announcers = get_announcers(root, config)
    posts = [post] if post else get_posts(root)
    for post in posts:
        # freeze currently configured announcers, so that if a new announcer is
        # added in the future old posts are not announced
        if "announce-on" not in post.parsed and config["announce-on"]:
            post.parsed["announce-on"] = ", ".join(config["announce-on"])
            post.save()

        # collect replies so we can use them when building the post
        if collect_replies:
            for announcer in announcers:
                if announcer.match(post):
                    announcer.update_replies(post)

        for builder in post_builders:
            builder.process_post(post, force)
        for assistant in post_assistants:
            assistant.process_post(post, force)

        # symlink build -> posts
        post_directory = post.file_path.parent
        relative_directory = post_directory.relative_to(root / "posts")
        target = root / "build" / relative_directory
        if post_directory.exists() and not target.exists():
            target.symlink_to(post_directory, target_is_directory=True)

    site_builders = get_builders(root, config, Scope.SITE)
    site_assistants = get_assistants(root, config, Scope.SITE)
    for builder in site_builders:
        builder.process_site(force)
    for assistant in site_assistants:
        assistant.process_site(force)
