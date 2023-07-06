"""
Tests for ``nefelibata.assistants.exif_description``.
"""

from pathlib import Path
from typing import Any, Dict

import pytest
from piexif import InvalidImageDataError
from pytest_mock import MockerFixture

from nefelibata.assistants.exif_description import (
    ExifDescriptionAssistant,
    get_image_description,
)
from nefelibata.config import Config
from nefelibata.enclosure import ImageEnclosure, MP3Enclosure
from nefelibata.post import Post


@pytest.mark.asyncio
async def test_get_image_description(post: Post) -> None:
    """
    Test the ``get_image_description`` function..
    """
    post.content = """
I have 2 images:

- ![First image](https://example.com/photo.jpg)
- ![Second image](img/logo.png)
    """

    assert (
        get_image_description(post, post.path.parent / "img/logo.png") == "Second image"
    )


@pytest.mark.asyncio
async def test_assistant(
    mocker: MockerFixture,
    root: Path,
    config: Config,
    post: Post,
) -> None:
    """
    Test the assistant.
    """
    mocker.patch(
        "nefelibata.assistants.exif_description.get_image_description",
        side_effect=[
            "Description of an image",
            None,
            "Description of another image",
        ],
    )
    piexif = mocker.patch("nefelibata.assistants.exif_description.piexif")
    exif: Dict[str, Any] = {"0th": {}}
    piexif.load.side_effect = [
        exif,
        InvalidImageDataError("Invalid data"),
    ]

    assistant = ExifDescriptionAssistant(root, config)

    post.content = """
I have 2 images:

- ![First image](https://example.com/photo.jpg)
- ![Second image](img/logo.png)
    """
    post.enclosures = [
        ImageEnclosure(
            path=post.path.parent / "img/logo.png",
            description="Image logo.png",
            type="image/jpeg",
            length=1234,
            href="img/logo.png",
        ),
        MP3Enclosure(
            path=post.path.parent / "audio/track.mp3",
            description="Audio track.mp3",
            length=1234,
            href="audio/track.mp3",
            title="Track",
            artist="Artist",
            album="Album",
            year=2021,
            duration=1234.5,
            track=1,
        ),
        ImageEnclosure(
            path=post.path.parent / "img/no_description.png",
            description="Image no_description.png",
            type="image/jpeg",
            length=1234,
            href="img/no_description.png",
        ),
        ImageEnclosure(
            path=post.path.parent / "img/no_exif_data.png",
            description="Image no_exif_data.png",
            type="image/jpeg",
            length=1234,
            href="img/no_exif_data.png",
        ),
    ]

    await assistant.process_post(post)

    piexif.load.assert_has_calls(
        [
            mocker.call("/path/to/blog/posts/first/img/logo.png"),
            mocker.call("/path/to/blog/posts/first/img/no_exif_data.png"),
        ],
    )
    piexif.insert.assert_called_once_with(
        piexif.dump(),
        "/path/to/blog/posts/first/img/logo.png",
    )
    assert exif == {
        "0th": {
            piexif.ImageIFD.ImageDescription: b"Description of an image",
        },
    }
