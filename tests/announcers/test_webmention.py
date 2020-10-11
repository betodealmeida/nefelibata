# -*- coding: utf-8 -*-
import json
import os.path
import textwrap
from datetime import datetime
from datetime import timezone
from pathlib import Path
from unittest.mock import call
from unittest.mock import MagicMock

from bs4 import BeautifulSoup
from freezegun import freeze_time
from nefelibata.announcers.webmention import get_response_from_child
from nefelibata.announcers.webmention import get_webmention_endpoint
from nefelibata.announcers.webmention import summarize
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
        "https://user3.example.com/",
        headers={"Content-Type": "text/html; charset=UTF-8"},
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
                    "html": 'Another milestone: <a href="https://twitter.com/eschnou">@eschnou</a> automatically shows #indieweb comments with h-entry sent via pingback <a href="http://eschnou.com/entry/testing-indieweb-federation-with-waterpigscouk-aaronpareckicom-and--62-24908.html">http://eschnou.com/entry/testing-indieweb-federation-with-waterpigscouk-aaronpareckicom-and--62-24908.html</a>',
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
                "html": 'Another milestone: <a href="https://twitter.com/eschnou">@eschnou</a> automatically shows #indieweb comments with h-entry sent via pingback <a href="http://eschnou.com/entry/testing-indieweb-federation-with-waterpigscouk-aaronpareckicom-and--62-24908.html">http://eschnou.com/entry/testing-indieweb-federation-with-waterpigscouk-aaronpareckicom-and--62-24908.html</a>',
                "summary": "Another milestone: @eschnou automatically shows #indieweb comments with h-entry sent via pingback http://eschnou.com/entry/testing-indieweb-federation-with-waterpigscouk-aaronpareckicom-and--62-24908.html",
            },
        },
    ]


def test_announcer_announced_partially(mock_post):
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
        json.dump(
            {"https://blog.example.com/": {"success": True, "content": "Accepted"}}, fp,
        )

    announcer.update_links(post)

    mock_send_mention.assert_called_with(
        "https://blog.example.com/first/index.html", "https://news.indieweb.org/en",
    )


def test_announcer_announced_queued(mock_post):
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

    mock_update_webmention = MagicMock()
    mock_update_webmention.return_value = {"success": True, "content": "Accepted"}
    announcer._update_webmention = mock_update_webmention

    with open(post.file_path.parent / "webmentions.json", "w") as fp:
        json.dump(
            {
                "https://blog.example.com/": {
                    "success": True,
                    "content": {
                        "status": "queued",
                        "location": "https://blog.example.com/mention/12345",
                    },
                },
                "https://news.indieweb.org/en": {
                    "success": True,
                    "content": {
                        "status": "queued",
                        "location": "https://news.indieweb.org/en/mention/12345",
                    },
                },
            },
            fp,
        )

    announcer.update_links(post)

    mock_update_webmention.assert_has_calls(
        [
            call(
                {
                    "success": True,
                    "content": {
                        "status": "queued",
                        "location": "https://blog.example.com/mention/12345",
                    },
                },
            ),
            call(
                {
                    "success": True,
                    "content": {
                        "status": "queued",
                        "location": "https://news.indieweb.org/en/mention/12345",
                    },
                },
            ),
        ],
    )


def test_update_webmention(requests_mock):
    root = Path("/path/to/blog")
    config = {"url": "https://blog.example.com/", "language": "en"}
    announcer = WebmentionAnnouncer(
        root, config, "https://webmention.io/example.com/webmention",
    )

    webmention = {
        "success": True,
        "content": {
            "status": "queued",
            "location": "https://blog.example.com/mention/12345",
        },
    }
    updated_webmention = {
        "status": "accepted",
        "location": "https://blog.example.com/mention/12345",
    }
    requests_mock.get("https://blog.example.com/mention/12345", json=updated_webmention)

    assert announcer._update_webmention(webmention) == {
        "success": True,
        "content": updated_webmention,
    }


def test_update_webmention_error(requests_mock):
    root = Path("/path/to/blog")
    config = {"url": "https://blog.example.com/", "language": "en"}
    announcer = WebmentionAnnouncer(
        root, config, "https://webmention.io/example.com/webmention",
    )

    webmention = {
        "success": True,
        "content": {
            "status": "queued",
            "location": "https://blog.example.com/mention/12345",
        },
    }
    requests_mock.get(
        "https://blog.example.com/mention/12345", text="Not Found", status_code=404,
    )

    assert announcer._update_webmention(webmention) == webmention


def test_update_webmention_timeout(mocker):
    root = Path("/path/to/blog")
    config = {"url": "https://blog.example.com/", "language": "en"}
    announcer = WebmentionAnnouncer(
        root, config, "https://webmention.io/example.com/webmention",
    )

    webmention = {
        "success": True,
        "content": {
            "status": "queued",
            "location": "https://blog.example.com/mention/12345",
        },
    }
    mocker.patch(
        "nefelibata.announcers.webmention.requests.get",
        side_effect=Exception("Timeout!"),
    )

    assert announcer._update_webmention(webmention) == webmention


def test_update_webmention_not_json(requests_mock):
    root = Path("/path/to/blog")
    config = {"url": "https://blog.example.com/", "language": "en"}
    announcer = WebmentionAnnouncer(
        root, config, "https://webmention.io/example.com/webmention",
    )

    webmention = {
        "success": True,
        "content": {
            "status": "queued",
            "location": "https://blog.example.com/mention/12345",
        },
    }
    requests_mock.get("https://blog.example.com/mention/12345", text="Accepted")

    assert announcer._update_webmention(webmention) == {
        "success": True,
        "content": "Accepted",
    }


def test_announcer_announced_no_new_mentions(mock_post):
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
    mock_send_mention.return_value = {"success": True, "content": "Accepted"}
    announcer._send_mention = mock_send_mention

    with freeze_time("2020-01-01T00:00:00Z"):
        with open(post.file_path.parent / "webmentions.json", "w") as fp:
            json.dump(
                {
                    "https://blog.example.com/": {
                        "success": True,
                        "content": "Accepted",
                    },
                    "https://news.indieweb.org/en": {
                        "success": True,
                        "content": "Accepted",
                    },
                },
                fp,
            )

    with freeze_time("2020-01-02T00:00:00Z"):
        announcer.update_links(post)

    assert datetime.fromtimestamp(
        (post.file_path.parent / "webmentions.json").stat().st_mtime,
    ).astimezone(timezone.utc) == datetime(2020, 1, 1, 0, 0, tzinfo=timezone.utc)


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
        json.dump(
            {"https://blog.example.com/": {"success": True, "content": "Accepted"}}, fp,
        )

    announcer.update_links(post)
    assert post.parsed["webmention-url"] == "https://commentpara.de/"

    with open(post.file_path.parent / "webmentions.json") as fp:
        contents = json.load(fp)

    assert contents == {
        "https://blog.example.com/": {"success": True, "content": "Accepted"},
        "https://news.indieweb.org/en": {"success": False},
    }


def test_announcer_announced_indienews_only(mock_post):
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
        json.dump(
            {"https://news.indieweb.org/en": {"success": True, "content": "Accepted"}},
            fp,
        )

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
    mock_send_mention.return_value = {"success": True, "content": "Accepted"}
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


def test_summarize():
    text = """<p>This post is inspired by the similarly named <a href="https://ohhelloana.blog/blogging-and-me/">"Blogging and me"</a><span>[<a href="https://web.archive.org/web/20200610010420/https://ohhelloana.blog/blogging-and-me/">archived</a>]</span>, by <a href="https://ohhelloana.blog/">Ana Rodrigues</a><span>[<a href="https://web.archive.org/web/20200610010421/https://ohhelloana.blog/">archived</a>]</span>. In her post, Ana describes her blogging life, in particular how it hit a hiatus in 2012 due to her lack of confidence, impostor syndrome, and a feeling that she had nothing important to say. It's a really honest and insightful account, and I highly recommend reading it.</p>\n<p>My experience with blogging started back in 2001, when I started learning how to program in PHP and to use MySQL. I ran many different platforms since then, including <a href="http://cafelog.com/">b2</a><span>[<a href="https://web.archive.org/web/20200610010423/http://cafelog.com/">archived</a>]</span>, <a href="https://pyblosxom.github.io/">pyblosxom</a><span>[<a href="https://web.archive.org/web/20200610010423/https://pyblosxom.github.io/">archived</a>]</span>, and <a href="https://wordpress.org/">Wordpress</a><span>[<a href="https://web.archive.org/web/20200610010423/https://wordpress.org/">archived</a>]</span> (I was always jealous of my friends running <a href="https://www.movabletype.org/">Movable Type</a><span>[<a href="https://web.archive.org/web/20200610010424/https://www.movabletype.org/">archived</a>]</span>, with its beautiful typography, but I didn't have the money to pay for it). At some point, I started making my own blogging software, including one based on AJAX called <a href="https://pypi.org/project/webskine/">webskine</a><span>[<a href="https://web.archive.org/web/20200610010425/https://pypi.org/project/webskine/">archived</a>]</span> ("a web Moleskine"), back when AJAX was a new thing. I also had a microblog <a href="https://web.archive.org/web/20051126032425/http://dealmeida.net/">back in 2005</a> that would show only a single phrase and had an Atom feed.</p>\n<p>Like Ana, I also stopped blogging somewhere around 2012. And like Ana, I also stopped blogging when I got my first job in tech, for similar reasons.</p>\n<p>First, blogs were stagnating and people were adopting Twitter and Facebook. I built my current blogging software, <a href="https://github.com/betodealmeida/nefelibata/">nefelibata</a><span>[<a href="https://web.archive.org/web/20200610010426/https://github.com/betodealmeida/nefelibata/">archived</a>]</span>, back in 2013 as a way of better integrating blogs with social media, bringing the conversation to where people were, while keeping my content where I owned it. But after a year I started working at Facebook, and that quickly became my new world.</p>\n<p>Second, I was a self-taught programmer working with many brilliant people, and I felt everything I wanted to say could be said better by someone else. The things I learned were obvious, and I felt embarrassed that I didn't know them yet. Only many years later I would start overcoming my impostor syndrome, and to realize that <strong>because of it</strong> I was actually good at teaching and explaining difficult concepts.</p>\n<p>Before 2012 I wrote probably a hundred posts about programming. As I was learning and falling in love with Python, I would write posts to share my excitement and new knowledge. In many of those posts I didn't know what I was talking about — I remember one where I called something "metaprogramming" which was just... programming — but that was OK, because I felt I was on some kind of journey. Learning was the norm.</p>\n<p>I miss that feeling.</p>\n<p>Last year I attended <a href="https://xoxofest.com/2019/">XOXO</a><span>[<a href="https://web.archive.org/web/20200610012435/https://xoxofest.com/2019/">archived</a>]</span> in Portland, and I met dozens of amazing online content producers. I remembered my old blog, and decided to start writing again. I bought back an old domain that I had many years ago, taoetc.org, a play on the expression <em>"etc. e tal"</em> from Portuguese. It captures well all the things I enjoy doing and all the things I've learned in my path through life.</p>\n<p>And this year, as I was starting to get back into blogging again, I came across the <a href="https://indieweb.org/">IndieWeb</a><span>[<a href="https://web.archive.org/web/20200610012436/https://indieweb.org/">archived</a>]</span>, a community of personal websites connected together by simple standards. Instead of having companies hosting (and owning) our content, each person has their own domain, their own data, their own blog, and they communicate with each other. This way we can build a decentralized social network that is fun, quirky and personalized, like the web was supposed to be.</p>\n<p>As an example of how this works, later this month there's an event called <a href="https://events.indieweb.org/2020/06/indiewebcamp-west-2020-ZB8zoAAu6sdN">IndieWebCamp 2020 West</a><span>[<a href="https://web.archive.org/web/20200610012437/https://events.indieweb.org/2020/06/indiewebcamp-west-2020-ZB8zoAAu6sdN">archived</a>]</span>, a "two days meeting up online to share ideas, create &amp; improve personal websites, and build upon each other's creations." One of the ways of signing up is to <strong>make a post on your own weblog</strong> RSVPing yes, like I did <a href="https://blog.taoetc.org/indiewebcamp_2020_west/index.html">here</a>. My blog then notifies the IndieWebCamp website that I mentioned them using a <a href="https://www.w3.org/TR/webmention/">W3C Recommendation</a><span>[<a href="https://web.archive.orgOverview.html">archived</a>]</span>, and they check my answer to the event by extracting metadata from my post. Isn't that awesome?</p>\n<p>It's good to be back.</p>"""
    url = "https://blog.taoetc.org/indiewebcamp_2020_west/index.html"
    assert (
        summarize(text, url)
        == """As an example of how this works, later this month there's an event called IndieWebCamp 2020 West[archived], a "two days meeting up online to share ideas, create & improve personal websites, and build upon each other's creations." One of the ways of signing up is to make a post on your own weblog RSVPing yes, like I did here. My blog then notifies the IndieWebCamp website that I mentioned them using a W3C Recommendation[archived], and they check my answer to the event by extracting metadata from my post. Isn't that awesome?"""
    )


def test_summarize_text():
    text = "Oh, hello!\nHow are you today?"
    assert summarize(text) == "Oh, hello!"


def test_summarize_no_paragraph():
    text = '<a href="https://example.com/">This is cool</a>, right?\nLove it.'
    url = "https://example.com/"
    assert summarize(text, url) == "This is cool, right?"


def test_get_response_from_child():
    child = {
        "type": "entry",
        "author": {
            "type": "card",
            "name": "Checkmention",
            "photo": "https://webmention.io/avatar/checkmention.appspot.com/18d522b2ddbef12a0a104dd17fbc24c15dcf0d123bc6611687e0051e13fc1559.png",
            "url": "https://checkmention.appspot.com/",
        },
        "url": "https://checkmention.appspot.com/content/17232f08aee/f4b3b18d39e054995940ad100ccbbb59635fc1e8/success",
        "published": "2020-05-20T16:35:24+00:00",
        "wm-received": "2020-05-20T16:35:30Z",
        "wm-id": 798949,
        "wm-source": "https://checkmention.appspot.com/content/17232f08aee/f4b3b18d39e054995940ad100ccbbb59635fc1e8/success",
        "wm-target": "https://blog.taoetc.org/webmention_test_2/index.html",
        "in-reply-to": "https://blog.taoetc.org/webmention_test_2/index.html",
        "wm-property": "in-reply-to",
        "wm-private": False,
    }
    url = "https://example.com/"
    assert get_response_from_child(child, url) == {
        "source": "https://checkmention.appspot.com/content/17232f08aee/f4b3b18d39e054995940ad100ccbbb59635fc1e8/success",
        "url": "https://checkmention.appspot.com/content/17232f08aee/f4b3b18d39e054995940ad100ccbbb59635fc1e8/success",
        "id": "webmention:798949",
        "timestamp": "2020-05-20T16:35:24+00:00",
        "user": {
            "name": "Checkmention",
            "image": "https://webmention.io/avatar/checkmention.appspot.com/18d522b2ddbef12a0a104dd17fbc24c15dcf0d123bc6611687e0051e13fc1559.png",
            "url": "https://checkmention.appspot.com/",
        },
        "comment": {"text": "", "html": "", "summary": ""},
    }
