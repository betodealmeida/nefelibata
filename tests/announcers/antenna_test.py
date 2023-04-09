"""
Tests for ``nefelibata.announcers.antenna``.
"""
# pylint: disable=invalid-name

import ssl
from datetime import datetime, timezone
from pathlib import Path

import pytest
from freezegun import freeze_time
from pytest_mock import MockerFixture
from yarl import URL

from nefelibata.announcers.antenna import AntennaAnnouncer
from nefelibata.announcers.base import Interaction
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

    Client = mocker.patch("nefelibata.announcers.gemlog.Client")
    Client.return_value.get = mocker.AsyncMock()

    announcer = AntennaAnnouncer(root, config, builders=[gemini_builder])

    # post announcement is no-op
    announcement = await announcer.announce_post(post)
    assert announcement is None

    with freeze_time("2021-01-01T00:00:00Z"):
        announcement = await announcer.announce_site()
    assert announcement.dict() == {
        "url": "gemini://warmedal.se/~antenna/",
        "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
        "grace_seconds": 0,
    }
    assert Client.return_value.get.called_with(
        URL("gemini://warmedal.se/~antenna/submit?gemini://example.com/feed"),
    )

    announcer = AntennaAnnouncer(root, config, builders=[html_builder])
    with pytest.raises(Exception) as excinfo:
        await announcer.announce_site()
    assert str(excinfo.value) == "Antenna announcer only works with `gemini://` builds"


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
    builder = Builder(root, config, "gemini://example.com/", "gemini")

    Client = mocker.patch("nefelibata.announcers.gemlog.Client")
    Client.return_value.get = mocker.AsyncMock()
    Client.return_value.get.return_value.read.side_effect = [
        b"""
=> gemini://example.com/reply.gmi Re: This is your first post
    """,
        b"""
=> gemini://example.com/first/index.gmi
    """,
    ]

    announcer = AntennaAnnouncer(root, config, builders=[builder])

    # post collect is no-op
    interactions = await announcer.collect_post(post)
    assert interactions == {}

    interactions = await announcer.collect_site()
    assert interactions == {
        Path("/path/to/blog/posts/first/index.mkd"): {
            "reply,gemini://example.com/reply.gmi": Interaction(
                id="reply,gemini://example.com/reply.gmi",
                name="Re: This is your first post",
                url="gemini://example.com/reply.gmi",
                type="reply",
                timestamp=None,
            ),
        },
    }

    # test no backlink
    Client.return_value.get.return_value.read.side_effect = [
        b"""
=> gemini://example.com/reply.gmi Re: This is your first post
    """,
        b"",
    ]

    announcer = AntennaAnnouncer(root, config, builders=[builder])

    interactions = await announcer.collect_site()
    assert interactions == {}

    # test SSL error
    response = mocker.AsyncMock()
    response.read.return_value = b"""
=> gemini://example.com/reply.gmi Re: This is your first post
    """
    Client.return_value.get.side_effect = [
        response,
        ssl.SSLCertVerificationError("A wild error appears!"),
    ]

    announcer = AntennaAnnouncer(root, config, builders=[builder])

    interactions = await announcer.collect_site()
    assert interactions == {
        Path("/path/to/blog/posts/first/index.mkd"): {
            "reply,gemini://example.com/reply.gmi": Interaction(
                id="reply,gemini://example.com/reply.gmi",
                name="Re: This is your first post",
                url="gemini://example.com/reply.gmi",
                type="reply",
                timestamp=None,
            ),
        },
    }
