"""
Tests for ``nefelibata.builders.gemini``.
"""
# pylint: disable=invalid-name
from pathlib import Path

import pytest
from freezegun import freeze_time
from pytest_mock import MockerFixture

from nefelibata.builders.gemini import GeminiBuilder
from nefelibata.post import Post
from nefelibata.typing import Config


@pytest.mark.asyncio
async def test_builder_create_directory(root: Path, config: Config) -> None:
    """
    Test that the build directory is created.
    """
    build_directory = root / "build/gemini"
    assert not build_directory.exists()
    GeminiBuilder(root, config)
    assert build_directory.exists()

    # on the second call the directory should be unmodified
    last_update = build_directory.stat().st_mtime
    GeminiBuilder(root, config)
    assert build_directory.stat().st_mtime == last_update


@pytest.mark.asyncio
async def test_builder_post(
    mocker: MockerFixture,
    root: Path,
    config: Config,
    post: Post,
) -> None:
    """
    Test ``process_post``.
    """
    _logger = mocker.patch("nefelibata.builders.gemini._logger")

    builder = GeminiBuilder(root, config)
    with freeze_time("2021-01-02T00:00:00Z"):
        await builder.process_post(post)

    post_path = root / "build/gemini/first/index.gmi"

    # test that file was created
    assert post_path.exists()
    _logger.info.assert_called_with("Creating Gemini post")
    with open(post_path, encoding="utf-8") as input_:
        content = input_.read()
    assert (
        content
        == """# Welcome

This is your first post. It should be written using Markdown.

Read more about Nefelibata[1].

=> https://nefelibata.readthedocs.io/ 1: https://nefelibata.readthedocs.io/"""
    )

    # call again, test that file is up-to-date
    _logger.reset_mock()
    last_update = post_path.stat().st_mtime
    with freeze_time("2021-01-03T00:00:00Z"):
        await builder.process_post(post)
    assert post_path.stat().st_mtime == last_update
    _logger.info.assert_called_with("Post %s is up-to-date, nothing to do", post_path)

    # call again, forcing a rebuild
    _logger.reset_mock()
    last_update = post_path.stat().st_mtime
    with freeze_time("2021-01-04T00:00:00Z"):
        await builder.process_post(post, force=True)
    assert post_path.stat().st_mtime > last_update
    _logger.info.assert_called_with("Creating Gemini post")


@pytest.mark.asyncio
async def test_builder_site(
    mocker: MockerFixture,
    root: Path,
    config: Config,
    post: Post,
) -> None:
    """
    Test ``process_site``.
    """
    _logger = mocker.patch("nefelibata.builders.gemini._logger")
    env = mocker.patch("nefelibata.builders.gemini.Environment")
    env.return_value.get_template.return_value.render.return_value = """
# 道&c.: Musings about the path and other things

    This is the Gemini capsule of Beto Dealmeida.

    => https://taoetc.org/ Website
    => mailto://roberto@dealmeida.net Email address

    ## Posts
""".strip()
    mocker.patch("nefelibata.builders.gemini.get_posts", return_value=[post])

    builder = GeminiBuilder(root, config)
    with freeze_time("2021-01-02T00:00:00Z"):
        await builder.process_site()

    index_path = root / "build/gemini/index.gmi"

    # test that file was created
    assert index_path.exists()
    _logger.info.assert_called_with("Creating Gemini index")
    with open(index_path, encoding="utf-8") as input_:
        content = input_.read()
    assert (
        content
        == """# 道&c.: Musings about the path and other things

    This is the Gemini capsule of Beto Dealmeida.

    => https://taoetc.org/ Website
    => mailto://roberto@dealmeida.net Email address

    ## Posts

=> first/index.gmi 2020-12-31 16:00:00-08:00 — This is your first post"""
    )

    # call again, test that file is up-to-date
    _logger.reset_mock()
    last_update = index_path.stat().st_mtime
    with freeze_time("2021-01-03T00:00:00Z"):
        await builder.process_site()
    assert index_path.stat().st_mtime == last_update
    _logger.info.assert_called_with("Gemini index is up-to-date, nothing to do")

    # call again, forcing a rebuild
    _logger.reset_mock()
    last_update = index_path.stat().st_mtime
    with freeze_time("2021-01-04T00:00:00Z"):
        await builder.process_site(force=True)
    assert index_path.stat().st_mtime > last_update
    _logger.info.assert_called_with("Creating Gemini index")
