from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any
from typing import Dict

import pytest
from freezegun import freeze_time
from nefelibata.builders.post import jinja2_formatdate
from nefelibata.builders.post import PostBuilder
from nefelibata.post import Post

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


test_template = """
{{ post.title }}
"""

test_post = """
subject: A test
summary: An initial test
keywords: foo, bar

Hello!
""".strip()

config: Dict[str, Any] = {
    "url": "https://example.com/",
    "language": "en",
    "theme": "test-theme",
    "webmention": {"endpoint": "https://webmention.io/example.com/webmention"},
}


def test_process_post(mock_post, fs):
    root = Path("/path/to/blog")

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

    with open(post.file_path.parent / "test.json", "w") as fp:
        fp.write("{}")

    builder = PostBuilder(root, config)
    builder.process_post(post)

    assert (post.file_path.with_suffix(".html")).exists()

    with open(post.file_path.with_suffix(".html")) as fp:
        contents = fp.read()
    assert (
        contents
        == """
<!DOCTYPE html><html lang="en">
<head>
<meta content="article" property="og:type"/>
<meta content="Post title" property="og:title"/>
<meta content="This is the post description" property="og:description"/>
<link href="https://webmention.io/example.com/webmention" rel="webmention" />
<link href="https://external.example.com/css/basic.css" rel="stylesheet">
<link href="/css/style.css" rel="stylesheet">

</head>
<body>
<h1>Welcome</h1>
<p>This is your first post. It should be written using Markdown.</p>
</body>
</html>"""
    )


def test_process_post_up_to_date(mock_post, fs):
    root = Path("/path/to/blog")

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

    with freeze_time("2020-01-02T00:00:00Z"):
        fs.create_file(post.file_path.with_suffix(".html"))

    builder = PostBuilder(root, config)
    with freeze_time("2020-01-03T00:00:00Z"):
        builder.process_post(post)

    assert datetime.fromtimestamp(
        post.file_path.with_suffix(".html").stat().st_mtime,
    ).astimezone(timezone.utc) == datetime(2020, 1, 2, 0, 0, tzinfo=timezone.utc)


def test_jinja2_formatdate_string():
    assert (
        jinja2_formatdate("2020-01-01T00:00:00Z", "%Y-%m-%dT%H:%M:%S%z")
        == "2020-01-01T00:00:00+0000"
    )


def test_jinja2_formatdate_float():
    assert (
        jinja2_formatdate(1577836800.0, "%Y-%m-%dT%H:%M:%S%z")
        == "2020-01-01T00:00:00+0000"
    )


def test_jinja2_formatdate_datetime():
    assert (
        jinja2_formatdate(
            datetime(2020, 1, 1, tzinfo=timezone.utc), "%Y-%m-%dT%H:%M:%S%z",
        )
        == "2020-01-01T00:00:00+0000"
    )


def test_jinja2_formatdate_invalid_string():
    assert jinja2_formatdate("1 de Abril", "%Y-%m-%dT%H:%M:%S%z") == "Unknown timestamp"
