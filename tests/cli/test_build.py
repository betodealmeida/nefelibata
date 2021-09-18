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
    builder = mocker.MagicMock()
    builder.process_post = mocker.AsyncMock()
    builder.process_site = mocker.AsyncMock()

    mocker.patch("nefelibata.cli.build.get_config")
    mocker.patch("nefelibata.cli.build.get_posts", return_value=[post])
    mocker.patch("nefelibata.cli.build.get_builders", return_value={"builder": builder})

    _logger = mocker.patch("nefelibata.cli.build._logger")

    await build.run(root)

    builder.process_post.assert_called_with(post, False)
    builder.process_site.assert_called_with(False)
    _logger.info.assert_has_calls(
        [
            mocker.call("Creating `build/` directory"),
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
