from freezegun import freeze_time
from nefelibata.assistants.playlist import PlaylistAssistant

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self


def test_playlist(mock_post, mocker, fs):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!
        """,
        )

    config = {"url": "https://example.com/"}
    assistant = PlaylistAssistant(post.root, config)

    # create 2 empty "MP3" files
    fs.create_file(post.file_path.parent / "demo1.mp3")
    fs.create_file(post.file_path.parent / "demo2.mp3")

    mocker.patch(
        "nefelibata.assistants.playlist.MP3",
        side_effect=[
            AttrDict(
                {
                    "TIT2": "Title 1",
                    "TPE1": "Famous Artist",
                    "TALB": "Some Album",
                    "TDRC": 2020,
                    "info": AttrDict(length=60),
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

    assistant.process_post(post)

    with open(post.file_path.parent / "index.pls") as fp:
        contents = fp.read()

    assert (
        contents
        == """
[playlist]

NumberOfEntries=2
Version=2

File1=https://example.com/first/demo1.mp3
Title1=Some Album (2020) - Famous Artist - Title 1
Length1=60

File2=https://example.com/first/demo2.mp3
Title2=Some Album (2020) - Famous Artist - Title 2
Length2=45
    """.strip()
    )


def test_playlist_no_files(mock_post, mocker, fs):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, World!
        keywords: test
        summary: My first post

        Hi, there!
        """,
        )

    config = {"url": "https://example.com/"}
    assistant = PlaylistAssistant(post.root, config)

    assistant.process_post(post)

    assert not (post.file_path.parent / "index.pls").exists()
