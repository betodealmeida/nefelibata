# -*- coding: utf-8 -*-
import os.path
import textwrap
from datetime import datetime
from datetime import timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from bs4 import BeautifulSoup
from freezegun import freeze_time
from nefelibata.announcers.fiftyninety import extract_params
from nefelibata.announcers.fiftyninety import FiftyNinetyAnnouncer
from nefelibata.announcers.fiftyninety import get_comments_from_fiftyninety_page
from nefelibata.announcers.fiftyninety import get_fid
from nefelibata.announcers.fiftyninety import get_session
from nefelibata.announcers.fiftyninety import parse_fuzzy_timestamp
from nefelibata.post import Post

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


add_song_page = """
    <html>
    <head>
        <script src="https://example.com/example.js"></script>
        <script>jQuery.extend(Drupal.settings, {"media": {"elements": {".js-media-element-edit-field-demo-und-0-upload": {"global": {"options": "options"}}}}});</script>
    </head>
    <body>
        <form id="bogus">
            <input name="form_build_id" value="foo" />
            <input name="form_token" value="bar" />
        </form>
        <form id="song-node-form">
            <input name="form_build_id" value="form_build_id" />
            <input name="form_token" value="form_token" />
        </form>
    </body>
    </html>
"""

add_song_page_no_js_1 = """
    <html>
    <head>
        <script src="https://example.com/example.js"></script>
    </head>
    <body>
        <form id="bogus">
            <input name="form_build_id" value="foo" />
            <input name="form_token" value="bar" />
        </form>
        <form id="song-node-form">
            <input name="form_build_id" value="form_build_id" />
            <input name="form_token" value="form_token" />
        </form>
    </body>
    </html>
"""

add_song_page_no_js_2 = """
    <html>
    <head>
        <script src="https://example.com/example.js"></script>
        <script>jQuery.extend(Drupal.settings);</script>
    </head>
    <body>
        <form id="bogus">
            <input name="form_build_id" value="foo" />
            <input name="form_token" value="bar" />
        </form>
        <form id="song-node-form">
            <input name="form_build_id" value="form_build_id" />
            <input name="form_token" value="form_token" />
        </form>
    </body>
    </html>
"""

login_page = """
    <html>
    <body>
        <form id="bogus">
            <input name="form_build_id" value="foo" />
        </form>
        <form id="user-login-form">
            <input name="form_build_id" value="form_build_id" />
        </form>
    </body>
    </html>
"""

fid_page = """
    <html>
    <body>
        <form id="bogus">
            <input name="form_build_id" value="foo" />
            <input name="form_token" value="bar" />
        </form>
        <form id="remote-stream-wrapper-file-add-form">
            <input name="form_build_id" value="form_build_id" />
            <input name="form_token" value="form_token" />
        </form>
    </body>
    </html>
"""


def test_extract_params(mocker, mock_post, fs):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Dance tag
        keywords: pop, nerd
        summary: A song about HTML
        announce-on: fiftyninety

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

    mock_session = MagicMock()
    mock_session.get.return_value.text = add_song_page
    mocker.patch("nefelibata.announcers.fiftyninety.get_fid", return_value="fid")

    params = extract_params(mock_session, post, root, config)
    assert params == {
        "body[und][0][value]": "This is a song about HTML.",
        "field_collab[und][0][_weight]": "0",
        "field_demo[und][0][display]": "1",
        "field_demo[und][0][fid]": "fid",
        "field_downloadable[und]": "1",
        "field_lyrics[und][0][value]": "Oh, HTML.\nWill you dance with me?",
        "field_tags[und]": "pop, nerd",
        "form_build_id": "form_build_id",
        "form_id": "song_node_form",
        "form_token": "form_token",
        "op": "Save",
        "title": "Dance tag",
        "changed": "",
    }


def test_extract_params_no_js(mocker, mock_post, fs):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Dance tag
        keywords: pop, nerd
        summary: A song about HTML
        announce-on: fiftyninety

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

    mock_session = MagicMock()
    mock_session.get.return_value.text = add_song_page_no_js_1
    mocker.patch("nefelibata.announcers.fiftyninety.get_fid", return_value="fid")

    with pytest.raises(Exception) as excinfo:
        extract_params(mock_session, post, root, config)

    assert str(excinfo.value) == "Unable to find options from Javascript"

    mock_session.get.return_value.text = add_song_page_no_js_2
    mocker.patch("nefelibata.announcers.fiftyninety.get_fid", return_value="fid")

    with pytest.raises(Exception) as excinfo:
        extract_params(mock_session, post, root, config)

    assert str(excinfo.value) == "Unable to parse options from Javascript"


def test_extract_params_no_lyrics(mocker, mock_post, fs):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Dance tag
        keywords: pop, nerd
        summary: A song about HTML
        announce-on: fiftyninety

        # Liner Notes

        This is a song about HTML.
        """,
        )

    root = Path("/path/to/blog")
    config = {"url": "https://blog.example.com/"}
    fs.create_file(post.file_path.parent / "demo.mp3")

    mock_session = MagicMock()
    mock_session.get.return_value.text = add_song_page
    mocker.patch("nefelibata.announcers.fiftyninety.get_fid", return_value="fid")

    params = extract_params(mock_session, post, root, config)
    assert params == {
        "body[und][0][value]": "This is a song about HTML.",
        "field_collab[und][0][_weight]": "0",
        "field_demo[und][0][display]": "1",
        "field_demo[und][0][fid]": "fid",
        "field_downloadable[und]": "1",
        "field_lyrics[und][0][value]": "N/A",
        "field_tags[und]": "pop, nerd",
        "form_build_id": "form_build_id",
        "form_id": "song_node_form",
        "form_token": "form_token",
        "op": "Save",
        "title": "Dance tag",
        "changed": "",
    }


def test_extract_params_multiple_mp3s(mock_post, fs):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Dance tag
        keywords: pop, nerd
        summary: A song about HTML
        announce-on: fiftyninety

        # Liner Notes

        This is a song about HTML.
        """,
        )

    root = Path("/path/to/blog")
    config = {"url": "https://blog.example.com/"}
    fs.create_file(post.file_path.parent / "demo1.mp3")
    fs.create_file(post.file_path.parent / "demo2.mp3")

    mock_session = MagicMock()

    with pytest.raises(Exception) as excinfo:
        extract_params(mock_session, post, root, config)

    assert (
        str(excinfo.value)
        == "Only posts with a single MP3 can be announced on FiftyNinety"
    )


def test_extract_params_no_demo(mocker, mock_post, fs):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Dance tag
        keywords: pop, nerd
        summary: A song about HTML
        announce-on: fiftyninety

        # Liner Notes

        This is a song about HTML.
        """,
        )

    root = Path("/path/to/blog")
    config = {"url": "https://blog.example.com/"}

    mock_session = MagicMock()
    mock_session.get.return_value.text = add_song_page
    mocker.patch("nefelibata.announcers.fiftyninety.get_fid", return_value="fid")

    params = extract_params(mock_session, post, root, config)
    assert params == {
        "body[und][0][value]": "This is a song about HTML.",
        "field_collab[und][0][_weight]": "0",
        "field_demo[und][0][display]": "1",
        "field_demo[und][0][fid]": "",
        "field_downloadable[und]": "0",
        "field_lyrics[und][0][value]": "N/A",
        "field_tags[und]": "pop, nerd",
        "form_build_id": "form_build_id",
        "form_id": "song_node_form",
        "form_token": "form_token",
        "op": "Save",
        "title": "Dance tag",
        "changed": "",
    }


def test_announcer(mock_post, mocker, requests_mock):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Dance tag
        keywords: pop, nerd
        summary: A song about HTML
        announce-on: fiftyninety

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
    announcer = FiftyNinetyAnnouncer(root, config, "username", "password")

    mock_session = MagicMock()
    mock_session.post.return_value.headers = {
        "Location": "https://fiftyninety.org/songs/110082/",
    }
    mocker.patch(
        "nefelibata.announcers.fiftyninety.get_session", return_value=mock_session,
    )
    mocker.patch("nefelibata.announcers.fiftyninety.extract_params", return_value={})
    url = announcer.announce(post)
    assert url == "https://fiftyninety.org/songs/110082/"

    # store URL in post
    post.parsed["fiftyninety-url"] = url

    mock_get_comments_from_fiftyninety_page = MagicMock()
    mock_get_comments_from_fiftyninety_page.return_value = [
        {
            "source": "FiftyNinety",
            "url": "https://fiftyninety.org/songs/110082/",
            "color": "#cc6600",
            "id": "fiftyninety:565501",
            "timestamp": "1583222400.0",
            "user": {
                "name": "phylo",
                "image": "https://fiftyninety.org/img/avatars/723.big.jpg",
                "url": "https://fiftyninety.org/fiftyninetyers/phylo/",
            },
            "comment": {
                "text": "This tune is so sweet!  The melody is very catchy.  There are lots of little surprises in there.  Nice work.",
                "url": "https://fiftyninety.org/songs/110082/#c565501",
            },
        },
    ]
    mocker.patch(
        "nefelibata.announcers.fiftyninety.get_comments_from_fiftyninety_page",
        mock_get_comments_from_fiftyninety_page,
    )
    announcer.collect(post)
    mock_get_comments_from_fiftyninety_page.assert_called_with(
        mock_session, "https://fiftyninety.org/songs/110082/", "username", "password",
    )


def test_get_session(mocker):
    mock_session = MagicMock()
    mock_session.get.return_value.text = login_page
    mocker.patch(
        "nefelibata.announcers.fiftyninety.requests.Session", return_value=mock_session,
    )

    get_session("username", "password")

    mock_session.post.assert_called_with(
        "http://fiftyninety.fawmers.org/node",
        params={"destination": "node"},
        data={
            "name": "username",
            "pass": "password",
            "form_build_id": "form_build_id",
            "form_id": "user_login_block",
            "feed_me": "",
            "op": "Log+in",
        },
    )


def test_get_fid(mocker):
    mock_session = MagicMock()
    mock_session.get.return_value.text = fid_page
    mock_session.post.return_value.headers = {
        "Location": "https://example.com/?fid=fid",
    }

    fid = get_fid(mock_session, "options", "https://example.com/demo.mp3")
    assert fid == "fid"

    mock_session.get.assert_called_with(
        "http://fiftyninety.fawmers.org/media/browser",
        params={"options": "options", "plugins": "undefined", "render": "media-popup"},
    )
    mock_session.post.assert_called_with(
        "http://fiftyninety.fawmers.org/media/browser",
        params={"options": "options", "plugins": "undefined", "render": "media-popup"},
        data={
            "form_build_id": "form_build_id",
            "form_id": "remote_stream_wrapper_file_add_form",
            "form_token": "form_token",
            "op": "Submit",
            "url": "https://example.com/demo.mp3",
        },
        allow_redirects=False,
    )


def test_parse_fuzzy_timestamp():
    with freeze_time("2020-01-01T00:00:00Z"):
        timestamp = parse_fuzzy_timestamp("0 sec")
    assert timestamp == datetime(2020, 1, 1, 0, 0, tzinfo=timezone.utc)

    with freeze_time("2020-01-01T00:00:00Z"):
        timestamp = parse_fuzzy_timestamp("3 min 50 sec")
    assert timestamp == datetime(2019, 12, 31, 23, 56, 10, tzinfo=timezone.utc)

    with freeze_time("2020-01-01T00:00:00Z"):
        timestamp = parse_fuzzy_timestamp("20 hours 38 min")
    assert timestamp == datetime(2019, 12, 31, 3, 22, tzinfo=timezone.utc)

    with freeze_time("2020-01-01T00:00:00Z"):
        timestamp = parse_fuzzy_timestamp("1 hour 52 min")
    assert timestamp == datetime(2019, 12, 31, 22, 8, tzinfo=timezone.utc)

    with freeze_time("2020-01-01T00:00:00Z"):
        timestamp = parse_fuzzy_timestamp("1 day 16 hours")
    assert timestamp == datetime(2019, 12, 30, 8, 0, tzinfo=timezone.utc)

    with freeze_time("2020-01-01T00:00:00Z"):
        timestamp = parse_fuzzy_timestamp("1 month 4 days")
    assert timestamp == datetime(2019, 11, 28, 0, 0, tzinfo=timezone.utc)


def test_get_comments_from_fiftyninety_page():
    url = "http://fiftyninety.fawmers.org/song/41558"

    current_dir = os.path.dirname(__file__)
    with open(os.path.join(current_dir, "fiftyninety.html")) as fp:
        html = fp.read()

    mock_session = MagicMock()
    mock_session.get.return_value.text = html

    with freeze_time("2020-01-01T00:00:00Z"):
        responses = get_comments_from_fiftyninety_page(
            mock_session, url, "username", "password",
        )
    assert responses == [
        {
            "source": "50/90",
            "url": "http://fiftyninety.fawmers.org/song/41558",
            "color": "#284ead",
            "id": "fiftyninety:2328",
            "timestamp": "2019-12-29T23:08:00+00:00",
            "user": {
                "name": "nancyrost",
                "url": "http://fiftyninety.fawmers.org/user/nancyrost",
                "image": "http://fiftyninety.fawmers.org/sites/default/files/styles/medium/public/pictures/picture-127-1372000342.jpg?itok=m34msJME",
            },
            "comment": {
                "text": "Whimsical for sure - it's a happy melody, and the quivering effect makes it sound like it's laughing. The coolness of the rain samples is very welcome on this hot day!",
                "url": "http://fiftyninety.fawmers.org/song/41558#comment-2328",
            },
        },
        {
            "source": "50/90",
            "url": "http://fiftyninety.fawmers.org/song/41558",
            "color": "#284ead",
            "id": "fiftyninety:2330",
            "timestamp": "2019-12-29T23:13:00+00:00",
            "user": {
                "name": "coolparadiso",
                "url": "http://fiftyninety.fawmers.org/user/coolparadiso",
                # "image": "http://fiftyninety.fawmers.org/sites/default/files/styles/medium/public/pictures/picture-448327-1561203958.jpg?itok=DpAOblZ6",
            },
            "comment": {
                "text": "yeah i like that one. i love your notes its like reading swahili, but slowly getting to understand some words. i like the rain",
                "url": "http://fiftyninety.fawmers.org/song/41558#comment-2330",
            },
        },
        {
            "source": "50/90",
            "url": "http://fiftyninety.fawmers.org/song/41558",
            "color": "#284ead",
            "id": "fiftyninety:2422",
            "timestamp": "2019-12-30T07:00:00+00:00",
            "user": {
                "name": "IA",
                "url": "http://fiftyninety.fawmers.org/user/ia",
                "image": "http://fiftyninety.fawmers.org/sites/default/files/styles/medium/public/pictures/picture-887-1592732750.jpg?itok=I_qdEKVV",
            },
            "comment": {
                "text": "Like strolling through an 8-bit flower field.\n\nGood melodies, fun use of the sample site!\n\nGood job!",
                "url": "http://fiftyninety.fawmers.org/song/41558#comment-2422",
            },
        },
        {
            "source": "50/90",
            "url": "http://fiftyninety.fawmers.org/song/41558",
            "color": "#284ead",
            "id": "fiftyninety:2538",
            "timestamp": "2019-12-30T11:00:00+00:00",
            "user": {
                "name": "RalphCarl",
                "url": "http://fiftyninety.fawmers.org/user/ralphcarl",
                "image": "http://fiftyninety.fawmers.org/sites/default/files/styles/medium/public/pictures/picture-3826-1432234990.jpg?itok=JNJXoYWD",
            },
            "comment": {
                "text": "The rain throughout is great,and complements the upbeat music perfectly.",
                "url": "http://fiftyninety.fawmers.org/song/41558#comment-2538",
            },
        },
        {
            "source": "50/90",
            "url": "http://fiftyninety.fawmers.org/song/41558",
            "color": "#284ead",
            "id": "fiftyninety:3134",
            "timestamp": "2019-12-31T10:59:07+00:00",
            "user": {
                "name": "Mt.Mélodie",
                "url": "http://fiftyninety.fawmers.org/user/mtm%C3%A9lodie",
                "image": "http://fiftyninety.fawmers.org/sites/default/files/styles/medium/public/pictures/picture-446066-1499174878.jpg?itok=kz6xuWKr",
            },
            "comment": {
                "text": "Lots of nice sounds, a bit of blippy 8 bit summer chill out vibe, is the tape track a kind of tape delay thingies?",
                "url": "http://fiftyninety.fawmers.org/song/41558#comment-3134",
            },
        },
    ]
