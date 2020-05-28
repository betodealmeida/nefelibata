from datetime import datetime
from unittest.mock import MagicMock

import twitter
from freezegun import freeze_time
from nefelibata.announcers.twitter import TwitterAnnouncer

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


def test_announcer(mock_post, mocker):
    mock_client = MagicMock()
    mock_client.return_value.statuses.update.return_value = {
        "user": {"screen_name": "user"},
        "id_str": "1",
    }
    mock_client.return_value.statuses.mentions_timeline.return_value = [
        {
            "id_str": "2",
            "in_reply_to_status_id_str": "1",
            "created_at": "2020-01-01T00:00:00Z",
            "user": {
                "name": "User",
                "screen_name": "user",
                "profile_image_url_https": "https://user.example.com/photo.jpg",
                "url": "https://user.example.com/",
                "description": "A user.",
            },
            "text": "Welcome!",
        },
        {
            "id_str": "3",
            "in_reply_to_status_id_str": "2",
            "created_at": "2020-01-01T00:00:00Z",
            "user": {
                "name": "User",
                "profile_image_url_https": "https://user.example.com/photo.jpg",
                "url": "https://user.example.com/",
                "decription": "A user.",
            },
            "text": "Not a reply",
        },
    ]
    mocker.patch("nefelibata.announcers.twitter.twitter.Twitter", mock_client)

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, Twitter!
        keywords: test
        summary: My first Twitter post
        announce-on: twitter

        Hi, there!
        """,
        )

    config = {
        "url": "http://blog.example.com/",
        "language": "en",
    }
    announcer = TwitterAnnouncer(
        post, config, "oauth_token", "oauth_secret", "consumer_key", "consumer_secret",
    )

    url = announcer.announce()
    assert url == "https://twitter.com/user/status/1"

    post.parsed["twitter-url"] = "https://twitter.example.com/user/status/1"
    responses = announcer.collect()
    assert responses == [
        {
            "source": "Twitter",
            "color": "#00acee",
            "id": "twitter:2",
            "timestamp": "2020-01-01T00:00:00+00:00",
            "user": {
                "name": "User",
                "image": "https://user.example.com/photo.jpg",
                "url": "https://user.example.com/",
                "description": "A user.",
            },
            "comment": {"text": "Welcome!", "url": "https://twitter.com/user/status/2"},
            "url": "https://twitter.example.com/user/status/1",
        },
    ]


def test_collect_exception(mock_post, mocker):
    mock_client = MagicMock()
    mock_client.return_value.statuses.mentions_timeline.side_effect = Exception(
        "An error occurred!",
    )
    mocker.patch("nefelibata.announcers.twitter.twitter.Twitter", mock_client)

    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: Hello, Twitter!
        keywords: test
        summary: My first Twitter post
        announce-on: twitter

        Hi, there!
        """,
        )

    post.parsed["twitter-url"] = "https://twitter.example.com/user/status/1"

    config = {
        "url": "http://blog.example.com/",
        "language": "en",
    }
    announcer = TwitterAnnouncer(
        post, config, "oauth_token", "oauth_secret", "consumer_key", "consumer_secret",
    )
    responses = announcer.collect()
    assert responses == []