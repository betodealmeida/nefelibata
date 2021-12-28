"""
Build the blog.
"""
import asyncio
import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict

import yaml

from nefelibata.announcers.base import Announcer, Interaction, Scope, get_announcers
from nefelibata.assistants.base import get_assistants
from nefelibata.builders.base import get_builders
from nefelibata.constants import INTERACTIONS_FILENAME
from nefelibata.post import Post, get_posts
from nefelibata.utils import dict_merge, get_config, load_yaml

_logger = logging.getLogger(__name__)


async def collect_post(
    post: Post,
    announcer: Announcer,
    post_interactions,
) -> None:
    """
    Collect site interactions using a given announcer.
    """
    interactions = await announcer.collect_post(post)
    post_interactions[post.path].update(interactions)


async def collect_site(
    announcer: Announcer,
    post_interactions,
) -> None:
    """
    Collect site interactions using a given announcer.
    """
    interactions = await announcer.collect_site()
    dict_merge(post_interactions, interactions)


async def save_interactions(
    post_directory: Path,
    interactions: Dict[str, Interaction],
) -> None:
    """
    Save new post interactions.
    """
    path = post_directory / INTERACTIONS_FILENAME
    current_interactions = load_yaml(path, Interaction)
    # recursive update
    dict_merge(current_interactions, interactions)
    with open(path, "w", encoding="utf-8") as output:
        return yaml.dump(
            {
                name: interaction.dict()
                for name, interaction in current_interactions.items()
            },
            output,
        )


async def run(  # pylint: disable=too-many-locals
    root: Path,
    force: bool = False,
) -> None:
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
    post_interactions: Dict[Path, Dict[str, Interaction]] = defaultdict(dict)

    _logger.info("Collecting interactions from posts")
    announcers = get_announcers(root, config, Scope.POST)
    for post in posts:
        for name, announcer in announcers.items():
            if name in post.announcers:
                task = asyncio.create_task(
                    collect_post(post, announcer, post_interactions),
                )
                tasks.append(task)

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

    # run assistants
    tasks = []

    _logger.info("Running post assistants")
    assistants = get_assistants(root, config, Scope.POST)
    for post in posts:
        for assistant in assistants.values():
            task = asyncio.create_task(assistant.process_post(post, force))
            tasks.append(task)

    _logger.info("Running site assistants")
    assistants = get_assistants(root, config, Scope.SITE)
    for assistant in assistants.values():
        task = asyncio.create_task(assistant.process_site(force))
        tasks.append(task)

    await asyncio.gather(*tasks)

    # build posts/site
    tasks = []
    builders = get_builders(root, config)

    _logger.info("Processing posts")
    for post in posts:
        for builder in builders.values():
            task = asyncio.create_task(builder.process_post(post, force))
            tasks.append(task)

    _logger.info("Processing site")
    for builder in builders.values():
        task = asyncio.create_task(builder.process_site(force))
        tasks.append(task)

    await asyncio.gather(*tasks)
