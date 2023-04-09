"""
Tests for ``nefelibata.assistants.reading_time``.
"""

from pathlib import Path

import pytest

from nefelibata.assistants.reading_time import ReadingTimeAssistant
from nefelibata.config import Config
from nefelibata.post import Post


@pytest.mark.asyncio
async def test_assistant(root: Path, config: Config, post: Post) -> None:
    """
    Test the assistant.
    """
    assistant = ReadingTimeAssistant(root, config)

    payload = await assistant.get_post_metadata(post)
    assert payload == {
        "images": 0,
        "total_minutes": 1,
        "total_seconds": 3.6226415094339623,
        "words": 16,
    }
