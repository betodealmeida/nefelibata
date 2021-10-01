"""
Test ``nefelibata.cli.build``.
"""
# pylint: disable=invalid-name

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from nefelibata.cli import build
from nefelibata.post import Post


@pytest.mark.asyncio
async def test_run(
    mocker: MockerFixture,
    root: Path,
    post: Post,
) -> None:
    """
    Test ``run``.
    """
    assistant = mocker.MagicMock()
    assistant.process_post = mocker.AsyncMock()
    assistant.process_site = mocker.AsyncMock()

    builder = mocker.MagicMock()
    builder.process_post = mocker.AsyncMock()
    builder.process_site = mocker.AsyncMock()

    announcer1 = mocker.MagicMock()
    announcer1.collect_post = mocker.AsyncMock(return_value={})
    announcer1.collect_site = mocker.AsyncMock(return_value={})

    announcer2 = mocker.MagicMock()
    announcer2.collect_site = mocker.AsyncMock(return_value={})
    announcer2.collect_site.return_value = {}

    mocker.patch(
        "nefelibata.cli.build.get_announcers",
        return_value={"announcer1": announcer1, "announcer2": announcer2},
    )
    mocker.patch(
        "nefelibata.cli.build.get_assistants",
        return_value={"assistant": assistant},
    )
    mocker.patch("nefelibata.cli.build.get_builders", return_value={"builder": builder})
    mocker.patch("nefelibata.cli.build.get_config")
    mocker.patch("nefelibata.cli.build.get_posts", return_value=[post])

    _logger = mocker.patch("nefelibata.cli.build._logger")

    post.announcers = {"announcer1"}

    await build.run(root)

    assistant.process_post.assert_called_with(post, False)
    assistant.process_site.assert_called_with(False)
    builder.process_post.assert_called_with(post, False)
    builder.process_site.assert_called_with(False)
    announcer1.collect_post.assert_called_with(post)
    announcer1.collect_site.assert_called_with()
    announcer2.collect_post.assert_not_called()
    announcer2.collect_site.assert_called_with()
    _logger.info.assert_has_calls(
        [
            mocker.call("Building blog"),
            mocker.call("Creating `build/` directory"),
            mocker.call("Collecting interactions from posts"),
            mocker.call("Collecting interactions from site"),
            mocker.call("Running post assistants"),
            mocker.call("Running site assistants"),
            mocker.call("Processing posts"),
            mocker.call("Processing site"),
        ],
    )

    _logger.reset_mock()

    await build.run(root)
    _logger.info.assert_has_calls(
        [
            mocker.call("Processing posts"),
            mocker.call("Processing site"),
        ],
    )
