"""
Tests for ``nefelibata.announcers.campcom``.
"""
# pylint: disable=invalid-name

from datetime import datetime, timezone
from pathlib import Path

import pytest
from freezegun import freeze_time
from pytest_mock import MockerFixture
from yarl import URL

from nefelibata.announcers.base import Interaction
from nefelibata.announcers.geminispace import GeminispaceAnnouncer
from nefelibata.builders.base import Builder
from nefelibata.config import Config
from nefelibata.post import Post


@pytest.mark.asyncio
async def test_announcer_announce(
    mocker: MockerFixture,
    root: Path,
    config: Config,
    post: Post,
) -> None:
    """
    Test announcing sites and posts.
    """
    gemini_builder = Builder(root, config, "gemini://example.com/", "gemini")
    html_builder = Builder(root, config, "https://example.com/", "www")

    Client = mocker.patch("nefelibata.announcers.geminispace.Client")
    Client.return_value.get = mocker.AsyncMock()

    announcer = GeminispaceAnnouncer(root, config, builders=[gemini_builder])

    # post announcement is no-op
    announcement = await announcer.announce_post(post)
    assert announcement is None

    with freeze_time("2021-01-01T00:00:00Z"):
        announcement = await announcer.announce_site()
    assert announcement.dict() == {
        "url": "gemini://geminispace.info/",
        "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
        "grace_seconds": 31536000,
    }
    assert Client.return_value.get.called_with(
        URL("gemini://geminipace.info/add-seed?gemini://example.com/feed"),
    )

    announcer = GeminispaceAnnouncer(root, config, builders=[html_builder])
    with pytest.raises(Exception) as excinfo:
        await announcer.announce_site()
    assert (
        str(excinfo.value) == "Geminispace announcer only works with `gemini://` builds"
    )


@pytest.mark.asyncio
async def test_announcer_collect(
    mocker: MockerFixture,
    root: Path,
    config: Config,
    post: Post,
) -> None:
    """
    Test collecting interactions on posts and sites.
    """
    gemini_builder = Builder(root, config, "gemini://example.com/", "gemini")
    html_builder = Builder(root, config, "https://example.com/", "www")

    Client = mocker.patch("nefelibata.announcers.geminispace.Client")
    Client.return_value.get = mocker.AsyncMock()
    Client.return_value.get.return_value.read.return_value = b"""
### 3 cross-capsule backlinks

=> gemini://example.com/reply.gmi Re: This is your first post
=> gemini://example.com/another-reply.gmi Re: This is your first post
    """

    announcer = GeminispaceAnnouncer(root, config, builders=[gemini_builder])

    # site collect is no-op
    interactions = await announcer.collect_site()
    assert interactions == {}

    interactions = await announcer.collect_post(post)
    assert interactions == {
        "backlink,gemini://example.com/reply.gmi": Interaction(
            id="backlink,gemini://example.com/reply.gmi",
            name="Re: This is your first post",
            url="gemini://example.com/reply.gmi",
            type="backlink",
            timestamp=None,
        ),
        "backlink,gemini://example.com/another-reply.gmi": Interaction(
            id="backlink,gemini://example.com/another-reply.gmi",
            name="Re: This is your first post",
            url="gemini://example.com/another-reply.gmi",
            type="backlink",
            timestamp=None,
        ),
    }

    announcer = GeminispaceAnnouncer(root, config, builders=[html_builder])
    with pytest.raises(Exception) as excinfo:
        await announcer.collect_post(post)
    assert (
        str(excinfo.value) == "Geminispace announcer only works with `gemini://` builds"
    )
