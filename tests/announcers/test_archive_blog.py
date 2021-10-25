"""
Tests for ``nefelibata.announcers.archive_blog``.
"""

from datetime import datetime, timezone
from pathlib import Path

import pytest
from freezegun import freeze_time
from pytest_mock import MockerFixture
from yarl import URL

from nefelibata.announcers.archive_blog import ArchiveBlogAnnouncer
from nefelibata.announcers.base import Announcement
from nefelibata.builders.base import Builder
from nefelibata.config import Config
from nefelibata.post import Post


@pytest.mark.asyncio
async def test_announcer_announce_post(
    mocker: MockerFixture,
    root: Path,
    config: Config,
    post: Post,
) -> None:
    """
    Test the announcer saving a post.
    """
    gemini_builder = Builder(root, config, "gemini://example.com/", "gemini")
    gemini_builder.extension = ".gmi"
    html_builder = Builder(root, config, "https://example.com/", "www")
    html_builder.extension = ".html"

    mocker.patch(
        "nefelibata.announcers.archive_blog.archive_urls",
        return_value={},
    )

    announcer = ArchiveBlogAnnouncer(
        root,
        config,
        builders=[gemini_builder, html_builder],
    )

    announcement = await announcer.announce_post(post)
    assert announcement is None

    archive_urls = mocker.patch(
        "nefelibata.announcers.archive_blog.archive_urls",
        return_value={
            URL("https://nefelibata.readthedocs.io/"): URL(
                "https://web.archive.org/web/20211003154602/https://nefelibata.readthedocs.io/",
            ),
        },
    )

    with freeze_time("2021-01-01T00:00:00Z"):
        announcement = await announcer.announce_post(post)
    assert announcement == Announcement(
        url="https://web.archive.org/save/",
        timestamp=datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
        grace_seconds=0,
    )

    archive_urls.assert_called_with(
        [
            URL("gemini://example.com/first/index.gmi"),
            URL("https://example.com/first/index.html"),
        ],
    )


@pytest.mark.asyncio
async def test_announcer_announce_site(
    mocker: MockerFixture,
    root: Path,
    config: Config,
) -> None:
    """
    Test the announcer saving a blog.
    """
    gemini_builder = Builder(root, config, "gemini://example.com/", "gemini")
    gemini_builder.extension = ".gmi"
    html_builder = Builder(root, config, "https://example.com/", "www")
    html_builder.extension = ".html"

    mocker.patch(
        "nefelibata.announcers.archive_blog.archive_urls",
        return_value={},
    )

    announcer = ArchiveBlogAnnouncer(
        root,
        config,
        builders=[gemini_builder, html_builder],
    )

    announcement = await announcer.announce_site()
    assert announcement is None

    archive_urls = mocker.patch(
        "nefelibata.announcers.archive_blog.archive_urls",
        return_value={
            URL("https://example.com/"): URL(
                "https://web.archive.org/web/20211003154602/https://example.com/",
            ),
        },
    )

    with freeze_time("2021-01-01T00:00:00Z"):
        announcement = await announcer.announce_site()
    assert announcement == Announcement(
        url="https://web.archive.org/save/",
        timestamp=datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
        grace_seconds=0,
    )

    archive_urls.assert_called_with(
        [
            URL("gemini://example.com/"),
            URL("https://example.com/"),
        ],
    )
