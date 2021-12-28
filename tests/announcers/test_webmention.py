"""
Tests for ``nefelibata.announcers.mastodon``.
"""
# pylint: disable=invalid-name, redefined-outer-name

from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml
from freezegun import freeze_time
from pytest_mock import MockerFixture
from yarl import URL

from nefelibata.announcers.base import Announcement, Author, Interaction
from nefelibata.announcers.webmention import (
    Webmention,
    WebmentionAnnouncer,
    get_webmention_endpoint,
    send_webmention,
    update_webmention,
)
from nefelibata.builders.base import Builder
from nefelibata.config import Config
from nefelibata.post import Post


@pytest.mark.asyncio
async def test_get_webmention_endpoint(mocker: MockerFixture) -> None:
    """
    Test ``get_webmention_endpoint``.
    """
    session = mocker.MagicMock()
    head_response = session.head.return_value.__aenter__.return_value
    head_response.headers = {
        "content-type": "text/html",
    }
    head_response.links = {
        "alternate": {
            "url": "/atom.xml",
        },
        "webmention": {
            "url": "/webmention.php",
        },
    }
    get_response = session.get.return_value.__aenter__.return_value
    get_response.text = mocker.AsyncMock()
    get_response.text.return_value = """<!doctype html>
<html lang="en">
  <head>
    <link rel="webmention" href="/webmention.php" />
  </head>
  <body>
  </body>
</html>"""

    # endpoint in Link header
    endpoint = await get_webmention_endpoint(
        session,
        URL("https://example.com/post/hello.php"),
    )
    assert endpoint == URL("https://example.com/webmention.php")

    # endpoint in HTML
    head_response.links = {}
    endpoint = await get_webmention_endpoint(
        session,
        URL("https://example.com/post/hello.php"),
    )
    assert endpoint == URL("https://example.com/webmention.php")

    # no endpoint in HTML
    get_response.text.return_value = """<!doctype html>
<html lang="en">
  <head>
  </head>
  <body>
  </body>
</html>"""
    endpoint = await get_webmention_endpoint(
        session,
        URL("https://example.com/post/hello.php"),
    )
    assert endpoint is None

    # unable to extract endpoint
    head_response.headers = {
        "content-type": "application/pdf",
    }
    endpoint = await get_webmention_endpoint(
        session,
        URL("https://example.com/post/hello.php"),
    )
    assert endpoint is None

    # gemini target
    head_response.links = {}
    endpoint = await get_webmention_endpoint(
        session,
        URL("gemini://example.com/post/hello.gmi"),
    )
    assert endpoint is None


@pytest.mark.asyncio
async def test_get_webmention_endpoint_unicode_error(mocker: MockerFixture) -> None:
    """
    Test ``get_webmention_endpoint`` when response is not text.
    """
    session = mocker.MagicMock()
    head_response = session.head.return_value.__aenter__.return_value
    head_response.headers = {
        "content-type": "text/html",
    }
    head_response.links = {}
    mocker.patch("nefelibata.announcers.webmention.UnicodeDecodeError", Exception)
    get_response = session.get.return_value.__aenter__.return_value
    get_response.text = mocker.AsyncMock()
    get_response.text.side_effect = Exception()

    endpoint = await get_webmention_endpoint(
        session,
        URL("https://example.com/post/hello.php"),
    )
    assert endpoint is None


@pytest.mark.asyncio
async def test_send_webmention(mocker: MockerFixture) -> None:
    """
    Test ``send_webmention``.
    """
    session = mocker.MagicMock()
    post_response = session.post.return_value.__aenter__.return_value
    post_response.raise_for_status = mocker.MagicMock()
    post_response.raise_for_status.return_value = None

    source = URL("https://alice.example.com/posts/one")
    target = URL("https://bob.example.com/posts/two")

    # no endpoint
    mocker.patch(
        "nefelibata.announcers.webmention.get_webmention_endpoint",
        return_value=None,
    )
    webmention = await send_webmention(session, source, target)
    assert webmention.dict() == {
        "source": "https://alice.example.com/posts/one",
        "target": "https://bob.example.com/posts/two",
        "status": "invalid",
        "location": None,
    }

    # 200 OK
    mocker.patch(
        "nefelibata.announcers.webmention.get_webmention_endpoint",
        return_value=URL("//bob.example.com/webmention.php"),
    )
    post_response.status = 200
    webmention = await send_webmention(session, source, target)
    assert webmention.dict() == {
        "source": "https://alice.example.com/posts/one",
        "target": "https://bob.example.com/posts/two",
        "status": "success",
        "location": None,
    }

    # 201 CREATED
    post_response.status = 201
    post_response.headers = {"location": "https://bob.example.com/webmention.php?id=42"}
    webmention = await send_webmention(session, source, target)
    assert webmention.dict() == {
        "source": "https://alice.example.com/posts/one",
        "target": "https://bob.example.com/posts/two",
        "status": "queue",
        "location": "https://bob.example.com/webmention.php?id=42",
    }

    # 202 ACCEPTED
    post_response.status = 202
    webmention = await send_webmention(session, source, target)
    assert webmention.dict() == {
        "source": "https://alice.example.com/posts/one",
        "target": "https://bob.example.com/posts/two",
        "status": "success",
        "location": None,
    }

    # error
    post_response.raise_for_status.side_effect = Exception("Error")
    mocker.patch("nefelibata.announcers.webmention.ClientResponseError", Exception)
    webmention = await send_webmention(session, source, target)
    assert webmention.dict() == {
        "source": "https://alice.example.com/posts/one",
        "target": "https://bob.example.com/posts/two",
        "status": "error",
        "location": None,
    }


@pytest.mark.asyncio
async def test_update_webmention(mocker: MockerFixture) -> None:
    """
    Test ``update_webmention``.
    """
    session = mocker.MagicMock()
    get_response = session.get.return_value.__aenter__.return_value

    source = URL("https://alice.example.com/posts/one")
    target = URL("https://bob.example.com/posts/two")
    location = URL("https://bob.example.com/webmention.php?id=42")

    get_response.ok = True
    webmention = await update_webmention(session, source, target, location)
    assert webmention.dict() == {
        "source": "https://alice.example.com/posts/one",
        "target": "https://bob.example.com/posts/two",
        "status": "success",
        "location": None,
    }

    get_response.ok = False
    webmention = await update_webmention(session, source, target, location)
    assert webmention.dict() == {
        "source": "https://alice.example.com/posts/one",
        "target": "https://bob.example.com/posts/two",
        "status": "queue",
        "location": None,
    }


@pytest.mark.asyncio
async def test_announcer_announce(
    mocker: MockerFixture,
    root: Path,
    config: Config,
    post: Post,
) -> None:
    """
    Test announcing posts.
    """
    gemini_builder = Builder(root, config, "gemini://example.com/", "gemini")
    gemini_builder.extension = ".gmi"
    html_builder = Builder(root, config, "https://example.com/", "www")
    html_builder.extension = ".html"

    send_webmention = mocker.AsyncMock(
        side_effect=[
            Webmention(
                source="gemini://example.com/first/index.html",
                target="https://nefelibata.readthedocs.io/",
                status="invalid",
            ),
            Webmention(
                source="https://example.com/first/index.html",
                target="https://nefelibata.readthedocs.io/",
                status="queue",
                location="https://bob.example.com/webmention.php?id=42",
            ),
        ],
    )
    mocker.patch("nefelibata.announcers.webmention.send_webmention", send_webmention)

    announcer = WebmentionAnnouncer(
        root,
        config,
        builders=[gemini_builder, html_builder],
    )

    announcement = await announcer.announce_post(post)
    assert announcement is None

    path = post.path.parent / "webmentions.yaml"
    with open(path, encoding="utf-8") as input_:
        webmentions = yaml.load(input_, Loader=yaml.SafeLoader)
    assert webmentions == {
        "gemini://example.com/first/index.gmi => https://nefelibata.readthedocs.io/": {
            "location": None,
            "source": "gemini://example.com/first/index.html",
            "status": "invalid",
            "target": "https://nefelibata.readthedocs.io/",
        },
        "https://example.com/first/index.html => https://nefelibata.readthedocs.io/": {
            "location": "https://bob.example.com/webmention.php?id=42",
            "source": "https://example.com/first/index.html",
            "status": "queue",
            "target": "https://nefelibata.readthedocs.io/",
        },
    }

    update_webmention = mocker.AsyncMock(
        return_value=Webmention(
            source="https://example.com/first/index.html",
            target="https://nefelibata.readthedocs.io/",
            status="success",
            location=None,
        ),
    )
    mocker.patch(
        "nefelibata.announcers.webmention.update_webmention",
        update_webmention,
    )

    with freeze_time("2021-01-01T00:00:00Z"):
        announcement = await announcer.announce_post(post)
    assert announcement == Announcement(
        url="first/index",
        timestamp=datetime(2021, 1, 1, tzinfo=timezone.utc),
        grace_seconds=0,
    )

    path = post.path.parent / "webmentions.yaml"
    with open(path, encoding="utf-8") as input_:
        webmentions = yaml.load(input_, Loader=yaml.SafeLoader)
    assert webmentions == {
        "gemini://example.com/first/index.gmi => https://nefelibata.readthedocs.io/": {
            "location": None,
            "source": "gemini://example.com/first/index.html",
            "status": "invalid",
            "target": "https://nefelibata.readthedocs.io/",
        },
        "https://example.com/first/index.html => https://nefelibata.readthedocs.io/": {
            "location": None,
            "source": "https://example.com/first/index.html",
            "status": "success",
            "target": "https://nefelibata.readthedocs.io/",
        },
    }


@pytest.mark.asyncio
async def test_announcer_collect(
    mocker: MockerFixture,
    root: Path,
    config: Config,
    post: Post,
) -> None:
    """
    Test collecting posts.
    """
    gemini_builder = Builder(root, config, "gemini://example.com/", "gemini")
    gemini_builder.extension = ".gmi"
    html_builder = Builder(root, config, "https://example.com/", "www")
    html_builder.extension = ".html"

    mocker.patch("nefelibata.announcers.webmention.ClientResponseError", Exception)
    get = mocker.patch("nefelibata.announcers.webmention.ClientSession.get")
    get_response = get.return_value.__aenter__.return_value
    get_response.raise_for_status = mocker.MagicMock()
    get_response.raise_for_status.side_effect = [
        Exception("Gemini not supported"),
        None,
        Exception("Gemini not supported"),
        None,
    ]

    announcer = WebmentionAnnouncer(
        root,
        config,
        builders=[gemini_builder, html_builder],
    )

    get_response.json = mocker.AsyncMock(return_value={"children": []})
    interactions = await announcer.collect_post(post)
    assert interactions == {}

    entries = [
        {
            "type": "entry",
            "wm-id": 1,
            "wm-source": "https://alice.example.com/posts/one",
            "name": "This is the title",
            "summary": {"value": "This is the summary"},
            "content": {"text": "This is the post content."},
            "published": "2021-01-01T00:00:00Z",
            "author": {
                "name": "Alice Doe",
                "url": "https://alice.example.com/",
                "photo": "https://alice.example.com/photo.jpg",
                "note": "My name is Alice",
            },
            "wm-property": "in-reply-to",
        },
        {
            "type": "entry",
            "wm-id": 2,
            "wm-source": "https://bob.example.com/posts/two",
            "summary": {"value": "This is the summary"},
            "content": {"text": "This is the post content."},
            "published": "2021-01-01T00:00:00Z",
            "author": {
                "name": "Bob Doe",
                "url": "https://bob.example.com/",
                "photo": "https://bob.example.com/photo.jpg",
            },
            "wm-property": "like-of",
        },
        {"type": "invalid"},
    ]

    get_response.json = mocker.AsyncMock(return_value={"children": entries})
    interactions = await announcer.collect_post(post)
    assert interactions == {
        1: Interaction(
            id="1",
            name="This is the title",
            summary="This is the summary",
            content="This is the post content.",
            published=datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            updated=None,
            author=Author(
                name="Alice Doe",
                url="https://alice.example.com/",
                avatar="https://alice.example.com/photo.jpg",
                note="My name is Alice",
            ),
            url="https://alice.example.com/posts/one",
            in_reply_to=None,
            type="reply",
        ),
        2: Interaction(
            id="2",
            name="https://bob.example.com/posts/two",
            summary="This is the summary",
            content="This is the post content.",
            published=datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
            updated=None,
            author=Author(
                name="Bob Doe",
                url="https://bob.example.com/",
                avatar="https://bob.example.com/photo.jpg",
                note="",
            ),
            url="https://bob.example.com/posts/two",
            in_reply_to=None,
            type="like",
        ),
    }
