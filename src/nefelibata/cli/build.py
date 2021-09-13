"""
Build the blog.
"""
import asyncio
import logging
from pathlib import Path

from nefelibata.builders.base import Scope, get_builders
from nefelibata.post import get_posts
from nefelibata.utils import get_config

_logger = logging.getLogger(__name__)


async def run(root: Path, force: bool = False) -> None:
    """
    Build blog from Markdown files and online interactions.
    """
    _logger.info("Building blog")

    config = get_config(root)
    _logger.debug(config)

    build = root / "build"
    if not build.exists():
        _logger.info("Creating `build/` directory")
        build.mkdir()

    tasks = []

    _logger.info("Processing posts")
    posts = get_posts(root, config)
    builders = get_builders(root, config, Scope.POST)
    for post in posts:
        for builder in builders:
            task = asyncio.create_task(builder.process_post(post, force))
            tasks.append(task)

    _logger.info("Processing site")
    builders = get_builders(root, config, Scope.SITE)
    for builder in builders:
        task = asyncio.create_task(builder.process_site(force))
        tasks.append(task)

    await asyncio.gather(*tasks)
