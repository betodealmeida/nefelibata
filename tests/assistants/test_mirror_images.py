"""
Tests for ``nefelibata.assistants.mirror_images``.
"""
# pylint: disable=invalid-name, redefined-outer-name

from pathlib import Path
from typing import Dict

import pytest
from aiohttp import ClientSession
from pytest_mock import MockerFixture

from nefelibata.assistants.mirror_images import (
    MirrorImagesAssistant,
    add_exif,
    download_image,
    extract_images,
    get_filename,
    get_resource_extension,
    is_local,
)
from nefelibata.config import Config
from nefelibata.post import Post


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
        "nefelibata.assistants.mirror_images.download_image",
        return_value=mocker.AsyncMock(),
    )

    assistant = MirrorImagesAssistant(root, config)

    post.content = """
I have 2 images:

- ![First image](https://example.com/photo.jpg)
- ![Second image](img/logo.png)
    """

    await assistant.process_post(post)
    await assistant.process_post(post)

    async def modify_replacements(  # pylint: disable=too-many-arguments, unused-argument
        session: ClientSession,
        url: str,
        title: str,
        post: Post,
        mirror: Path,
        replacements: Dict[str, str],
    ) -> None:
        """
        A dummy function to modify ``replacements``.
        """
        replacements["hello"] = "world"

    mocker.patch(
        "nefelibata.assistants.mirror_images.download_image",
        modify_replacements,
    )

    await assistant.process_post(post)


def test_extract_images() -> None:
    """
    Test ``extract_images``.
    """

    assert list(extract_images("No images here, move along")) == []

    content = """
This is a long document with ![A title](https://example.com/photo.jpg).
    """
    assert list(extract_images(content)) == [
        ("https://example.com/photo.jpg", "A title"),
    ]


def test_is_local() -> None:
    """
    Test ``is_local``.
    """
    assert not is_local("https://example.com/photo.jpg")
    assert is_local("img/logo.png")


@pytest.mark.asyncio
async def test_get_resource_extension(mocker: MockerFixture) -> None:
    """
    Test ``get_resource_extension``.
    """
    session = mocker.MagicMock()
    session.head.return_value.__aenter__.return_value.headers = {
        "content-type": "image/jpeg",
    }

    extension = await get_resource_extension(session, "https://example.com/photo.jpg")
    assert extension == ".jpg"


def test_get_filename() -> None:
    """
    Test ``get_filename``.
    """
    assert (
        get_filename("https://example.com/photo.jpg", ".jpg")
        == "39c18449612764d8d87663444426c037.jpg"
    )


def test_add_exif(mocker: MockerFixture) -> None:
    """
    Test ``add_exif``.
    """
    BytesIO = mocker.patch("nefelibata.assistants.mirror_images.BytesIO")
    Image = mocker.patch("nefelibata.assistants.mirror_images.Image")
    piexif = mocker.patch("nefelibata.assistants.mirror_images.piexif")

    buf = BytesIO()
    add_exif(buf, "https://example.com/photo.jpg", "A title")

    piexif.dump.assert_called_with(
        {
            "0th": {
                piexif.ImageIFD.Copyright: "https://example.com/photo.jpg",
                piexif.ImageIFD.ImageDescription: "A title",
            },
        },
    )
    Image.open.return_value.save.assert_called_with(
        BytesIO.return_value,
        "jpeg",
        exif=piexif.dump.return_value,
    )


@pytest.mark.asyncio
async def test_download_image(mocker: MockerFixture, post: Post) -> None:
    """
    Test ``download_image``.
    """
    # mock network calls
    session = mocker.MagicMock()
    session.head.return_value.__aenter__.return_value.headers = {
        "content-type": "image/jpeg",
    }
    response = session.get.return_value.__aenter__.return_value = mocker.MagicMock()
    response.content.iter_chunked.return_value.__aiter__.return_value = [
        b"hello",
        b" ",
        b"world",
    ]

    # mock image manipulation
    add_exif = mocker.patch("nefelibata.assistants.mirror_images.add_exif")
    add_exif.return_value.getvalue.return_value = b"Hello"
    BytesIO = mocker.patch("nefelibata.assistants.mirror_images.BytesIO")

    _logger = mocker.patch("nefelibata.assistants.mirror_images._logger")

    mirror = post.path.parent / "img"
    mirror.mkdir()
    replacements: Dict[str, str] = {}

    # simple call
    await download_image(
        session,
        "https://example.com/photo.jpg",
        "A title",
        post,
        mirror,
        replacements,
    )
    assert (mirror / "39c18449612764d8d87663444426c037.jpg").exists()
    add_exif.assert_called_with(
        BytesIO.return_value,
        "https://example.com/photo.jpg",
        "A title",
    )
    assert replacements == {
        "https://example.com/photo.jpg": "img/39c18449612764d8d87663444426c037.jpg",
    }
    _logger.info.assert_called_with(
        "Downloading image from %s",
        "https://example.com/photo.jpg",
    )

    # call again
    await download_image(
        session,
        "https://example.com/photo.jpg",
        "A title",
        post,
        mirror,
        replacements,
    )
    _logger.debug.assert_called_with("Image already mirrored")

    # no EXIF
    session.head.return_value.__aenter__.return_value.headers = {
        "content-type": "image/png",
    }
    BytesIO.return_value.getvalue.return_value = b"Hello"
    add_exif.reset_mock()
    await download_image(
        session,
        "https://example.com/logo.png",
        "A title",
        post,
        mirror,
        replacements,
    )
    add_exif.assert_not_called()
