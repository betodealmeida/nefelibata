# -*- coding: utf-8 -*-
import logging
from pathlib import Path

from nefelibata.announcers import get_announcers
from nefelibata.post import get_posts
from nefelibata.publishers import get_publishers
from nefelibata.utils import get_config

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"

_logger = logging.getLogger(__name__)


def run(root: Path, force: bool = False) -> None:
    """Publish weblog.
    """
    _logger.info("Publishing weblog")

    config = get_config(root)
    _logger.debug(config)

    for publisher in get_publishers(config):
        publisher.publish(root, force)

    # announce posts
    for post in get_posts(root):
        # freeze currently configured announcers, so that if a new announcer is
        # added in the future old posts are not announced
        if "announce-on" not in post.parsed:
            post.parsed["announce-on"] = ", ".join(config["announce-on"])
            post.save()

        for announcer in get_announcers(post, config):
            announcer.update_links()
