import urllib.parse
from datetime import datetime
from unittest.mock import MagicMock

from freezegun import freeze_time
from nefelibata.announcers.medium import MediumAnnouncer

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


def test_announcer(mock_post, requests_mock):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, Medium!
        keywords: test
        summary: My first Medium post
        announce-on: medium

        Hi, there!
        """,
        )

    config = {
        "url": "https://blog.example.com/",
        "language": "en",
    }
    announcer = MediumAnnouncer(post, config, "token", "public")

    requests_mock.get(
        "https://api.medium.com/v1/me", json={"data": {"id": 1}},
    )
    mock_post = requests_mock.post(
        "https://api.medium.com/v1/users/1/posts",
        json={"data": {"url": "https://medium.com/@user/hello-medium"}},
    )

    url = announcer.announce()
    assert url == "https://medium.com/@user/hello-medium"
    assert urllib.parse.parse_qs(mock_post.last_request.text) == {
        "canonicalUrl": ["https://blog.example.com/first/index.html"],
        "content": ["<p>Hi, there!</p>"],
        "contentFormat": ["html"],
        "publishStatus": ["public"],
        "tags": ["test"],
        "title": ["Hello, Medium!"],
    }

    post.parsed["medium-url"] = "https://medium.com/@user/hello-medium"
    responses = announcer.collect()
    assert responses == []
