import json
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any
from typing import Dict
from unittest.mock import MagicMock
from unittest.mock import PropertyMock

from freezegun import freeze_time
from mutagen import id3
from nefelibata.assistants.twitter_card import TwitterCardAssistant
from nefelibata.builders.post import PostBuilder
from nefelibata.utils import modify_html

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self


config: Dict[str, Any] = {
    "url": "https://example.com/",
    "language": "en",
    "theme": "test-theme",
    "webmention": {"endpoint": "https://webmention.io/example.com/webmention"},
    "twitter": {"handle": "handle"},
}


def test_twitter_card(mock_post, requests_mock):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!
        """,
        )
    PostBuilder(root, config).process_post(post)

    assistant = TwitterCardAssistant(root, config)

    with freeze_time("2020-01-01T00:00:00Z"):
        assistant.process_post(post)

    with open(post.file_path.with_suffix(".html")) as fp:
        contents = fp.read()

    assert (
        contents
        == """
<!DOCTYPE html>
<html lang="en">
<head>
<meta content="article" property="og:type"/>
<meta content="Post title" property="og:title"/>
<meta content="This is the post description" property="og:description"/>
<link href="https://webmention.io/example.com/webmention" rel="webmention"/>
<link href="https://external.example.com/css/basic.css" rel="stylesheet"/>
<link href="/css/style.css" rel="stylesheet"/>
<meta content="summary" name="twitter:card"/><meta content="@handle" name="twitter:site"/><meta content="Post title" name="twitter:title"/><meta content="This is the post description" name="twitter:description"/></head>
<body>
<p>Hi, there!</p>
</body>
</html>"""
    )


def test_twitter_card_with_image(mock_post, mocker, fs, requests_mock):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!
        """,
        )
    PostBuilder(root, config).process_post(post)

    assistant = TwitterCardAssistant(root, config)

    fs.create_file(post.file_path.parent / "img/image1.jpg")
    fs.create_file(post.file_path.parent / "img/image2.jpg")

    mock_image = MagicMock()
    type(mock_image.open.return_value).size = PropertyMock(
        side_effect=[(10, 10), (1000, 1000)],
    )
    mocker.patch("nefelibata.assistants.twitter_card.Image", mock_image)

    with freeze_time("2020-01-01T00:00:00Z"):
        assistant.process_post(post)

    with open(post.file_path.with_suffix(".html")) as fp:
        contents = fp.read()

    assert (
        contents
        == """
<!DOCTYPE html>
<html lang="en">
<head>
<meta content="article" property="og:type"/>
<meta content="Post title" property="og:title"/>
<meta content="This is the post description" property="og:description"/>
<link href="https://webmention.io/example.com/webmention" rel="webmention"/>
<link href="https://external.example.com/css/basic.css" rel="stylesheet"/>
<link href="/css/style.css" rel="stylesheet"/>
<meta content="summary" name="twitter:card"/><meta content="@handle" name="twitter:site"/><meta content="Post title" name="twitter:title"/><meta content="This is the post description" name="twitter:description"/><meta content="https://example.com/first/img/image2.jpg" name="twitter:image"/></head>
<body>
<p>Hi, there!</p>
</body>
</html>"""
    )


def test_twitter_card_with_image_no_valid_size(mock_post, mocker, fs, requests_mock):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!
        """,
        )
    PostBuilder(root, config).process_post(post)

    assistant = TwitterCardAssistant(root, config)

    fs.create_file(post.file_path.parent / "img/image1.jpg")
    fs.create_file(post.file_path.parent / "img/image2.jpg")

    mock_image = MagicMock()
    type(mock_image.open.return_value).size = PropertyMock(
        side_effect=[(10, 10), (10, 10)],
    )
    mocker.patch("nefelibata.assistants.twitter_card.Image", mock_image)

    with freeze_time("2020-01-01T00:00:00Z"):
        assistant.process_post(post)

    with open(post.file_path.with_suffix(".html")) as fp:
        contents = fp.read()

    assert (
        contents
        == """
<!DOCTYPE html>
<html lang="en">
<head>
<meta content="article" property="og:type"/>
<meta content="Post title" property="og:title"/>
<meta content="This is the post description" property="og:description"/>
<link href="https://webmention.io/example.com/webmention" rel="webmention"/>
<link href="https://external.example.com/css/basic.css" rel="stylesheet"/>
<link href="/css/style.css" rel="stylesheet"/>
<meta content="summary" name="twitter:card"/><meta content="@handle" name="twitter:site"/><meta content="Post title" name="twitter:title"/><meta content="This is the post description" name="twitter:description"/></head>
<body>
<p>Hi, there!</p>
</body>
</html>"""
    )


def test_twitter_card_existing(mock_post, requests_mock):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!
        """,
        )
    PostBuilder(root, config).process_post(post)

    assistant = TwitterCardAssistant(root, config)

    with freeze_time("2020-01-01T00:00:00Z"):
        assistant.process_post(post)
    with freeze_time("2020-01-02T00:00:00Z"):
        assistant.process_post(post)

    assert datetime.fromtimestamp(
        post.file_path.with_suffix(".html").stat().st_mtime,
    ).astimezone(timezone.utc) == datetime(2020, 1, 1, 0, 0, tzinfo=timezone.utc)

    # modify and process again
    with modify_html(post.file_path.with_suffix(".html")) as soup:
        meta = soup.head.find("meta", {"property": "og:title"})
        meta.attrs["content"] = "This is a new title"

    with freeze_time("2020-01-03T00:00:00Z"):
        assistant.process_post(post)

    with open(post.file_path.with_suffix(".html")) as fp:
        contents = fp.read()

    assert (
        contents
        == """
<!DOCTYPE html>

<html lang="en">
<head>
<meta content="article" property="og:type"/>
<meta content="This is a new title" property="og:title"/>
<meta content="This is the post description" property="og:description"/>
<link href="https://webmention.io/example.com/webmention" rel="webmention"/>
<link href="https://external.example.com/css/basic.css" rel="stylesheet"/>
<link href="/css/style.css" rel="stylesheet"/>
<meta content="summary" name="twitter:card"/><meta content="@handle" name="twitter:site"/><meta content="This is the post description" name="twitter:description"/><meta content="This is a new title" name="twitter:title"/></head>
<body>
<p>Hi, there!</p>
</body>
</html>"""
    )


def test_twitter_card_no_og(mock_post, requests_mock):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!
        """,
        )
    PostBuilder(root, config).process_post(post)

    # remove meta tags with og information
    with modify_html(post.file_path.with_suffix(".html")) as soup:
        for meta in soup.head.find_all("meta"):
            meta.decompose()

    assistant = TwitterCardAssistant(root, config)

    with freeze_time("2020-01-01T00:00:00Z"):
        assistant.process_post(post)

    with open(post.file_path.with_suffix(".html")) as fp:
        contents = fp.read()

    assert (
        contents
        == """
<!DOCTYPE html>

<html lang="en">
<head>
<link href="https://webmention.io/example.com/webmention" rel="webmention"/>
<link href="https://external.example.com/css/basic.css" rel="stylesheet"/>
<link href="/css/style.css" rel="stylesheet"/>
<meta content="summary" name="twitter:card"/><meta content="@handle" name="twitter:site"/><meta content="No title" name="twitter:title"/><meta content="No description" name="twitter:description"/></head>
<body>
<p>Hi, there!</p>
</body>
</html>"""
    )


def test_twitter_card_with_mp3(mocker, mock_post, fs, requests_mock):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!
        """,
        )
    PostBuilder(root, config).process_post(post)

    assistant = TwitterCardAssistant(root, config)

    fs.create_file(post.file_path.parent / "demo1.mp3")
    mocker.patch(
        "nefelibata.assistants.twitter_card.MP3",
        return_value=AttrDict(
            {
                "TIT2": "Title 1",
                "TPE1": "Famous Artist",
                "TALB": "Some Album",
                "TDRC": 2020,
                "info": AttrDict(length=60),
                "TRCK": id3.TRCK(encoding=id3.Encoding.LATIN1, text=["3"]),
            },
        ),
    )

    with freeze_time("2020-01-01T00:00:00Z"):
        assistant.process_post(post)
    with freeze_time("2020-01-02T00:00:00Z"):
        assistant.process_post(post)

    assert datetime.fromtimestamp(
        post.file_path.with_suffix(".html").stat().st_mtime,
    ).astimezone(timezone.utc) == datetime(2020, 1, 1, 0, 0, tzinfo=timezone.utc)

    with open(post.file_path.with_suffix(".html")) as fp:
        contents = fp.read()

    assert (
        contents
        == """
<!DOCTYPE html>
<html lang="en">
<head>
<meta content="article" property="og:type"/>
<meta content="Post title" property="og:title"/>
<meta content="This is the post description" property="og:description"/>
<link href="https://webmention.io/example.com/webmention" rel="webmention"/>
<link href="https://external.example.com/css/basic.css" rel="stylesheet"/>
<link href="/css/style.css" rel="stylesheet"/>
<meta content="player" name="twitter:card"/><meta content="@handle" name="twitter:site"/><meta content="Post title" name="twitter:title"/><meta content="This is the post description" name="twitter:description"/><meta content="https://example.com/img/cassette.png" name="twitter:image"/><meta content="https://example.com/first/twitter_card.html" name="twitter:player"/><meta content="800" name="twitter:player:width"/><meta content="464" name="twitter:player:height"/></head>
<body>
<p>Hi, there!</p>
</body>
</html>"""
    )
