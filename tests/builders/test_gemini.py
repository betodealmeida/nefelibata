"""
Tests for ``nefelibata.builders.gemini``.
"""
# pylint: disable=invalid-name
from pathlib import Path
from typing import Any, Dict

import pytest
from freezegun import freeze_time
from pytest_mock import MockerFixture

from nefelibata.builders.gemini import GeminiBuilder
from nefelibata.post import Post
from nefelibata.typing import Config


@pytest.mark.asyncio
async def test_builder_setup(root: Path, config: Config) -> None:
    """
    Test that templates and build directory are created.
    """
    template_directory = root / "templates/builders/gemini"
    build_directory = root / "build/gemini"
    assert not template_directory.exists()
    assert not build_directory.exists()

    GeminiBuilder(root, config, "gemini://localhost:1965")
    last_update: Dict[Any, Any] = {}
    assert template_directory.exists()
    for file in ("index.gmi", "feed.gmi", "post.gmi"):
        assert (template_directory / file).exists()
        last_update[file] = (template_directory / file).stat().st_mtime
    assert build_directory.exists()
    last_update[build_directory] = build_directory.stat().st_mtime

    # on the second call the files and directories should be unmodified
    GeminiBuilder(root, config, "gemini://localhost:1965")
    for file in ("index.gmi", "feed.gmi", "post.gmi"):
        assert (template_directory / file).stat().st_mtime == last_update[file]
    assert build_directory.stat().st_mtime == last_update[build_directory]


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

    builder = GeminiBuilder(root, config, "gemini://localhost:1965")
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

=> https://nefelibata.readthedocs.io/ 1: https://nefelibata.readthedocs.io/

# About

Published on 2020-12-31 16:00:00-08:00 by Beto Dealmeida <roberto@dealmeida.net>.

=> gemini://localhost:1965 Go back to the main index"""
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
    mocker.patch("nefelibata.builders.gemini.get_posts", return_value=[post])

    config["social"] = [{"title": "Mastodon", "url": "https://2c.taoetc.org/@beto"}]
    builder = GeminiBuilder(root, config, "gemini://localhost:1965")
    with freeze_time("2021-01-02T00:00:00Z"):
        await builder.process_site()

    assets_directory = root / "build/gemini"
    assets = ("index.gmi", "feed.gmi")

    # test that files were created
    last_update: Dict[Any, Any] = {}
    for asset in assets:
        assert (assets_directory / asset).exists()
        last_update[asset] = (assets_directory / asset).stat().st_mtime
    _logger.info.assert_has_calls(
        [
            mocker.call("Creating %s", "index.gmi"),
            mocker.call("Creating %s", "feed.gmi"),
        ],
    )
    with open(assets_directory / "index.gmi", encoding="utf-8") as input_:
        content = input_.read()
    assert (
        content
        == """# 道&c.: Musings about the path and other things

This is the Gemini capsule of Beto Dealmeida.

=> https://taoetc.org/ Website
=> mailto://roberto@dealmeida.net Email address
=> feed.gmi Gemlog

## Posts

=> first/index.gmi 2020-12-31 16:00:00-08:00 — This is your first post

## Links

=> https://2c.taoetc.org/@beto Mastodon

Crafted with ❤️  using Nefelibata

=> https://nefelibata.readthedocs.io/ Nefelibata"""
    )
    with open(assets_directory / "feed.gmi", encoding="utf-8") as input_:
        content = input_.read()
    assert (
        content
        == """# 道&c.: Musings about the path and other things

## Beto Dealmeida's gemlog

=> first/index.gmi 2020-12-31 — This is your first post"""
    )

    # call again, test that file is up-to-date
    _logger.reset_mock()
    with freeze_time("2021-01-03T00:00:00Z"):
        await builder.process_site()
    for asset in assets:
        assert (assets_directory / asset).stat().st_mtime == last_update[asset]
    _logger.info.assert_has_calls(
        [
            mocker.call("File %s is up-to-date, nothing to do", "index.gmi"),
            mocker.call("File %s is up-to-date, nothing to do", "feed.gmi"),
        ],
    )

    # call again, forcing a rebuild
    _logger.reset_mock()
    with freeze_time("2021-01-04T00:00:00Z"):
        await builder.process_site(force=True)
    for asset in assets:
        assert (assets_directory / asset).stat().st_mtime > last_update[asset]
    _logger.info.assert_has_calls(
        [
            mocker.call("Creating %s", "index.gmi"),
            mocker.call("Creating %s", "feed.gmi"),
        ],
    )
