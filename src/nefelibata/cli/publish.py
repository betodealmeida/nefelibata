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

    for publisher in get_publishers(root, config):
        publisher.publish(force)

    # announce posts
    announcers = get_announcers(root, config)
    for post in get_posts(root):
        for announcer in announcers:
            if announcer.match(post):
                announcer.update_links(post)
