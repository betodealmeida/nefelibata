"""
Publish the blog.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

import yaml

from nefelibata.announcers.base import Announcement, Announcer, Scope, get_announcers
from nefelibata.constants import ANNOUNCEMENTS_FILENAME, PUBLISHINGS_FILENAME
from nefelibata.post import Post, get_posts
from nefelibata.publishers.base import Publisher, Publishing, get_publishers
from nefelibata.utils import get_config, load_yaml

_logger = logging.getLogger(__name__)


async def publish_site(
    name: str,
    publisher: Publisher,
    publishings: Dict[str, Publishing],
    since: Optional[datetime],
    force: bool = False,
) -> None:
    """
    Announce a site and store the result.
    """
    publishing = await publisher.publish(since, force)
    if publishing:
        publishings[name] = publishing


async def announce_site(
    name: str,
    announcer: Announcer,
    announcements: Dict[str, Announcement],
) -> None:
    """
    Announce a site and store the result.
    """
    announcement = await announcer.announce_site()
    if announcement:
        announcements[name] = announcement


async def announce_post(
    name: str,
    announcer: Announcer,
    post: Post,
    announcements: Dict[str, Announcement],
) -> None:
    """
    Announce a post and store the result.
    """
    announcement = await announcer.announce_post(post)
    if announcement:
        announcements[name] = announcement


async def save_announcements(
    post_directory: Path,
    announcements: Dict[str, Announcement],
) -> None:
    """
    Save modified post announcements.
    """
    path = post_directory / ANNOUNCEMENTS_FILENAME
    with open(path, "w", encoding="utf-8") as output:
        return yaml.dump(
            {name: announcement.dict() for name, announcement in announcements.items()},
            output,
        )


async def run(  # pylint: disable=too-many-locals
    root: Path,
    force: bool = False,
) -> None:
    """
    Publish blog.
    """
    _logger.info("Publishing blog")

    config = get_config(root)
    _logger.debug(config)

    # publish site
    publishings = load_yaml(root / PUBLISHINGS_FILENAME, Publishing)
    tasks = []
    for name, publisher in get_publishers(root, config).items():
        since = publishings[name].timestamp if name in publishings else None
        task = asyncio.create_task(
            publish_site(name, publisher, publishings, since, force),
        )
        tasks.append(task)

    await asyncio.gather(*tasks)

    # persist publishings
    with open(root / PUBLISHINGS_FILENAME, "w", encoding="utf-8") as output:
        yaml.dump(
            {name: publishing.dict() for name, publishing in publishings.items()},
            output,
        )

    # announcements
    tasks = []

    # announce site
    site_announcements = load_yaml(root / ANNOUNCEMENTS_FILENAME, Announcement)
    last_published = max(publishing.timestamp for publishing in publishings.values())
    announcers = get_announcers(root, config, Scope.SITE)
    for name, announcer in announcers.items():
        if (
            name in site_announcements
            and (
                site_announcements[name].timestamp
                + timedelta(seconds=site_announcements[name].grace_seconds)
            )
            >= last_published
        ):
            # already announced after last published
            _logger.info("Announcer %s is up-to-date", name)
            continue

        task = asyncio.create_task(announce_site(name, announcer, site_announcements))
        tasks.append(task)

    # announce posts
    modified_post_announcements: Dict[Path, Dict[str, Announcement]] = {}
    announcers = get_announcers(root, config, Scope.POST)
    for post in get_posts(root, config):
        path = post.path.parent / ANNOUNCEMENTS_FILENAME
        post_announcements = load_yaml(path, Announcement)
        post_announcers = {
            name: announcers[name]
            for name in post.announcers
            if name in announcers and name not in post_announcements
        }
        for name, announcer in post_announcers.items():
            task = asyncio.create_task(
                announce_post(name, announcer, post, post_announcements),
            )
            tasks.append(task)

        # store new announcements to persist later
        if post_announcers:
            modified_post_announcements[post.path] = post_announcements

    await asyncio.gather(*tasks)

    # persist new announcements
    tasks = []
    task = asyncio.create_task(save_announcements(root, site_announcements))
    for post_path, announcements in modified_post_announcements.items():
        task = asyncio.create_task(save_announcements(post_path.parent, announcements))
        tasks.append(task)

    await asyncio.gather(*tasks)
