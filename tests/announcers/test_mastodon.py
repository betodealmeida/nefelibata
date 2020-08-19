from datetime import datetime
from datetime import timezone
from pathlib import Path
from unittest.mock import MagicMock

from freezegun import freeze_time
from mastodon import AttribAccessDict
from nefelibata.announcers.mastodon import MastodonAnnouncer

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


def test_announcer(mock_post, mocker):
    mock_client = MagicMock()
    mock_client.return_value.status_post.return_value = AttribAccessDict(
        {"url": "https://mastodon.example.com/@user/1"},
    )
    mock_client.return_value.status_context.return_value = {
        "descendants": [
            AttribAccessDict(
                {
                    "uri": "tag:example.com,2020-01-01:objectId=1:objectType=Status",
                    "created_at": datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                    "account": AttribAccessDict(
                        {
                            "display_name": "user",
                            "avatar": "https://user.example.com/photo.gif",
                            "url": "https://user.example.com/",
                            "note": "A user",
                        },
                    ),
                    "content": "Hello, world!",
                    "url": "https://mastodon.example.com/@user/1",
                },
            ),
        ],
    }
    mocker.patch("nefelibata.announcers.mastodon.mastodon.Mastodon", mock_client)

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, Mastodon!
        keywords: test
        summary: My first Mastodon post
        announce-on: mastodon

        Hi, there!
        """,
        )

    root = Path("/path/to/blog")
    config = {
        "url": "https://blog.example.com/",
        "language": "en",
    }
    announcer = MastodonAnnouncer(root, config, "token", "https://mastodon.example.com")

    url = announcer.announce(post)
    assert url == "https://mastodon.example.com/@user/1"
    mock_client.return_value.status_post.assert_called_with(
        status="My first Mastodon post\n\nhttps://blog.example.com/first/index.html",
        visibility="public",
        language="en",
        idempotency_key="/path/to/blog/posts/first/index.mkd",
    )

    post.parsed["mastodon-url"] = "https://mastodon.example.com/@user/1"
    responses = announcer.collect(post)
    assert responses == [
        {
            "source": "Mastodon",
            "color": "#2b90d9",
            "id": "mastodon:tag:example.com,2020-01-01:objectId=1:objectType=Status",
            "timestamp": "2020-01-01T00:00:00+00:00",
            "user": {
                "name": "user",
                "image": "https://user.example.com/photo.gif",
                "url": "https://user.example.com/",
                "description": "A user",
            },
            "comment": {
                "text": "Hello, world!",
                "url": "https://mastodon.example.com/@user/1",
            },
            "url": "https://mastodon.example.com/@user/1",
        },
    ]
