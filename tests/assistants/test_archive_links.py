"""
Tests for ``nefelibata.assistants.archive_links``.
"""

from pathlib import Path

import pytest
from pytest_mock import MockerFixture
from yarl import URL

from nefelibata.assistants.archive_links import ArchiveLinksAssistant
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
    mocker.patch(
        "nefelibata.assistants.archive_links.archive_urls",
        return_value={
            URL("https://nefelibata.readthedocs.io/"): URL(
                "https://web.archive.org/web/20211003154602/https://nefelibata.readthedocs.io/",
            ),
        },
    )

    assistant = ArchiveLinksAssistant(root, config)

    response = await assistant.get_post_metadata(post)
    assert response == {
        "https://nefelibata.readthedocs.io/": (
            "https://web.archive.org/web/20211003154602/"
            "https://nefelibata.readthedocs.io/"
        ),
    }
