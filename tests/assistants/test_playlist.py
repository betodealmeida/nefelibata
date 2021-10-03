"""
Tests for ``nefelibata.assistants.playlist``.
"""

from datetime import datetime, timezone
from pathlib import Path

import pytest
from freezegun import freeze_time

from nefelibata.assistants.playlist import PlaylistAssistant
from nefelibata.config import Config
from nefelibata.enclosure import MP3Enclosure
from nefelibata.post import Post


@pytest.mark.asyncio
async def test_assistant(root: Path, config: Config, post: Post) -> None:
    """
    Test the assistant.
    """
    assistant = PlaylistAssistant(root, config, base_url="https://example.com/mp3s/")

    index_path = post.path.parent / "index.pls"

    await assistant.process_post(post)
    assert not index_path.exists()

    post.enclosures.append(
        MP3Enclosure(
            path=root / "posts/first/song.mp3",
            description='"A title" (2m3s) by An artist (An album, 2021)',
            type="audio/mpeg",
            length=666,
            href="first/song.mp3",
            title="A title",
            artist="An artist",
            album="An album",
            year=2021,
            duration=123,
            track=0,
        ),
    )

    with freeze_time("2021-01-01T00:00:00Z"):
        await assistant.process_post(post)
    assert (
        index_path.stat().st_mtime
        == datetime(2021, 1, 1, tzinfo=timezone.utc).timestamp()
    )

    with open(index_path, encoding="utf-8") as input_:
        content = input_.read()
    assert (
        content
        == """[playlist]

NumberOfEntries=1
Version=2

File1=https://example.com/mp3s/first/song.mp3
Title1="A title" (2m3s) by An artist (An album, 2021)
Length1=123.0

"""
    )

    with freeze_time("2021-01-02T00:00:00Z"):
        await assistant.process_post(post)
    assert (
        index_path.stat().st_mtime
        == datetime(2021, 1, 1, tzinfo=timezone.utc).timestamp()
    )

    with freeze_time("2021-01-03T00:00:00Z"):
        await assistant.process_post(post, force=True)
    assert (
        index_path.stat().st_mtime
        == datetime(2021, 1, 3, tzinfo=timezone.utc).timestamp()
    )
