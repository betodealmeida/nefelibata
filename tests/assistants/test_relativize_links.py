from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any
from typing import Dict
from unittest import mock

from freezegun import freeze_time
from nefelibata.assistants.relativize_links import RelativizeLinksAssistant
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
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!

        <a id="4-links">Four links</a>:

        - [Atom feed](https://example.com/atom.xml)
        - [An image](img/sample.jpg)
        - [My favorite mp3](file.mp3)
        - [My favorite CSS](/css/style.css)
        """,
        )
    PostBuilder(root, config).process_post(post)

    assistant = RelativizeLinksAssistant(root, config)
    assistant.process_post(post)

    with open(post.file_path.with_suffix(".html")) as fp:
        html = fp.read()

    assert (
        html
        == """
<!DOCTYPE html>
<html lang="en">
<head>
<meta content="article" property="og:type"/>
<meta content="Post title" property="og:title"/>
<meta content="This is the post description" property="og:description"/>
<link href="https://webmention.io/example.com/webmention" rel="webmention"/>
<link href="https://external.example.com/css/basic.css" rel="stylesheet"/>
<link href="../css/style.css" rel="stylesheet"/>
</head>
<body>
<p>Hi, there!</p>
<p><a id="4-links">Four links</a>:</p>
<ul>
<li><a href="../atom.xml">Atom feed</a></li>
<li><a href="img/sample.jpg">An image</a></li>
<li><a href="file.mp3">My favorite mp3</a></li>
<li><a href="../css/style.css">My favorite CSS</a></li>
</ul>
</body>
</html>"""
    )


def test_process_post_no_modification(mock_post):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!

        <a id="4-links">Four links</a>:

        - [Atom feed](https://example.com/atom.xml)
        - [An image](img/sample.jpg)
        - [My favorite mp3](file.mp3)
        - [My favorite CSS](/css/style.css)
        """,
        )
        PostBuilder(root, config).process_post(post)

    assistant = RelativizeLinksAssistant(root, config)

    with freeze_time("2020-01-02T00:00:00Z"):
        assistant.process_post(post)
    with freeze_time("2020-01-03T00:00:00Z"):
        assistant.process_post(post)

    assert datetime.fromtimestamp(
        post.file_path.with_suffix(".html").stat().st_mtime,
    ).astimezone(timezone.utc) == datetime(2020, 1, 2, 0, 0, tzinfo=timezone.utc)


def test_process_site(fs):
    root = Path("/path/to/blog")

    fs.create_dir(root / "build")
    with open(root / "build/test.html", "w") as fp:
        fp.write('<img src="/img/background.jpg" />')

    assistant = RelativizeLinksAssistant(root, config)
    assistant.process_site()

    with open(root / "build/test.html") as fp:
        html = fp.read()

    assert html == '<img src="img/background.jpg"/>'
