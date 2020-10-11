import copy
import json
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from unittest.mock import MagicMock

from freezegun import freeze_time
from nefelibata.announcers import Announcer
from nefelibata.announcers import get_announcers
from nefelibata.announcers import Response
from nefelibata.post import Post

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


response1 = {
    "source": "Test",
    "url": "https://example.com/1",
    "color": "#ff0000",
    "id": "test:1",
    "timestamp": "2020-01-01T00:00:00Z",
    "user": {
        "name": "User",
        "image": "https://example.com/u/1/photo.jpg",
        "url": "https://example.com/u/1",
        "description": "I'm just a user.",
    },
    "comment": {"text": "Welcome!", "url": "https://example.com/1#c1"},
}

response2 = {
    "source": "Test",
    "url": "https://example.com/2",
    "color": "#ff0000",
    "id": "test:2",
    "timestamp": "2020-01-02T00:00:00Z",
    "user": {
        "name": "Another User",
        "image": "https://example.com/u/2/photo.jpg",
        "url": "https://example.com/u/2",
        "description": "I'm just another user.",
    },
    "comment": {"text": "Welcome!", "url": "https://example.com/2#c2"},
}

response3 = {
    "source": "Test",
    "url": "https://example.com/3",
    "color": "#ff0000",
    "id": "test:3",
    "timestamp": "2020-01-03T00:00:00Z",
    "user": {
        "name": "",
        "image": "",
        "url": "https://example.com/u/3",
        "description": "",
    },
    "comment": {"text": "Welcome!", "url": "https://example.com/3#c3"},
}


class MockAnnouncer(Announcer):

    id = "test"
    name = "Test"
    url_header = "test-url"

    def __init__(
        self,
        root: Path,
        config: Dict[str, Any],
        url: Optional[str] = None,
        responses: Optional[List[Response]] = None,
    ):
        super().__init__(root, config)

        self.url = url
        self.responses = responses or []

    def announce(self, post: Post) -> Optional[str]:
        return self.url

    def collect(self, post: Post) -> List[Response]:
        return self.responses


def make_dummy_announcer(name):
    return type("SomeAnnouncer", (Announcer,), {"name": name, "id": name.lower()})


class MockEntryPoint:
    def __init__(self, name: str, announcer: Announcer):
        self.name = name
        self.announcer = announcer

    def load(self) -> Announcer:
        return self.announcer


def test_update_links(mock_post):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, there!
        keywords: test
        summary: My first post
        announce-on: test

        Hi, there!
        """,
        )

    root = Path("/path/to/blog")
    config = {
        "url": "https://blog.example.com/",
        "language": "en",
    }
    announcer = MockAnnouncer(root, config, "https://example.com/", [])

    announcer.update_links(post)
    with open(post.file_path.parent / "links.json") as fp:
        contents = fp.read()
    links = json.loads(contents)
    assert links == {"Test": "https://example.com/"}


def test_update_links_already_announced(mock_post):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, there!
        keywords: test
        summary: My first post
        announce-on: test
        test-url: https://test.example.com

        Hi, there!
        """,
        )

    root = Path("/path/to/blog")
    config = {
        "url": "https://blog.example.com/",
        "language": "en",
    }
    announcer = MockAnnouncer(root, config, "https://example.com/", [])

    # add some initial content to the file
    contents = json.dumps({"Test": "https://test.example.com/"})
    with freeze_time("2020-01-01T00:00:00Z"):
        with open(post.file_path.parent / "links.json", "w") as fp:
            fp.write(contents)

    with freeze_time("2020-01-02T00:00:00Z"):
        announcer.update_links(post)

    assert datetime.fromtimestamp(
        (post.file_path.parent / "links.json").stat().st_mtime,
    ).astimezone(timezone.utc) == datetime(2020, 1, 1, 0, 0, tzinfo=timezone.utc)


def test_update_links_file_exists(mock_post):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, there!
        keywords: test
        summary: My first post
        announce-on: test

        Hi, there!
        """,
        )

    root = Path("/path/to/blog")
    config = {
        "url": "https://blog.example.com/",
        "language": "en",
    }
    announcer = MockAnnouncer(root, config, "https://example.com/", [])

    # add some initial content to the file
    contents = json.dumps({"Foo": "https://foo.example.com/"})
    with open(post.file_path.parent / "links.json", "w") as fp:
        fp.write(contents)

    announcer.update_links(post)
    with open(post.file_path.parent / "links.json") as fp:
        contents = fp.read()
    links = json.loads(contents)
    assert links == {"Test": "https://example.com/", "Foo": "https://foo.example.com/"}


def test_update_links_link_exists(mock_post):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, there!
        keywords: test
        summary: My first post
        announce-on: test

        Hi, there!
        """,
        )

    root = Path("/path/to/blog")
    config = {
        "url": "https://blog.example.com/",
        "language": "en",
    }
    announcer = MockAnnouncer(root, config, "https://example.com/", [])

    # add some initial content to the file
    contents = json.dumps({"Test": "https://example.com/"})
    with open(post.file_path.parent / "links.json", "w") as fp:
        fp.write(contents)

    announcer.update_links(post)
    with open(post.file_path.parent / "links.json") as fp:
        contents = fp.read()
    links = json.loads(contents)
    assert links == {"Test": "https://example.com/"}


def test_update_links_no_link(mock_post):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, there!
        keywords: test
        summary: My first post
        announce-on: test

        Hi, there!
        """,
        )

    root = Path("/path/to/blog")
    config = {
        "url": "https://blog.example.com/",
        "language": "en",
    }
    announcer = MockAnnouncer(root, config, None, [])

    announcer.update_links(post)
    assert not (post.file_path.parent / "links.json").exists()


def test_update_replies(mock_post):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, there!
        keywords: test
        summary: My first post
        announce-on: test
        test-url: https://example.com/

        Hi, there!
        """,
        )

    root = Path("/path/to/blog")
    config = {
        "url": "https://blog.example.com/",
        "language": "en",
    }
    announcer = MockAnnouncer(root, config, "https://example.com/", [response1])

    announcer.update_replies(post)
    with open(post.file_path.parent / "replies.json") as fp:
        contents = fp.read()
    replies = json.loads(contents)
    assert replies == [response1]


def test_update_replies_not_announced(mock_post):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, there!
        keywords: test
        summary: My first post
        announce-on: test

        Hi, there!
        """,
        )

    root = Path("/path/to/blog")
    config = {
        "url": "https://blog.example.com/",
        "language": "en",
    }
    announcer = MockAnnouncer(root, config, "https://example.com/", [])

    announcer.update_replies(post)
    assert not (post.file_path.parent / "replies.json").exists()


def test_update_replies_storage_exists(mock_post):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, there!
        keywords: test
        summary: My first post
        announce-on: test
        test-url: https://example.com/

        Hi, there!
        """,
        )

    root = Path("/path/to/blog")
    config = {
        "url": "https://blog.example.com/",
        "language": "en",
    }
    announcer = MockAnnouncer(root, config, "https://example.com/", [response1])

    # add some initial content to the file
    contents = json.dumps([response2])
    with open(post.file_path.parent / "replies.json", "w") as fp:
        fp.write(contents)

    announcer.update_replies(post)
    with open(post.file_path.parent / "replies.json") as fp:
        contents = fp.read()
    replies = json.loads(contents)
    # replies are showin in chronological order
    assert replies == [response1, response2]


def test_update_replies_no_overwrite(mock_post):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, there!
        keywords: test
        summary: My first post
        announce-on: test
        test-url: https://example.com/

        Hi, there!
        """,
        )

    root = Path("/path/to/blog")
    config = {
        "url": "https://blog.example.com/",
        "language": "en",
    }
    announcer = MockAnnouncer(root, config, "https://example.com/", [response1])

    # add some initial content to the file
    contents = json.dumps([response1])
    with open(post.file_path.parent / "replies.json", "w") as fp:
        fp.write(contents)

    announcer.update_replies(post)
    with open(post.file_path.parent / "replies.json") as fp:
        contents = fp.read()
    replies = json.loads(contents)
    # replies are showin in chronological order
    assert replies == [response1]


def test_update_replies_no_name_or_image(mock_post, mocker):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, there!
        keywords: test
        summary: My first post
        announce-on: test
        test-url: https://example.com/

        Hi, there!
        """,
        )

    root = Path("/path/to/blog")
    config = {
        "url": "https://blog.example.com/",
        "language": "en",
    }
    announcer = MockAnnouncer(root, config, "https://example.com/", [response3.copy()])

    # mf2py payload
    payload = {
        "items": [
            {"type": ["h-event"], "properties": {}},
            {
                "type": ["h-card"],
                "properties": {
                    "name": ["User"],
                    "photo": ["https://example.com/u/3/photo.jpg"],
                },
            },
            {"type": ["h-entry"], "properties": {}},
        ],
    }
    mock_mf2py = MagicMock()
    mock_mf2py.parse.return_value = payload
    mocker.patch("nefelibata.announcers.mf2py", mock_mf2py)

    announcer.update_replies(post)
    with open(post.file_path.parent / "replies.json") as fp:
        contents = fp.read()
    replies = json.loads(contents)
    assert replies == [
        {
            "source": "Test",
            "url": "https://example.com/3",
            "color": "#ff0000",
            "id": "test:3",
            "timestamp": "2020-01-03T00:00:00Z",
            "user": {
                "name": "User",
                "image": "https://example.com/u/3/photo.jpg",
                "url": "https://example.com/u/3",
                "description": "",
            },
            "comment": {"text": "Welcome!", "url": "https://example.com/3#c3"},
        },
    ]


def test_update_replies_no_name_or_image_no_hcard(mock_post, mocker):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, there!
        keywords: test
        summary: My first post
        announce-on: test
        test-url: https://example.com/

        Hi, there!
        """,
        )

    root = Path("/path/to/blog")
    config = {
        "url": "https://blog.example.com/",
        "language": "en",
    }
    announcer = MockAnnouncer(root, config, "https://example.com/", [response3.copy()])

    # mf2py payload
    payload = {
        "items": [{"type": ["h-event"], "properties": {}}],
    }
    mock_mf2py = MagicMock()
    mock_mf2py.parse.return_value = payload
    mocker.patch("nefelibata.announcers.mf2py", mock_mf2py)

    announcer.update_replies(post)
    with open(post.file_path.parent / "replies.json") as fp:
        contents = fp.read()
    replies = json.loads(contents)
    assert replies == [response3]


def test_update_replies_no_name_or_image_no_items(mock_post, mocker):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, there!
        keywords: test
        summary: My first post
        announce-on: test
        test-url: https://example.com/

        Hi, there!
        """,
        )

    root = Path("/path/to/blog")
    config = {
        "url": "https://blog.example.com/",
        "language": "en",
    }
    announcer = MockAnnouncer(root, config, "https://example.com/", [response3.copy()])

    # mf2py payload
    payload = {
        "items": [],
    }
    mock_mf2py = MagicMock()
    mock_mf2py.parse.return_value = payload
    mocker.patch("nefelibata.announcers.mf2py", mock_mf2py)

    announcer.update_replies(post)
    with open(post.file_path.parent / "replies.json") as fp:
        contents = fp.read()
    replies = json.loads(contents)
    assert replies == [response3]


def test_get_announcers_from_header(mock_post, mocker):
    entry_points = [
        MockEntryPoint("test1", make_dummy_announcer("Test1")),
        MockEntryPoint("test2", make_dummy_announcer("Test2")),
    ]
    mocker.patch("nefelibata.announcers.iter_entry_points", return_value=entry_points)

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, there!
        keywords: test
        summary: My first post
        announce-on: test1

        Hi, there!
        """,
        )

    root = Path("/path/to/blog")
    config = {
        "url": "https://blog.example.com/",
        "language": "en",
        "announce-on": ["test2"],
        "test1": {},
        "test2": {},
    }

    announcers = [
        announcer for announcer in get_announcers(root, config) if announcer.match(post)
    ]
    assert len(announcers) == 1
    assert announcers[0].name == "Test1"


def test_get_announcers_from_config(mock_post, mocker):
    entry_points = [
        MockEntryPoint("test1", make_dummy_announcer("Test1")),
        MockEntryPoint("test2", make_dummy_announcer("Test2")),
    ]
    mocker.patch("nefelibata.announcers.iter_entry_points", return_value=entry_points)

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, there!
        keywords: test
        summary: My first post

        Hi, there!
        """,
        )

    root = Path("/path/to/blog")
    config = {
        "url": "https://blog.example.com/",
        "language": "en",
        "announce-on": "test2",
        "test1": {},
        "test2": {},
    }

    announcers = [
        announcer for announcer in get_announcers(root, config) if announcer.match(post)
    ]
    assert len(announcers) == 1
    assert announcers[0].name == "Test2"


def test_get_announcers_extra(mock_post, mocker):
    entry_points = [
        MockEntryPoint("test1", make_dummy_announcer("Test1")),
        MockEntryPoint("test2", make_dummy_announcer("Test2")),
    ]
    mocker.patch("nefelibata.announcers.iter_entry_points", return_value=entry_points)

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, there!
        keywords: test
        summary: My first post
        announce-on-extra: test1

        Hi, there!
        """,
        )

    root = Path("/path/to/blog")
    config = {
        "url": "https://blog.example.com/",
        "language": "en",
        "announce-on": ["test2"],
        "test1": {},
        "test2": {},
    }

    announcers = [
        announcer for announcer in get_announcers(root, config) if announcer.match(post)
    ]
    assert len(announcers) == 2


def test_get_announcers_skip(mock_post, mocker):
    entry_points = [
        MockEntryPoint("test1", make_dummy_announcer("Test1")),
        MockEntryPoint("test2", make_dummy_announcer("Test2")),
    ]
    mocker.patch("nefelibata.announcers.iter_entry_points", return_value=entry_points)

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, there!
        keywords: test
        summary: My first post
        announce-on-skip: test1

        Hi, there!
        """,
        )

    root = Path("/path/to/blog")
    config = {
        "url": "https://blog.example.com/",
        "language": "en",
        "announce-on": ["test1", "test2"],
        "test1": {},
        "test2": {},
    }

    announcers = [
        announcer for announcer in get_announcers(root, config) if announcer.match(post)
    ]
    assert len(announcers) == 1
