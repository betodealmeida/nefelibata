import json
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any
from typing import Dict
from unittest.mock import MagicMock

import requests
from freezegun import freeze_time
from nefelibata.assistants.archive_links import ArchiveLinksAssistant
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


def test_archive_links(mock_post, requests_mock):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!

        This is [an external link](https://google.com/).
        This is a link to [the blog itself](https://example.com/).
        This is a link to [the Wayback Machine](https://archive.org/web).
        This is a link to <a href="https://webmention.io/example.com/webmention" rel="webmention">send webmentions</a>.
        """,
        )
    PostBuilder(root, config).process_post(post)

    assistant = ArchiveLinksAssistant(root, config)

    requests_mock.get(
        "https://web.archive.org/save/https://google.com/",
        headers={
            "Link": (
                '<https://google.com/>; rel="original", '
                '<https://web.archive.org/web/timemap/link/https://google.com/>; rel="timemap"; type="application/link-format", '
                '<https://web.archive.org/web/https://google.com/>; rel="timegate", '
                '<https://web.archive.org/web/20200101080000/https://google.com/>; rel="first memento"; datetime="Wed, 1 Jan 2020 00:00:00 GMT", '
                '<https://web.archive.org/web/20200101080000/https://google.com/>; rel="memento"; datetime="Wed, 1 Jan 2020 00:00:00 GMT", '
                '<https://web.archive.org/web/20200101080000/https://google.com/>; rel="last memento"; datetime="Wed, 1 Jan Nov 2020 00:00:00 GMT"'
            ),
        },
    )

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
</head>
<body>
<p>Hi, there!</p>
<p>This is <a data-archive-date="2020-01-01T00:00:00+00:00" data-archive-url="https://web.archive.org/web/20200101080000/https://google.com/" href="https://google.com/">an external link</a><span class="archive">[<a href="https://web.archive.org/web/20200101080000/https://google.com/">archived</a>]</span>.
This is a link to <a href="https://example.com/">the blog itself</a>.
This is a link to <a href="https://archive.org/web">the Wayback Machine</a>.
This is a link to <a href="https://webmention.io/example.com/webmention" rel="webmention">send webmentions</a>.</p>
</body>
</html>"""
    )


def test_archive_links_storage_exists(mock_post, mocker):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!

        This is [an external link](https://google.com/).
        This is a link to [the blog itself](https://example.com/).
        This is a link to [the Wayback Machine](https://archive.org/web).
        This is a link to <a href="https://webmention.io/example.com/webmention" rel="webmention">send webmentions</a>.
        """,
        )
    PostBuilder(root, config).process_post(post)

    assistant = ArchiveLinksAssistant(root, config)

    mock_requests = MagicMock()
    mocker.patch("nefelibata.assistants.archive_links.requests", mock_requests)

    archives = {
        "https://google.com/": {
            "url": "https://web.archive.org/web/20200101000000/https://google.com/",
            "date": "2020-01-01T08:00:00+00:00",
        },
    }
    storage = post.file_path.parent / "archives.json"
    with freeze_time("2020-01-01T00:00:00Z"):
        with open(storage, "w") as fp:
            json.dump(archives, fp)

    with freeze_time("2020-01-02T00:00:00Z"):
        assistant.process_post(post)

    mock_requests.get.assert_not_called()

    assert (
        datetime.fromtimestamp(storage.stat().st_mtime).astimezone(
            timezone.utc,
        )
        == datetime(2020, 1, 1, 0, 0, tzinfo=timezone.utc)
    )


def test_archive_links_already_modified(mock_post, requests_mock):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!

        This is [an external link](https://google.com/).
        This is a link to [the blog itself](https://example.com/).
        This is a link to [the Wayback Machine](https://archive.org/web).
        This is a link to <a href="https://webmention.io/example.com/webmention" rel="webmention">send webmentions</a>.
        """,
        )
    PostBuilder(root, config).process_post(post)

    assistant = ArchiveLinksAssistant(root, config)

    requests_mock.get(
        "https://web.archive.org/save/https://google.com/",
        headers={
            "Link": (
                '<https://google.com/>; rel="original", '
                '<https://web.archive.org/web/timemap/link/https://google.com/>; rel="timemap"; type="application/link-format", '
                '<https://web.archive.org/web/https://google.com/>; rel="timegate", '
                '<https://web.archive.org/web/20200101080000/https://google.com/>; rel="first memento"; datetime="Wed, 1 Jan 2020 00:00:00 GMT", '
                '<https://web.archive.org/web/20200101080000/https://google.com/>; rel="prev memento"; datetime="Wed, 1 Jan 2020 00:00:00 GMT", '
                '<https://web.archive.org/web/20200102080000/https://google.com/>; rel="memento"; datetime="Thu, 2 Jan 2020 00:00:00 GMT", '
                '<https://web.archive.org/web/20200102080000/https://google.com/>; rel="last memento"; datetime="Thu, 2 Jan Nov 2020 00:00:00 GMT"'
            ),
        },
    )

    with freeze_time("2020-01-02T00:00:00Z"):
        assistant.process_post(post)

    with freeze_time("2020-01-03T00:00:00Z"):
        assistant.process_post(post)

    assert (
        datetime.fromtimestamp(
            post.file_path.with_suffix(".html").stat().st_mtime,
        ).astimezone(timezone.utc)
        == datetime(2020, 1, 2, 0, 0, tzinfo=timezone.utc)
    )


def test_archive_links_update(mock_post, requests_mock):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!

        This is [an external link](https://google.com/).
        This is a link to [the blog itself](https://example.com/).
        This is a link to [the Wayback Machine](https://archive.org/web).
        This is a link to <a href="https://webmention.io/example.com/webmention" rel="webmention">send webmentions</a>.
        """,
        )
    PostBuilder(root, config).process_post(post)

    assistant = ArchiveLinksAssistant(root, config)

    archives = {
        "https://google.com/": {"url": None, "date": "2020-01-01T08:00:00+00:00"},
    }
    storage = post.file_path.parent / "archives.json"
    with freeze_time("2020-01-01T00:00:00Z"):
        with open(storage, "w") as fp:
            json.dump(archives, fp)

    with freeze_time("2020-01-01T01:00:00Z"):
        assistant.process_post(post)

    assert (
        datetime.fromtimestamp(storage.stat().st_mtime).astimezone(
            timezone.utc,
        )
        == datetime(2020, 1, 1, 0, 0, tzinfo=timezone.utc)
    )

    requests_mock.get(
        "https://web.archive.org/save/https://google.com/",
        headers={
            "Link": (
                '<https://google.com/>; rel="original", '
                '<https://web.archive.org/web/timemap/link/https://google.com/>; rel="timemap"; type="application/link-format", '
                '<https://web.archive.org/web/https://google.com/>; rel="timegate", '
                '<https://web.archive.org/web/20200101080000/https://google.com/>; rel="first memento"; datetime="Wed, 1 Jan 2020 00:00:00 GMT", '
                '<https://web.archive.org/web/20200102080000/https://google.com/>; rel="prev memento"; datetime="Thu, 2 Jan 2020 00:00:00 GMT", '
                '<https://web.archive.org/web/20200103080000/https://google.com/>; rel="memento"; datetime="Fri, 3 Jan 2020 00:00:00 GMT", '
                '<https://web.archive.org/web/20200103080000/https://google.com/>; rel="last memento"; datetime="Fri, 3 Jan Nov 2020 00:00:00 GMT"'
            ),
        },
    )

    with freeze_time("2020-01-03T00:00:00Z"):
        assistant.process_post(post)

    with open(storage) as fp:
        archives = json.load(fp)

    assert archives == {
        "https://google.com/": {
            "url": "https://web.archive.org/web/20200103080000/https://google.com/",
            "date": "2020-01-03T00:00:00+00:00",
        },
    }


def test_archive_links_timeout(mocker, mock_post):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!

        This is [an external link](https://google.com/).
        This is a link to [the blog itself](https://example.com/).
        This is a link to [the Wayback Machine](https://archive.org/web).
        This is a link to <a href="https://webmention.io/example.com/webmention" rel="webmention">send webmentions</a>.
        """,
        )
    PostBuilder(root, config).process_post(post)

    assistant = ArchiveLinksAssistant(root, config)

    mocker.patch(
        "nefelibata.assistants.archive_links.requests.get",
        side_effect=requests.exceptions.ReadTimeout(),
    )

    with freeze_time("2020-01-01T00:00:00Z"):
        assistant.process_post(post)

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
<p>Hi, there!</p>
<p>This is <a href="https://google.com/">an external link</a>.
This is a link to <a href="https://example.com/">the blog itself</a>.
This is a link to <a href="https://archive.org/web">the Wayback Machine</a>.
This is a link to <a href="https://webmention.io/example.com/webmention" rel="webmention">send webmentions</a>.</p>
</body>
</html>"""
    )


def test_archive_links_no_link_header(mock_post, requests_mock):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!

        This is [an external link](https://google.com/).
        This is a link to [the blog itself](https://example.com/).
        This is a link to [the Wayback Machine](https://archive.org/web).
        This is a link to <a href="https://webmention.io/example.com/webmention" rel="webmention">send webmentions</a>.
        """,
        )
    PostBuilder(root, config).process_post(post)

    assistant = ArchiveLinksAssistant(root, config)

    requests_mock.get("https://web.archive.org/save/https://google.com/")

    with freeze_time("2020-01-01T00:00:00Z"):
        assistant.process_post(post)

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
<p>Hi, there!</p>
<p>This is <a href="https://google.com/">an external link</a>.
This is a link to <a href="https://example.com/">the blog itself</a>.
This is a link to <a href="https://archive.org/web">the Wayback Machine</a>.
This is a link to <a href="https://webmention.io/example.com/webmention" rel="webmention">send webmentions</a>.</p>
</body>
</html>"""
    )


def test_archive_links_no_header_links(mocker, mock_post):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!

        This is [an external link](https://google.com/).
        This is a link to [the blog itself](https://example.com/).
        This is a link to [the Wayback Machine](https://archive.org/web).
        This is a link to <a href="https://webmention.io/example.com/webmention" rel="webmention">send webmentions</a>.
        """,
        )
    PostBuilder(root, config).process_post(post)

    assistant = ArchiveLinksAssistant(root, config)

    mock_requests = MagicMock()
    mock_requests.utils.parse_header_links.return_value = []
    mocker.patch("nefelibata.assistants.archive_links.requests", mock_requests)

    with freeze_time("2020-01-01T00:00:00Z"):
        assistant.process_post(post)

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
<p>Hi, there!</p>
<p>This is <a href="https://google.com/">an external link</a>.
This is a link to <a href="https://example.com/">the blog itself</a>.
This is a link to <a href="https://archive.org/web">the Wayback Machine</a>.
This is a link to <a href="https://webmention.io/example.com/webmention" rel="webmention">send webmentions</a>.</p>
</body>
</html>"""
    )
