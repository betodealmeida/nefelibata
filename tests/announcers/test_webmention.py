# -*- coding: utf-8 -*-
import json
import os.path
import textwrap
from pathlib import Path
from unittest.mock import call
from unittest.mock import MagicMock

from bs4 import BeautifulSoup
from freezegun import freeze_time
from nefelibata.announcers.webmention import get_webmention_endpoint
from nefelibata.announcers.webmention import WebmentionAnnouncer
from nefelibata.post import Post

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


def test_get_webmention_endpoint_header(requests_mock):
    requests_mock.head(
        "https://user1.example.com/",
        headers={
            "Link": '<https://user1.example.com/webmention-endpoint>; rel="webmention"',
        },
    )
    url = get_webmention_endpoint("https://user1.example.com/")
    assert url == "https://user1.example.com/webmention-endpoint"


def test_get_webmention_endpoint_link(requests_mock):
    html = """
<html>
<head>
<link href="https://user2.example.com/webmention-endpoint" rel="webmention" />
</head>
<body>
Hello!
</body>
</html>
"""
    requests_mock.head(
        "https://user2.example.com/", headers={"Content-Type": "text/html"},
    )
    requests_mock.get(
        "https://user2.example.com/", text=html,
    )
    url = get_webmention_endpoint("https://user2.example.com/")
    assert url == "https://user2.example.com/webmention-endpoint"


def test_get_webmention_endpoint_anchor(requests_mock):
    html = """
<html>
<head>
</head>
<body>
<a href="https://user3.example.com/webmention-endpoint" rel="webmention">webmention</a>
</body>
</html>
"""
    requests_mock.head(
        "https://user3.example.com/", headers={"Content-Type": "text/html"},
    )
    requests_mock.get(
        "https://user3.example.com/", text=html,
    )
    url = get_webmention_endpoint("https://user3.example.com/")
    assert url == "https://user3.example.com/webmention-endpoint"


def test_get_webmention_non_html(requests_mock):
    requests_mock.head(
        "https://user4.example.com/", headers={"Content-Type": "application/pdf"},
    )
    url = get_webmention_endpoint("https://user4.example.com/")
    assert url is None


def test_get_webmention_endpoint_none(requests_mock):
    html = """
<html>
<head>
</head>
<body>
</body>
</html>
"""
    requests_mock.head(
        "https://user4.example.com/",
        headers={"Link": '<https://user1.example.com/atom.xml>; rel="alternate"'},
    )
    requests_mock.get(
        "https://user4.example.com/", text=html,
    )
    url = get_webmention_endpoint("https://user4.example.com/")
    assert url is None


def test_announcer(mock_post, requests_mock):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, friends!
        keywords: test, indieweb
        summary: My first post
        announce-on: webmention

        Hi, there! I heard [this blog](https://blog.example.com/) supports webmention.
        """,
        )

    root = Path("/path/to/blog")
    config = {"url": "https://blog.example.com/", "language": "en"}
    announcer = WebmentionAnnouncer(
        root, config, "https://webmention.io/example.com/webmention",
    )

    mock_send_mention = MagicMock()
    mock_send_mention.return_value = {"success": True}
    announcer._send_mention = mock_send_mention

    announcer.update_links(post)
    assert post.parsed["webmention-url"] == "https://commentpara.de/"

    mock_send_mention.assert_has_calls(
        [
            call(
                "https://blog.example.com/first/index.html",
                "https://blog.example.com/",
            ),
            call(
                "https://blog.example.com/first/index.html",
                "https://news.indieweb.org/en",
            ),
        ],
    )

    webmentions = {
        "type": "feed",
        "name": "Webmentions",
        "children": [
            {
                "type": "entry",
                "author": {
                    "type": "card",
                    "name": "Tantek Çelik",
                    "url": "http://tantek.com/",
                    "photo": "http://tantek.com/logo.jpg",
                },
                "url": "http://tantek.com/2013/112/t2/milestone-show-indieweb-comments-h-entry-pingback",
                "published": "2013-04-22T15:03:00-07:00",
                "wm-received": "2013-04-25T17:09:33-07:00",
                "wm-id": 900,
                "content": {
                    "text": "Another milestone: @eschnou automatically shows #indieweb comments with h-entry sent via pingback http://eschnou.com/entry/testing-indieweb-federation-with-waterpigscouk-aaronpareckicom-and--62-24908.html",
                    "html": r'Another milestone: &lt;a href="https:\/\/twitter.com\/eschnou">@eschnou&lt;\/a> automatically shows #indieweb comments with h-entry sent via pingback &lt;a href="http:\/\/eschnou.com\/entry\/testing-indieweb-federation-with-waterpigscouk-aaronpareckicom-and--62-24908.html">http:\/\/eschnou.com\/entry\/testing-indieweb-federation-with-waterpigscouk-aaronpareckicom-and--62-24908.html&lt;\/a>',
                },
            },
        ],
    }
    requests_mock.get("https://webmention.io/api/mentions.jf2", json=webmentions)

    results = announcer.collect(post)
    assert results == [
        {
            "source": "http://tantek.com/2013/112/t2/milestone-show-indieweb-comments-h-entry-pingback",
            "url": "http://tantek.com/2013/112/t2/milestone-show-indieweb-comments-h-entry-pingback",
            "id": "webmention:900",
            "timestamp": "2013-04-22T15:03:00-07:00",
            "user": {
                "name": "Tantek Çelik",
                "image": "http://tantek.com/logo.jpg",
                "url": "http://tantek.com/",
            },
            "comment": {
                "text": "Another milestone: @eschnou automatically shows #indieweb comments with h-entry sent via pingback http://eschnou.com/entry/testing-indieweb-federation-with-waterpigscouk-aaronpareckicom-and--62-24908.html",
            },
        },
    ]


def test_announcer_announced_partially(mock_post, requests_mock):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, friends!
        keywords: test, indieweb
        summary: My first post
        announce-on: webmention

        Hi, there! I heard [this blog](https://blog.example.com/) supports webmention.
        """,
        )

    root = Path("/path/to/blog")
    config = {"url": "https://blog.example.com/", "language": "en"}
    announcer = WebmentionAnnouncer(
        root, config, "https://webmention.io/example.com/webmention",
    )

    mock_send_mention = MagicMock()
    mock_send_mention.return_value = {"success": True}
    announcer._send_mention = mock_send_mention

    with open(post.file_path.parent / "webmentions.json", "w") as fp:
        json.dump({"https://blog.example.com/": {"success": True}}, fp)

    announcer.update_links(post)

    mock_send_mention.assert_called_with(
        "https://blog.example.com/first/index.html", "https://news.indieweb.org/en",
    )


def test_announcer_announced_exception_on_mention(mock_post, mocker, requests_mock):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, friends!
        keywords: test, indieweb
        summary: My first post
        announce-on: webmention

        Hi, there! I heard [this blog](https://blog.example.com/) supports webmention.
        """,
        )

    root = Path("/path/to/blog")
    config = {"url": "https://blog.example.com/", "language": "en"}
    announcer = WebmentionAnnouncer(
        root, config, "https://webmention.io/example.com/webmention",
    )

    mock_get_webmention_endpoint = MagicMock()
    mock_get_webmention_endpoint.return_value = "https://endpoint.example.com/"
    mocker.patch(
        "nefelibata.announcers.webmention.get_webmention_endpoint",
        mock_get_webmention_endpoint,
    )

    requests_mock.post("https://endpoint.example.com", status_code=500)

    with open(post.file_path.parent / "webmentions.json", "w") as fp:
        json.dump({"https://blog.example.com/": {"success": True}}, fp)

    announcer.update_links(post)
    assert post.parsed["webmention-url"] == "https://commentpara.de/"

    with open(post.file_path.parent / "webmentions.json") as fp:
        contents = json.load(fp)

    assert contents == {
        "https://blog.example.com/": {"success": True},
        "https://news.indieweb.org/en": {"success": False},
    }


def test_announcer_announced_indienews_only(mock_post, requests_mock):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, friends!
        keywords: test, indieweb
        summary: My first post
        announce-on: webmention

        Hi, there! I heard [this blog](https://blog.example.com/) supports webmention.
        """,
        )

    root = Path("/path/to/blog")
    config = {"url": "https://blog.example.com/", "language": "en"}
    announcer = WebmentionAnnouncer(
        root, config, "https://webmention.io/example.com/webmention",
    )

    mock_send_mention = MagicMock()
    mock_send_mention.return_value = {"success": True}
    announcer._send_mention = mock_send_mention

    with open(post.file_path.parent / "webmentions.json", "w") as fp:
        json.dump({"https://news.indieweb.org/en": {"success": True}}, fp)

    announcer.update_links(post)
    assert post.parsed["webmention-url"] == "https://commentpara.de/"

    mock_send_mention.assert_called_with(
        "https://blog.example.com/first/index.html", "https://blog.example.com/",
    )


def test_announcer_no_indienews(mock_post):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, friends!
        keywords: test
        summary: My first post
        announce-on: webmention

        Hi, there! I heard [this blog](https://blog.example.com/) supports webmention.
        """,
        )

    root = Path("/path/to/blog")
    config = {"url": "https://blog.example.com/", "language": "en"}
    announcer = WebmentionAnnouncer(
        root, config, "https://webmention.io/example.com/webmention",
    )

    mock_send_mention = MagicMock()
    mock_send_mention.return_value = {"success": True}
    announcer._send_mention = mock_send_mention

    url = announcer.announce(post)
    assert url == "https://commentpara.de/"
    mock_send_mention.assert_has_calls(
        [
            call(
                "https://blog.example.com/first/index.html",
                "https://blog.example.com/",
            ),
        ],
    )


def test_announcer_indienews_no_language(mock_post):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, friends!
        keywords: test, indieweb
        summary: My first post
        announce-on: webmention

        Hi, there! I heard [this blog](https://blog.example.com/) supports webmention.
        """,
        )

    root = Path("/path/to/blog")
    config = {"url": "https://blog.example.com/", "language": "pt_BR"}
    announcer = WebmentionAnnouncer(
        root, config, "https://webmention.io/example.com/webmention",
    )

    mock_send_mention = MagicMock()
    mock_send_mention.return_value = {"success": True}
    announcer._send_mention = mock_send_mention

    url = announcer.announce(post)
    assert url == "https://commentpara.de/"
    mock_send_mention.assert_has_calls(
        [
            call(
                "https://blog.example.com/first/index.html",
                "https://blog.example.com/",
            ),
        ],
    )


def test_announcer_send_mention(mock_post, requests_mock):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, friends!
        keywords: test, indieweb
        summary: My first post
        announce-on: webmention

        Hi, there! I heard [this blog](https://blog.example.com/) supports webmention.
        """,
        )

    root = Path("/path/to/blog")
    config = {"url": "https://blog.example.com/", "language": "en"}
    announcer = WebmentionAnnouncer(
        root, config, "https://webmention.io/example.com/webmention",
    )

    # indienews support webmention
    requests_mock.head(
        "https://news.indieweb.org/en",
        headers={
            "Link": '<https://user1.example.com/webmention-endpoint>; rel="webmention"',
        },
    )
    requests_mock.post("https://user1.example.com/webmention-endpoint")

    # the linked site does not
    html = "<html><head></head><body></body></html>"
    requests_mock.head(
        "https://blog.example.com/", headers={"Content-Type": "text/html"},
    )
    requests_mock.get("https://blog.example.com/", text=html)

    announcer.announce(post)


def test_announcer_exception(mock_post, requests_mock):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, friends!
        keywords: test, indieweb
        summary: My first post
        announce-on: webmention
        webmention-url: https://commentpara.de/

        Hi, there! I heard [this blog](https://blog.example.com/) supports webmention.
        """,
        )

    root = Path("/path/to/blog")
    config = {"url": "https://blog.example.com/", "language": "en"}
    announcer = WebmentionAnnouncer(
        root, config, "https://webmention.io/example.com/webmention",
    )

    # passing a target with non-ASCII characters results in a 500 from webmention.io
    requests_mock.get(
        "https://webmention.io/api/mentions.jf2",
        status_code=500,
        text="<h1>Internal Server Error</h1>",
    )

    results = announcer.collect(post)
    assert results == []
