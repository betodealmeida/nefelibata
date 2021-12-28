"""
Tests for ``nefelibata.announcers.mastodon``.
"""
# pylint: disable=invalid-name

from datetime import datetime, timezone
from pathlib import Path

import pytest
from mastodon import MastodonNotFoundError
from pytest_mock import MockerFixture

from nefelibata.announcers.base import Author, Interaction
from nefelibata.announcers.mastodon import MastodonAnnouncer
from nefelibata.builders.base import Builder
from nefelibata.config import Config
from nefelibata.enclosure import Enclosure
from nefelibata.post import Post


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

    Mastodon = mocker.patch("nefelibata.announcers.mastodon.Mastodon")
    Mastodon.return_value.status_post.return_value.url = "https://example.com/1"
    Mastodon.return_value.status_post.return_value.created_at = datetime(
        2021,
        1,
        1,
        tzinfo=timezone.utc,
    )

    announcer = MastodonAnnouncer(
        root,
        config,
        builders=[gemini_builder, html_builder],
        access_token="access_token",
        base_url="https://example.com/",
    )

    enclosure_path = post.path.parent / "picture.jpg"
    enclosure_path.touch()
    post.enclosures.append(
        Enclosure(
            path=enclosure_path,
            description="A photo",
            type="image/jpeg",
            length=666,
            href="first/picture.jpg",
        ),
    )

    announcement = await announcer.announce_post(post)
    assert announcement.dict() == {
        "url": "https://example.com/1",
        "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
        "grace_seconds": 0,
    }

    Mastodon.return_value.media_post.assert_called_with(
        str(enclosure_path),
        "image/jpeg",
        "A photo",
    )
    Mastodon.return_value.status_post.assert_called_with(
        status="""Hello, world!

gemini://example.com/first/index.gmi
https://example.com/first/index.html""",
        visibility="public",
        media_ids=[Mastodon.return_value.media_post.return_value],
        language="en",
        idempotency_key=str(post.path),
    )


@pytest.mark.asyncio
async def test_announcer_announce_multiple_enclosures(
    mocker: MockerFixture,
    root: Path,
    config: Config,
    post: Post,
) -> None:
    """
    Test announcing posts with 4+ enclosures.
    """
    gemini_builder = Builder(root, config, "gemini://example.com/", "gemini")
    gemini_builder.extension = ".gmi"

    Mastodon = mocker.patch("nefelibata.announcers.mastodon.Mastodon")
    Mastodon.return_value.status_post.return_value.url = "https://example.com/1"
    Mastodon.return_value.status_post.return_value.created_at = datetime(
        2021,
        1,
        1,
        tzinfo=timezone.utc,
    )
    _logger = mocker.patch("nefelibata.announcers.mastodon._logger")

    announcer = MastodonAnnouncer(
        root,
        config,
        builders=[gemini_builder],
        access_token="access_token",
        base_url="https://example.com/",
    )

    for i in range(5):
        enclosure_path = post.path.parent / f"picture{i}.jpg"
        enclosure_path.touch()
        post.enclosures.append(
            Enclosure(
                path=enclosure_path,
                description=f"Photo #{i}",
                type="image/jpeg",
                length=666,
                href=f"first/picture{i}.jpg",
            ),
        )

    await announcer.announce_post(post)

    _logger.warning.assert_called_with(
        "Found more than %d media enclosures in post %s. Only the first "
        "%d will be uploaded.",
        4,
        post.path,
        4,
    )


@pytest.mark.asyncio
async def test_announcer_collect(
    mocker: MockerFixture,
    root: Path,
    config: Config,
    post: Post,
) -> None:
    """
    Test collecting interactions on a given post.
    """
    Mastodon = mocker.patch("nefelibata.announcers.mastodon.Mastodon")
    Mastodon.return_value.status_context.return_value = {
        "descendants": [
            {
                "uri": "https://example.com/2",
                "id": 2,
                "url": "https://example.com/2",
                "content": "This is a reply",
                "created_at": datetime(2021, 1, 1),
                "account": {
                    "display_name": "Alice Doe",
                    "url": "https://alice.example.com/",
                    "avatar": "https://alice.example.com/profile.gif",
                    "note": "Best friends with Bob and Charlie",
                },
                "in_reply_to_id": 1,
            },
        ],
    }

    announcer = MastodonAnnouncer(
        root,
        config,
        builders=[],
        access_token="access_token",
        base_url="https://example.com/",
    )

    post.metadata["announcements"] = {
        "mastodon": {
            "url": "https://example.com/1",
        },
        "something": {
            "url": "https://foo.example.com/",
        },
    }

    interactions = await announcer.collect_post(post)
    assert interactions == {
        "https://example.com/2": Interaction(
            id="https://example.com/2",
            name="https://example.com/2",
            summary=None,
            content="This is a reply",
            published=datetime(2021, 1, 1, 0, 0),
            updated=None,
            author=Author(
                name="Alice Doe",
                url="https://alice.example.com/",
                avatar="https://alice.example.com/profile.gif",
                note="Best friends with Bob and Charlie",
            ),
            url="https://example.com/2",
            in_reply_to="https://example.com/1",
            type="reply",
        ),
    }


@pytest.mark.asyncio
async def test_announcer_collect_not_found(
    mocker: MockerFixture,
    root: Path,
    config: Config,
    post: Post,
) -> None:
    """
    Test collecting interactions when post has been deleted.
    """
    Mastodon = mocker.patch("nefelibata.announcers.mastodon.Mastodon")
    Mastodon.return_value.status_context.side_effect = MastodonNotFoundError(
        "Not found",
    )
    _logger = mocker.patch("nefelibata.announcers.mastodon._logger")

    announcer = MastodonAnnouncer(
        root,
        config,
        builders=[],
        access_token="access_token",
        base_url="https://example.com/",
    )

    post.metadata["announcements"] = {
        "mastodon": {
            "url": "https://example.com/1",
        },
    }

    interactions = await announcer.collect_post(post)
    assert interactions == {}

    _logger.warning.assert_called_with("Toot %s not found", "https://example.com/1")
