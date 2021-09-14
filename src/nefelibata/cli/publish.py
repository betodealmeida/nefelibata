"""
Publish the blog.
"""
import asyncio
import logging
from pathlib import Path

from nefelibata.publishers.base import get_publishers
from nefelibata.utils import get_config

_logger = logging.getLogger(__name__)


async def run(root: Path, force: bool = False) -> None:
    """
    Publish blog.
    """
    _logger.info("Publishing blog")

    config = get_config(root)
    _logger.debug(config)

    tasks = []
    for publisher in get_publishers(root, config):
        task = asyncio.create_task(publisher.publish(force))
        tasks.append(task)

    await asyncio.gather(*tasks)
