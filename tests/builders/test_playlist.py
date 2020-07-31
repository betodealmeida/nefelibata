from datetime import datetime
from datetime import timezone
from pathlib import Path

from freezegun import freeze_time
from mutagen import id3
from nefelibata.builders.playlist import PlaylistBuilder

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


config = {"url": "https://example.com/"}


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self


def test_playlist(mock_post, mocker, fs):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!
        """,
        )

    builder = PlaylistBuilder(root, config)

    # create 2 empty "MP3" files
    fs.create_file(post.file_path.parent / "demo1.mp3")
    fs.create_file(post.file_path.parent / "demo2.mp3")

    mocker.patch(
        "nefelibata.builders.playlist.MP3",
        side_effect=[
            AttrDict(
                {
                    "TIT2": "Title 1",
                    "TPE1": "Famous Artist",
                    "TALB": "Some Album",
                    "TDRC": 2020,
                    "info": AttrDict(length=60),
                    "TRCK": id3.TRCK(encoding=id3.Encoding.LATIN1, text=["3"]),
                },
            ),
            AttrDict(
                {
                    "TIT2": "Title 2",
                    "TPE1": "Famous Artist",
                    "TALB": "Some Album",
                    "TDRC": 2020,
                    "info": AttrDict(length=45),
                },
            ),
        ],
    )

    builder.process_post(post)

    with open(post.file_path.parent / "index.pls") as fp:
        contents = fp.read()

    assert (
        contents
        == """
[playlist]

NumberOfEntries=2
Version=2

File1=https://example.com/first/demo2.mp3
Title1=Some Album (2020) - Famous Artist - Title 2
Length1=45

File2=https://example.com/first/demo1.mp3
Title2=Some Album (2020) - Famous Artist - Title 1
Length2=60
    """.strip()
    )


def test_playlist_no_files(mock_post, mocker, fs):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!
        """,
        )

    builder = PlaylistBuilder(root, config)
    builder.process_post(post)

    assert not (post.file_path.parent / "index.pls").exists()


def test_playlist_not_modified(mock_post, mocker, fs):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!
        """,
        )

    builder = PlaylistBuilder(root, config)

    # create 2 empty "MP3" files
    fs.create_file(post.file_path.parent / "demo1.mp3")
    fs.create_file(post.file_path.parent / "demo2.mp3")

    mocker.patch(
        "nefelibata.builders.playlist.MP3",
        side_effect=[
            AttrDict(
                {
                    "TIT2": "Title 1",
                    "TPE1": "Famous Artist",
                    "TALB": "Some Album",
                    "TDRC": 2020,
                    "info": AttrDict(length=60),
                    "TRCK": id3.TRCK(encoding=id3.Encoding.LATIN1, text=["3"]),
                },
            ),
            AttrDict(
                {
                    "TIT2": "Title 2",
                    "TPE1": "Famous Artist",
                    "TALB": "Some Album",
                    "TDRC": 2020,
                    "info": AttrDict(length=45),
                },
            ),
        ],
    )

    pls_path = post.file_path.parent / "index.pls"
    contents = """
[playlist]

NumberOfEntries=2
Version=2

File1=https://example.com/first/demo2.mp3
Title1=Some Album (2020) - Famous Artist - Title 2
Length1=45

File2=https://example.com/first/demo1.mp3
Title2=Some Album (2020) - Famous Artist - Title 1
Length2=60
    """.strip()
    with freeze_time("2020-01-01T00:00:00Z"):
        with open(pls_path, "w") as fp:
            fp.write(contents)

    builder.process_post(post)

    # file shouldn't have been touched
    assert datetime.fromtimestamp(pls_path.stat().st_mtime).astimezone(
        timezone.utc,
    ) == datetime(2020, 1, 1, 0, 0, tzinfo=timezone.utc)


def test_playlist_modified(mock_post, mocker, fs):
    root = Path("/path/to/blog")

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!
        """,
        )

    builder = PlaylistBuilder(root, config)

    # create 2 empty "MP3" files
    fs.create_file(post.file_path.parent / "demo1.mp3")
    fs.create_file(post.file_path.parent / "demo2.mp3")

    mocker.patch(
        "nefelibata.builders.playlist.MP3",
        side_effect=[
            AttrDict(
                {
                    "TIT2": "Title 1",
                    "TPE1": "Famous Artist",
                    "TALB": "Some Album",
                    "TDRC": 2020,
                    "info": AttrDict(length=60),
                    "TRCK": id3.TRCK(encoding=id3.Encoding.LATIN1, text=["3"]),
                },
            ),
            AttrDict(
                {
                    "TIT2": "Title 2",
                    "TPE1": "Famous Artist",
                    "TALB": "Some Album",
                    "TDRC": 2020,
                    "info": AttrDict(length=45),
                },
            ),
        ],
    )

    pls_path = post.file_path.parent / "index.pls"
    contents = """
[playlist]

NumberOfEntries=2
Version=2

File1=https://example.com/first/demo2.mp3
Title1=Some Album (2020) - Famous Artist - Title 2
Length1=45
    """.strip()
    with freeze_time("2020-01-01T00:00:00Z"):
        with open(pls_path, "w") as fp:
            fp.write(contents)

    with freeze_time("2020-01-02T00:00:00Z"):
        builder.process_post(post)

    # file should have been touched
    assert datetime.fromtimestamp(pls_path.stat().st_mtime).astimezone(
        timezone.utc,
    ) == datetime(2020, 1, 2, 0, 0, tzinfo=timezone.utc)
