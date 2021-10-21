"""
Tests for ``nefelibata.assistants.news``.
"""

import random
from pathlib import Path

import pytest
from freezegun import freeze_time
from pytest_mock import MockerFixture

from nefelibata.assistants.news import NewsAssistant
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
    random.seed(42)

    get = mocker.patch("nefelibata.assistants.news.ClientSession.get")
    get.return_value.__aenter__.return_value.json.return_value = {
        "articles": [
            {"hello": "world"},
            {"goodbye": "world"},
        ],
    }

    assistant = NewsAssistant(root, config, "SECRET", "us")

    with freeze_time("2021-01-01T00:00:00Z"):
        response = await assistant.get_post_metadata(post)
    assert response == {"hello": "world"}

    with freeze_time("2021-01-03T00:00:00Z"):
        response = await assistant.get_post_metadata(post)
    assert response == {}
