"""
Build the blog.
"""
import asyncio
import logging
from pathlib import Path
from typing import Dict

import yaml

from nefelibata.announcers.base import Announcer, Interaction, get_announcers
from nefelibata.builders.base import Scope, get_builders
from nefelibata.constants import INTERACTIONS_FILENAME
from nefelibata.post import get_posts
from nefelibata.utils import get_config, load_yaml

_logger = logging.getLogger(__name__)


async def collect_site(
    announcer: Announcer,
    post_interactions,
) -> None:
    """
    Collect site interactions using a given announcer.
    """
    interactions = await announcer.collect_site()
    post_interactions.update(interactions)


async def save_interactions(
    post_directory: Path,
    interactions: Dict[str, Interaction],
) -> None:
    """
    Save new post interactions.
    """
    path = post_directory / INTERACTIONS_FILENAME
    current_interactions = load_yaml(path, Interaction)
    current_interactions.update(interactions)
    with open(path, "w", encoding="utf-8") as output:
        return yaml.dump(
            {
                name: interaction.dict()
                for name, interaction in current_interactions.items()
            },
            output,
        )


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

    posts = get_posts(root, config)

    # collect interactions from posts/site
    tasks = []
    post_interactions: Dict[Path, Dict[str, Interaction]] = {}

    _logger.info("Collecting interactions from site")
    announcers = get_announcers(root, config, Scope.SITE)
    for announcer in announcers.values():
        task = asyncio.create_task(collect_site(announcer, post_interactions))
        tasks.append(task)

    await asyncio.gather(*tasks)

    # store new interactions
    tasks = []
    for path, interactions in post_interactions.items():
        task = asyncio.create_task(save_interactions(path.parent, interactions))
        tasks.append(task)

    await asyncio.gather(*tasks)

    # build posts/site
    tasks = []

    _logger.info("Processing posts")
    builders = get_builders(root, config, Scope.POST)
    for post in posts:
        for builder in builders.values():
            task = asyncio.create_task(builder.process_post(post, force))
            tasks.append(task)

    _logger.info("Processing site")
    builders = get_builders(root, config, Scope.SITE)
    for builder in builders.values():
        task = asyncio.create_task(builder.process_site(force))
        tasks.append(task)

    await asyncio.gather(*tasks)
