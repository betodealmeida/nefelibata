"""
Test ``nefelibata.cli.publish``.
"""
# pylint: disable=unused-argument

from datetime import datetime
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from nefelibata.announcers.base import Announcement
from nefelibata.cli import publish
from nefelibata.config import Config
from nefelibata.post import Post
from nefelibata.publishers.base import Publishing


@pytest.mark.asyncio
async def test_run(
    mocker: MockerFixture,
    root: Path,
    config: Config,
    post: Post,
) -> None:
    """
    Test ``publish``.
    """
    publisher = mocker.MagicMock()
    publisher.publish = mocker.AsyncMock(
        side_effect=[
            Publishing(timestamp=datetime(2021, 1, 1)),
            None,
            Publishing(timestamp=datetime(2021, 1, 3)),
        ],
    )

    announcer = mocker.MagicMock()
    announcer.announce_post = mocker.AsyncMock(
        side_effect=[
            None,
            Announcement(
                url="https://host1.example.com/",
                timestamp=datetime(2021, 1, 1),
            ),
        ],
    )
    announcer.announce_site = mocker.AsyncMock(
        side_effect=[
            Announcement(
                url="https://host2.example.com/",
                timestamp=datetime(2021, 1, 2),
            ),
            None,
        ],
    )

    mocker.patch(
        "nefelibata.cli.publish.get_announcers",
        return_value={"announcer": announcer},
    )
    mocker.patch(
        "nefelibata.cli.publish.get_publishers",
        return_value={"publisher": publisher},
    )

    # On the first publish we should announce site and post.
    await publish.run(root)
    publisher.publish.assert_called_with(None, False)
    announcer.announce_site.assert_called_with()
    announcer.announce_post.assert_called()

    # Publish again, should have a ``since`` value. Because ``publish``
    # returns ``None`` the second time we shouldn't announce the site.
    # And because the first time ``publish_post`` returned ``None``,
    # it should try again now and be called.
    announcer.announce_site.reset_mock()
    announcer.announce_post.reset_mock()
    await publish.run(root)
    publisher.publish.assert_called_with(datetime(2021, 1, 1), False)
    announcer.announce_site.assert_not_called()
    announcer.announce_post.assert_called()

    # Publish again. This time ``publish`` returns a new data, so we
    # expect to call ``publish_site``. Because the post was already
    # published last time it shouldn't be announced this time.
    announcer.announce_post.reset_mock()
    await publish.run(root)
    publisher.publish.assert_called_with(datetime(2021, 1, 1), False)
    announcer.announce_site.assert_called_with()
    announcer.announce_post.assert_not_called()
