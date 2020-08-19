# -*- coding: utf-8 -*-
import os.path
import textwrap
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from bs4 import BeautifulSoup
from freezegun import freeze_time
from nefelibata.announcers.fawm import extract_params
from nefelibata.announcers.fawm import FAWMAnnouncer
from nefelibata.announcers.fawm import get_comments_from_fawm_page
from nefelibata.announcers.fawm import get_response_from_li
from nefelibata.post import Post

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


def test_extract_params(mock_post, fs):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Dance tag
        keywords: pop, nerd
        summary: A song about HTML
        announce-on: fawm

        # Liner Notes

        This is a song about HTML.

        # Lyrics

        <pre>
            Oh, HTML.
            Will you dance with me?
        </pre>
        """,
        )

    root = Path("/path/to/blog")
    config = {"url": "https://blog.example.com/"}
    fs.create_file(post.file_path.parent / "demo.mp3")

    params = extract_params(post, root, config)
    assert params == {
        "id": "",
        "title": "Dance tag",
        "tags": "pop nerd",
        "demo": "https://blog.example.com/first/demo.mp3",
        "notes": "This is a song about HTML.",
        "lyrics": "Oh, HTML.\nWill you dance with me?",
        "status": "public",
        "collab": 0,
        "downloadable": 1,
        "submit": "Save+It!",
    }


def test_extract_params_no_lyrics(mock_post, fs):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Dance tag
        keywords: pop, nerd
        summary: A song about HTML
        announce-on: fawm

        # Liner Notes

        This is a song about HTML.
        """,
        )

    root = Path("/path/to/blog")
    config = {"url": "https://blog.example.com/"}
    fs.create_file(post.file_path.parent / "demo.mp3")

    params = extract_params(post, root, config)
    assert params == {
        "id": "",
        "title": "Dance tag",
        "tags": "pop nerd",
        "demo": "https://blog.example.com/first/demo.mp3",
        "notes": "This is a song about HTML.",
        "lyrics": "N/A",
        "status": "public",
        "collab": 0,
        "downloadable": 1,
        "submit": "Save+It!",
    }


def test_extract_params_multiple_mp3s(mock_post, fs):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Dance tag
        keywords: pop, nerd
        summary: A song about HTML
        announce-on: fawm

        # Liner Notes

        This is a song about HTML.
        """,
        )

    root = Path("/path/to/blog")
    config = {"url": "https://blog.example.com/"}
    fs.create_file(post.file_path.parent / "demo1.mp3")
    fs.create_file(post.file_path.parent / "demo2.mp3")

    with pytest.raises(Exception) as excinfo:
        extract_params(post, root, config)

    assert str(excinfo.value) == "Only posts with a single MP3 can be announced on FAWM"


def test_extract_params_no_demo(mock_post, fs):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Dance tag
        keywords: pop, nerd
        summary: A song about HTML
        announce-on: fawm

        # Liner Notes

        This is a song about HTML.
        """,
        )

    root = Path("/path/to/blog")
    config = {"url": "https://blog.example.com/"}

    params = extract_params(post, root, config)
    assert params == {
        "id": "",
        "title": "Dance tag",
        "tags": "pop nerd",
        "demo": "",
        "notes": "This is a song about HTML.",
        "lyrics": "N/A",
        "status": "public",
        "collab": 0,
        "downloadable": 1,
        "submit": "Save+It!",
    }


def test_get_comments_from_fawm_page(requests_mock):
    url = "https://fawm.org/songs/110082/"

    current_dir = os.path.dirname(__file__)
    with open(os.path.join(current_dir, "fawm.html")) as fp:
        html = fp.read()
    requests_mock.get(url, text=html)

    comments = get_comments_from_fawm_page(url, "username", "password")

    assert comments == [
        {
            "source": "FAWM",
            "url": "https://fawm.org/songs/110082/",
            "color": "#cc6600",
            "id": "fawm:565501",
            "timestamp": "2020-03-03T00:00:00+00:00",
            "user": {
                "name": "phylo",
                "image": "https://fawm.org/img/avatars/723.big.jpg",
                "url": "https://fawm.org/fawmers/phylo/",
            },
            "comment": {
                "text": "This tune is so sweet!  The melody is very catchy.  There are lots of little surprises in there.  Nice work.",
                "url": "https://fawm.org/songs/110082/#c565501",
            },
        },
        {
            "source": "FAWM",
            "url": "https://fawm.org/songs/110082/",
            "color": "#cc6600",
            "id": "fawm:564029",
            "timestamp": "2020-03-01T00:00:00+00:00",
            "user": {
                "name": "kahlo2013",
                "image": "https://fawm.org/img/avatars/7832.big.jpg",
                "url": "https://fawm.org/fawmers/kahlo2013/",
            },
            "comment": {
                "text": "This is really lovely feel-good kind of music that has a wonderful groove. The different instrumental layers - piano, bells, etc really play off each other quite well. Lovely composition and a pleasure to listen to!",
                "url": "https://fawm.org/songs/110082/#c564029",
            },
        },
        {
            "source": "FAWM",
            "url": "https://fawm.org/songs/110082/",
            "color": "#cc6600",
            "id": "fawm:562750",
            "timestamp": "2020-03-01T00:00:00+00:00",
            "user": {
                "name": "sadloaf",
                "image": "https://fawm.org/img/avatars/17162.big.jpg",
                "url": "https://fawm.org/fawmers/sadloaf/",
            },
            "comment": {
                "text": "Fun song. The major tonality and the sort of post-chiptuney tones gave me a sort of I Am Robot And Proud feeling. Very jealous of anyone that owns an OP-Z lol.",
                "url": "https://fawm.org/songs/110082/#c562750",
            },
        },
        {
            "source": "FAWM",
            "url": "https://fawm.org/songs/110082/",
            "color": "#cc6600",
            "id": "fawm:562632",
            "timestamp": "2020-03-01T00:00:00+00:00",
            "user": {
                "name": "standup",
                "image": "https://fawm.org/img/avatars/479.big.jpg",
                "url": "https://fawm.org/fawmers/standup/",
            },
            "comment": {
                "text": "Cool sounds, I like the flowing melody that drops in early. Great tones. Bell sounds and echoey bits! The echo might be the Kaoss ? but sounds like it's only on a certain part. I like the floating piano parts too. There's a lot here to like. Those delays throughout are adding a lot. \n\nI was briefly tempted by the OP-Z, but my synths are modular and softsynths, they do the job, and it would be another thing to learn!",
                "url": "https://fawm.org/songs/110082/#c562632",
            },
        },
    ]


def test_get_response_from_li():
    url = "https://fawm.org/songs/110082/"
    soup = BeautifulSoup(
        textwrap.dedent(
            """
            <li class="comment-item media" id="c562632">
            <div class="media-left">
            <a href="/fawmers/standup/">
            <img alt="" class="media-object img-rounded comment-avatar" src="/img/avatars/479.big.jpg" style="background-color: #ff8766;"/>
            </a>
            </div>
            <div class="media-body">
            <h5 class="media-heading">@<a class="user-ref" href="/fawmers/standup/"><strong>standup</strong> <i class="icon-donated"></i></a> <small class="text-muted">Mar 1</small>
            <small class="media-meta pull-right hidden-xs">
            <!-- <a href="#"><i class="fa fa-flag"></i>report abuse</a>
                        <a href="#"><i class="fa fa-pencil"></i>edit</a>
                        <a href="#"><i class="fa fa-trash"></i>delete</a>  -->
            </small></h5>
            <p id="q562632">Cool sounds, I like the flowing melody that drops in early. Great tones. Bell sounds and echoey bits! The echo might be the Kaoss ? but sounds like it's only on a certain part. I like the floating piano parts too. There's a lot here to like. Those delays throughout are adding a lot. <br/>
            <br/>
            I was briefly tempted by the OP-Z, but my synths are modular and softsynths, they do the job, and it would be another thing to learn!</p>
            </div>
            </li>
        """,
        ),
        features="html5lib",
    )
    el = soup.html.body.li
    response = get_response_from_li(url, el)

    assert response == {
        "source": "FAWM",
        "url": "https://fawm.org/songs/110082/",
        "color": "#cc6600",
        "id": "fawm:562632",
        "timestamp": "2020-03-01T00:00:00+00:00",
        "user": {
            "name": "standup",
            "image": "https://fawm.org/img/avatars/479.big.jpg",
            "url": "https://fawm.org/fawmers/standup/",
        },
        "comment": {
            "text": "Cool sounds, I like the flowing melody that drops in early. Great tones. Bell sounds and echoey bits! The echo might be the Kaoss ? but sounds like it's only on a certain part. I like the floating piano parts too. There's a lot here to like. Those delays throughout are adding a lot. \n\nI was briefly tempted by the OP-Z, but my synths are modular and softsynths, they do the job, and it would be another thing to learn!",
            "url": "https://fawm.org/songs/110082/#c562632",
        },
    }


def test_get_response_from_li_relative_timestamp():
    url = "https://fawm.org/songs/110082/"
    soup = BeautifulSoup(
        textwrap.dedent(
            """
            <li class="comment-item media" id="c562632">
            <div class="media-left">
            <a href="/fawmers/standup/">
            <img alt="" class="media-object img-rounded comment-avatar" src="/img/avatars/479.big.jpg" style="background-color: #ff8766;"/>
            </a>
            </div>
            <div class="media-body">
            <h5 class="media-heading">@<a class="user-ref" href="/fawmers/standup/"><strong>standup</strong> <i class="icon-donated"></i></a> <small class="text-muted">2 days</small>
            <small class="media-meta pull-right hidden-xs">
            <!-- <a href="#"><i class="fa fa-flag"></i>report abuse</a>
                        <a href="#"><i class="fa fa-pencil"></i>edit</a>
                        <a href="#"><i class="fa fa-trash"></i>delete</a>  -->
            </small></h5>
            <p id="q562632">Cool sounds, I like the flowing melody that drops in early. Great tones. Bell sounds and echoey bits! The echo might be the Kaoss ? but sounds like it's only on a certain part. I like the floating piano parts too. There's a lot here to like. Those delays throughout are adding a lot. <br/>
            <br/>
            I was briefly tempted by the OP-Z, but my synths are modular and softsynths, they do the job, and it would be another thing to learn!</p>
            </div>
            </li>
        """,
        ),
        features="html5lib",
    )
    el = soup.html.body.li
    with freeze_time("2020-01-01T00:00:00Z"):
        response = get_response_from_li(url, el)

    assert response == {
        "source": "FAWM",
        "url": "https://fawm.org/songs/110082/",
        "color": "#cc6600",
        "id": "fawm:562632",
        "timestamp": "2019-12-30T00:00:00+00:00",
        "user": {
            "name": "standup",
            "image": "https://fawm.org/img/avatars/479.big.jpg",
            "url": "https://fawm.org/fawmers/standup/",
        },
        "comment": {
            "text": "Cool sounds, I like the flowing melody that drops in early. Great tones. Bell sounds and echoey bits! The echo might be the Kaoss ? but sounds like it's only on a certain part. I like the floating piano parts too. There's a lot here to like. Those delays throughout are adding a lot. \n\nI was briefly tempted by the OP-Z, but my synths are modular and softsynths, they do the job, and it would be another thing to learn!",
            "url": "https://fawm.org/songs/110082/#c562632",
        },
    }


def test_announcer(mock_post, mocker, requests_mock):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Dance tag
        keywords: pop, nerd
        summary: A song about HTML
        announce-on: fawm

        # Liner Notes

        This is a song about HTML.

        # Lyrics

        <pre>
            Oh, HTML.
            Will you dance with me?
        </pre>
        """,
        )

    root = Path("/path/to/blog")
    config = {"url": "https://blog.example.com/"}
    announcer = FAWMAnnouncer(root, config, "username", "password")

    requests_mock.post(
        "https://fawm.org/songs/add",
        headers={"Location": "https://fawm.org/songs/110082/"},
    )
    url = announcer.announce(post)
    assert url == "https://fawm.org/songs/110082/"

    # store URL in post
    post.parsed["fawm-url"] = url

    mock_get_comments_from_fawm_page = MagicMock()
    mock_get_comments_from_fawm_page.return_value = [
        {
            "source": "FAWM",
            "url": "https://fawm.org/songs/110082/",
            "color": "#cc6600",
            "id": "fawm:565501",
            "timestamp": "1583222400.0",
            "user": {
                "name": "phylo",
                "image": "https://fawm.org/img/avatars/723.big.jpg",
                "url": "https://fawm.org/fawmers/phylo/",
            },
            "comment": {
                "text": "This tune is so sweet!  The melody is very catchy.  There are lots of little surprises in there.  Nice work.",
                "url": "https://fawm.org/songs/110082/#c565501",
            },
        },
    ]
    mocker.patch(
        "nefelibata.announcers.fawm.get_comments_from_fawm_page",
        mock_get_comments_from_fawm_page,
    )
    announcer.collect(post)
    mock_get_comments_from_fawm_page.assert_called_with(
        "https://fawm.org/songs/110082/", "username", "password",
    )
