from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any
from typing import Dict
from unittest import mock

from freezegun import freeze_time
from nefelibata.assistants.reading_time import ReadingTimeAssistant
from nefelibata.builders.post import PostBuilder

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


config: Dict[str, Any] = {
    "url": "https://example.com/",
    "language": "en",
    "theme": "test-theme",
    "webmention": {"endpoint": "https://webmention.io/example.com/webmention"},
}


def test_process_post(mock_post):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        lorem_ipsum = ("lorem ipsum " * 1000).strip()
        post = mock_post(
            f"""
        subject: Hello, World!
        keywords: test
        summary: My first post

        <p id="post-reading-time"></p>

        {lorem_ipsum}
        """,
        )
    PostBuilder(root, config).process_post(post)

    assistant = ReadingTimeAssistant(root, config)
    assistant.process_post(post)

    with open(post.file_path.with_suffix(".html")) as fp:
        html = fp.read()

    assert (
        html
        == f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta content="article" property="og:type"/>
<meta content="Post title" property="og:title"/>
<meta content="This is the post description" property="og:description"/>
<link href="https://webmention.io/example.com/webmention" rel="webmention"/>
<link href="https://external.example.com/css/basic.css" rel="stylesheet"/>
<link href="/css/style.css" rel="stylesheet"/>
</head>
<body>
<p id="post-reading-time"><span>Approximate reading time: 8 minutes</span></p>
<p>{lorem_ipsum}</p>
</body>
</html>"""
    )

    # test idempotency
    previous = html
    assistant.process_post(post)
    with open(post.file_path.with_suffix(".html")) as fp:
        html = fp.read()

    assert html == previous


def test_process_post_too_short(mock_post):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            f"""
        subject: Hello, World!
        keywords: test
        summary: My first post

        <p id="post-reading-time"></p>

        Hello!
        """,
        )
    PostBuilder(root, config).process_post(post)

    assistant = ReadingTimeAssistant(root, config)
    assistant.process_post(post)

    with open(post.file_path.with_suffix(".html")) as fp:
        html = fp.read()

    print(html)
    assert (
        html
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
<p id="post-reading-time"></p>

<p>Hello!</p>
</body>
</html>"""
    )


def test_process_post_no_element(mock_post):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        lorem_ipsum = ("lorem ipsum " * 1000).strip()
        post = mock_post(
            f"""
        subject: Hello, World!
        keywords: test
        summary: My first post

        {lorem_ipsum}
        """,
        )
    PostBuilder(root, config).process_post(post)

    assistant = ReadingTimeAssistant(root, config)
    assistant.process_post(post)

    with open(post.file_path.with_suffix(".html")) as fp:
        html = fp.read()

    assert (
        html
        == f"""
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
<p>{lorem_ipsum}</p>
</body>
</html>"""
    )
