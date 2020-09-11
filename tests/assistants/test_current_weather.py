import json
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any
from typing import Dict
from unittest.mock import MagicMock

import requests
from freezegun import freeze_time
from nefelibata.assistants.current_weather import CurrentWeatherAssistant
from nefelibata.builders.post import PostBuilder

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


config: Dict[str, Any] = {
    "url": "https://example.com/",
    "language": "en",
    "theme": "test-theme",
    "webmention": {"endpoint": "https://webmention.io/example.com/webmention"},
}


def test_current_weather(mock_post, requests_mock):
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
    PostBuilder(root, config).process_post(post)
    assistant = CurrentWeatherAssistant(root, config)

    requests_mock.get("https://wttr.in/", json={"foo": "bar"})
    with freeze_time("2020-01-01T00:30:00Z"):
        assistant.process_post(post)

    storage = post.file_path.parent / "weather.json"
    with open(storage) as fp:
        contents = json.loads(fp.read())

    assert contents == {"foo": "bar"}
    assert datetime.fromtimestamp(storage.stat().st_mtime).astimezone(
        timezone.utc,
    ) == datetime(2020, 1, 1, 0, 30, tzinfo=timezone.utc)
    assert datetime.fromtimestamp(post.file_path.stat().st_mtime).astimezone(
        timezone.utc,
    ) == datetime(2020, 1, 1, 0, 30, tzinfo=timezone.utc)

    with freeze_time("2020-01-03T00:00:00Z"):
        assistant.process_post(post)

    assert datetime.fromtimestamp(storage.stat().st_mtime).astimezone(
        timezone.utc,
    ) == datetime(2020, 1, 1, 0, 30, tzinfo=timezone.utc)


def test_current_weather_stale(mock_post, requests_mock):
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
    PostBuilder(root, config).process_post(post)
    assistant = CurrentWeatherAssistant(root, config)

    requests_mock.get("https://wttr.in/", json={"foo": "bar"})
    with freeze_time("2020-01-02T00:30:00Z"):
        assistant.process_post(post)

    storage = post.file_path.parent / "weather.json"
    assert not storage.exists()
