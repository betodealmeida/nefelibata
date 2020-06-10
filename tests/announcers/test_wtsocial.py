# -*- coding: utf-8 -*-
from pathlib import Path

from bs4 import BeautifulSoup
from freezegun import freeze_time
from nefelibata.announcers.wtsocial import WTSocialAnnouncer
from nefelibata.post import Post

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


def test_announcer(mock_post, requests_mock):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, WT.Social!
        keywords: test
        summary: My first WT.Social post
        announce-on: wtsocial

        Hi, there!
        """,
        )

    root = Path("/path/to/blog")
    config = {"url": "https://blog.example.com/"}
    announcer = WTSocialAnnouncer(
        root, config, "https://wtsocial.io/example.com/wtsocial", True,
    )

    # login
    html1 = """
<form method="POST" action="https://wt.social/login">
    <input type="hidden" name="_token" value="token1">
</form>
    """
    requests_mock.get("https://wt.social/login", text=html1)
    html2 = """
 <meta name="csrf-token" content="token2">
    """
    requests_mock.post("https://wt.social/login", text=html2)

    # new post
    requests_mock.post(
        "https://wt.social/api/new-article", json={"0": {"URI": "/post/hash"}},
    )

    url = announcer.announce(post)
    assert url == "https://wt.social/post/hash"

    # store URL in post
    post.parsed["wtsocial-url"] = url

    # get comments
    comment_list = [
        {
            "parentUrl": "",
            "comment_id": "hash2",
            "formatted": {
                "created_at": "2020-01-01T00:00:00Z",
                "comment_body": "Welcome!",
                "url": "",
            },
            "users_name": "User",
            "user_uri": "user",
            "UURI": "",
        },
    ]
    requests_mock.get(
        "https://wt.social/api/post/hash", json={"comment_list": comment_list},
    )
    profile = r'"media":{"profile":{"filepath":"https:\/\/wtsocial-uploads.s3.amazonaws.com\/uploads\/2019-11\/fileName1574188367--profile_pic.jpg"}'
    requests_mock.get("https://wt.social/u/user", text=profile)

    responses = announcer.collect(post)
    assert responses == [
        {
            "source": "WT.Social",
            "color": "#1e1e1e",
            "id": "wtsocial:hash2",
            "timestamp": "2020-01-01T00:00:00+00:00",
            "user": {
                "name": "User",
                "image": "https://wtsocial-uploads.s3.amazonaws.com/uploads/2019-11/fileName1574188367--profile_pic.jpg",
                "url": "https://wt.social",
                "description": "",
            },
            "comment": {"text": "Welcome!", "url": "https://wt.social#comment-hash2"},
            "url": "https://wt.social/post/hash",
        },
    ]


def test_announcer_no_csrf_token(mock_post, requests_mock):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, WT.Social!
        keywords: test
        summary: My first WT.Social post
        announce-on: wtsocial

        Hi, there!
        """,
        )

    root = Path("/path/to/blog")
    config = {"url": "https://blog.example.com/"}
    announcer = WTSocialAnnouncer(
        root, config, "https://wtsocial.io/example.com/wtsocial", True,
    )

    # login
    html1 = """
<form method="POST" action="https://wt.social/login">
    <input type="hidden" name="_token" value="token1">
</form>
    """
    requests_mock.get("https://wt.social/login", text=html1)
    html2 = ""
    requests_mock.post("https://wt.social/login", text=html2)

    # new post
    requests_mock.post(
        "https://wt.social/api/new-article", json={"0": {"URI": "/post/hash"}},
    )

    url = announcer.announce(post)
    assert url is None

    responses = announcer.collect(post)
    assert responses == []
