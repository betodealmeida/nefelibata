# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import timezone
from pathlib import Path

import pytest
from dateutil.parser._parser import ParserError
from freezegun import freeze_time
from nefelibata.post import get_posts
from nefelibata.post import Post

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


def test_post(mock_post):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: This is your first post
        keywords: welcome, blog
        summary: Hello, world!

        # Welcome #

        This is your first post. It should be written using Markdown.
        """,
        )

    assert post.title == "This is your first post"
    assert post.summary == "Hello, world!"
    assert post.date.astimezone(timezone.utc) == datetime(
        2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc,
    )
    assert post.url == "first/index.html"
    assert post.up_to_date is False


def test_post_no_summary(mock_post):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: This is your first post
        keywords: welcome, blog
        summary:

        # Welcome #

        This is your first post. It should be written using Markdown.
        """,
        )

    # uses first paragraph
    assert (
        post.summary == "This is your first post. It should be written using Markdown."
    )


def test_post_no_summary_truncated(mock_post):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: This is your first post
        keywords: welcome, blog
        summary:

        # Welcome #

        This is your first post. It should be written using Markdown. The first paragraph
        is very long — indeed, it's longer than 140 characters. Which is what a Tweet used
        to be, but notw it's 280.
        """,
        )

    # uses first paragraph
    assert (
        post.summary
        == "This is your first post. It should be written using Markdown. The first paragraph is very long — indeed, it's longer than 140 characters. W\u2026"
    )


def test_post_no_summary_no_html(mock_post):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: This is your first post
        keywords: welcome, blog
        summary:

        # $Witticism #
        """,
        )

    # uses first paragraph
    assert post.summary == "No summary."


def test_post_with_date(mock_post):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: This is your first post
        keywords: welcome, blog
        summary: Hello, world!
        date: Wed, 1 Jan 2020 12:00:00 -0800

        # $Witticism #
        """,
        )

    assert post.date.astimezone(timezone.utc) == datetime(
        2020, 1, 1, 20, 0, 0, tzinfo=timezone.utc,
    )


def test_post_without_date(mock_post):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: This is your first post
        keywords: welcome, blog
        summary: Hello, world!

        # $Witticism #
        """,
        )

    del post.parsed["date"]
    with pytest.raises(Exception):
        post.date


def test_post_subject_from_h1(mock_post):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject:
        keywords: welcome, blog
        summary: Hello, world!

        # $Witticism #
        """,
        )

    assert post.title == "$Witticism"


def test_post_subject_from_filename(mock_post):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject:
        keywords: welcome, blog
        summary: Hello, world!

        Just a one-line witticism.
        """,
        )

    assert post.title == "first"


def test_get_posts(fs):
    root = Path("/path/to/blog")
    fs.create_dir(root / "/posts")
    fs.create_dir(root / "posts/one")
    fs.create_dir(root / "posts/two")

    fs.create_file(root / "posts/one/index.mkd")
    fs.create_file(root / "posts/two/index.mkd")

    posts = get_posts(root)
    assert len(posts) == 2
    assert posts[0].file_path == Path(root / "posts/one/index.mkd")
    assert posts[1].file_path == Path(root / "posts/two/index.mkd")
