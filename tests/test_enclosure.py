"""
Tests for ``nefelibata.enclosure``.
"""
# pylint: disable=invalid-name

from pathlib import Path

from pyfakefs.fake_filesystem import FakeFilesystem
from pytest_mock import MockerFixture

from nefelibata.enclosure import get_enclosures, get_pretty_duration


def test_get_pretty_duration() -> None:
    """
    Test ``get_pretty_duration``.
    """
    assert get_pretty_duration(0) == "0s"
    assert get_pretty_duration(1) == "1s"
    assert get_pretty_duration(60) == "1m"
    assert get_pretty_duration(61) == "1m1s"
    assert get_pretty_duration(120) == "2m"
    assert get_pretty_duration(121) == "2m1s"
    assert get_pretty_duration(3600) == "1h"
    assert get_pretty_duration(3601) == "1h0m1s"


def test_get_enclosures(mocker: MockerFixture, fs: FakeFilesystem, root: Path) -> None:
    """
    Test ``get_enclosures``.
    """
    MP3 = mocker.patch("nefelibata.enclosure.MP3")
    metadata = {
        "TIT2": "A title",
        "TPE1": "An artist",
        "TALB": "An album",
        "TDRC": 2021,
        "TRCK": 1,
    }
    MP3.return_value.get.side_effect = metadata.get
    MP3.return_value.info.length = 123.0

    piexif = mocker.patch("nefelibata.enclosure.piexif")
    piexif.ImageIFD.ImageDescription = 270
    piexif.load.return_value = {"0th": {270: "This is a nice photo"}}

    fs.create_dir(root / "posts/first")
    path = root / "posts/first/index.mkd"

    # create supported files
    (root / "posts/first/song.mp3").touch()
    (root / "posts/first/photo.jpg").touch()
    (root / "posts/first/logo.png").touch()

    # create non-supported file
    (root / "posts/first/test.txt").touch()

    enclosures = get_enclosures(root, path.parent)
    assert len(enclosures) == 3

    assert enclosures[0].dict() == {
        "path": Path("/path/to/blog/posts/first/song.mp3"),
        "description": '"A title" (2m3s) by An artist (An album, 2021)',
        "type": "audio/mpeg",
        "length": 0,
        "href": "first/song.mp3",
        "title": "A title",
        "artist": "An artist",
        "album": "An album",
        "year": 2021,
        "duration": 123.0,
        "track": 0,
    }

    assert enclosures[1].dict() == {
        "description": "This is a nice photo",
        "href": "first/photo.jpg",
        "length": 0,
        "path": Path("/path/to/blog/posts/first/photo.jpg"),
        "type": "image/jpeg",
    }

    assert enclosures[2].dict() == {
        "description": "Image logo.png",
        "href": "first/logo.png",
        "length": 0,
        "path": Path("/path/to/blog/posts/first/logo.png"),
        "type": "image/png",
    }
