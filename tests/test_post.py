"""
Tests for ``nefelibata.post``.
"""
# pylint: disable=invalid-name, unused-argument

from datetime import datetime, timezone
from pathlib import Path

import pytest
from freezegun import freeze_time
from pyfakefs.fake_filesystem import FakeFilesystem
from yarl import URL

from nefelibata.config import AnnouncerModel, Config
from nefelibata.post import Post, build_post, extract_links, get_posts

from .fakes import POST_CONTENT, POST_DATA


@pytest.mark.asyncio
async def test_post() -> None:
    """
    Test the ``Post`` model.
    """
    post = Post(**POST_DATA)

    assert post.path == Path("/path/to/blog/posts/first/index.mkd")
    assert post.title == "This is your first post"
    assert post.timestamp == datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc)
    assert post.metadata == {
        "keywords": "welcome, blog",
        "summary": "Hello, world!",
    }
    assert post.tags == {"welcome", "blog"}
    assert post.categories == {"stem"}
    assert post.type == "post"
    assert post.url == "first/index"
    assert (
        post.content
        == """# Welcome #

This is your first post. It should be written using Markdown.

Read more about [Nefelibata](https://nefelibata.readthedocs.io/)."""
    )


@pytest.mark.asyncio
async def test_build_post(fs: FakeFilesystem, root: Path, config: Config) -> None:
    """
    Test ``build_post``.
    """
    path = Path(root / "posts/first/index.mkd")

    # create post
    with freeze_time("2021-01-01T00:00:00Z"):
        fs.create_file(path, contents=POST_CONTENT)

    config.announcers = {"antenna": AnnouncerModel(plugin="antenna")}

    post = build_post(root, config, path)

    assert post.path == path
    assert post.title == "This is your first post"
    assert post.timestamp == datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc)
    assert post.metadata == {
        "keywords": "welcome, blog",
        "summary": "Hello, world!",
    }
    assert post.tags == {"welcome", "blog"}
    assert post.categories == {"stem"}
    assert post.type == "post"
    assert post.url == "first/index"
    assert (
        post.content
        == """# Welcome #

This is your first post. It should be written using Markdown.

Read more about [Nefelibata](https://nefelibata.readthedocs.io/)."""
    )
    assert post.announcers == {"antenna"}

    # check to file was updated with the ``date`` header
    with open(path, encoding="utf-8") as input_:
        content = input_.read()
    assert (
        content
        == """subject: This is your first post
keywords: welcome, blog
summary: Hello, world!
date: Thu, 31 Dec 2020 16:00:00 -0800
announce-on: antenna

# Welcome #

This is your first post. It should be written using Markdown.

Read more about [Nefelibata](https://nefelibata.readthedocs.io/)."""
    )

    # build again, and test that the file wasn't modified since it
    # already has all the required headers
    last_update = path.stat().st_mtime
    build_post(root, config, path)
    assert path.stat().st_mtime == last_update


@pytest.mark.asyncio
async def test_get_posts(fs: FakeFilesystem, root: Path, config: Config) -> None:
    """
    Test ``get_posts``.
    """
    with freeze_time("2021-01-01T00:00:00Z"):
        fs.create_dir(root / "posts/one")
        fs.create_file(root / "posts/one/index.mkd")
    with freeze_time("2021-01-02T00:00:00Z"):
        fs.create_dir(root / "posts/two")
        fs.create_file(root / "posts/two/index.mkd")

    posts = get_posts(root, config)
    assert len(posts) == 2
    assert posts[0].path == Path(root / "posts/two/index.mkd")
    assert posts[1].path == Path(root / "posts/one/index.mkd")

    # test limited number of posts returned
    posts = get_posts(root, config, 1)
    assert len(posts) == 1


def test_extract_links(post: Post) -> None:
    """
    Test ``extract_links``.
    """
    assert list(extract_links(post)) == [URL("https://nefelibata.readthedocs.io/")]

    post.metadata["test-url"] = "https://example.com/"
    assert list(extract_links(post)) == [
        URL("https://example.com/"),
        URL("https://nefelibata.readthedocs.io/"),
    ]
