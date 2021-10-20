"""
Tests for ``nefelibata.assistants.archive_links``.
"""

from datetime import timedelta
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
    # disable sleep
    mocker.patch("nefelibata.assistants.archive_links.SLEEP", timedelta(seconds=0))

    links = {
        "original": {
            "rel": "original",
            "url": URL("https://nefelibata.readthedocs.io/"),
        },
        "timemap": {
            "rel": "timemap",
            "type": "application/link-format",
            "url": URL(
                "https://web.archive.org/web/timemap/link/https://nefelibata.readthedocs.io/",
            ),
        },
        "timegate": {
            "rel": "timegate",
            "url": URL(
                "https://web.archive.org/web/https://nefelibata.readthedocs.io/",
            ),
        },
        "first memento": {
            "rel": "first memento",
            "datetime": "Sun, 05 Aug 2018 06:22:28 GMT",
            "url": URL(
                "https://web.archive.org/web/20180805062228/http://nefelibata.readthedocs.io/",
            ),
        },
        "prev memento": {
            "rel": "prev memento",
            "datetime": "Tue, 29 Jun 2021 01:15:06 GMT",
            "url": URL(
                "https://web.archive.org/web/20210629011506/https://nefelibata.readthedocs.io/",
            ),
        },
        "memento": {
            "rel": "memento",
            "datetime": "Sun, 03 Oct 2021 15:46:02 GMT",
            "url": URL(
                "https://web.archive.org/web/20211003154602/https://nefelibata.readthedocs.io/",
            ),
        },
        "last memento": {
            "rel": "last memento",
            "datetime": "Sun, 03 Oct 2021 15:46:02 GMT",
            "url": URL(
                "https://web.archive.org/web/20211003154602/https://nefelibata.readthedocs.io/",
            ),
        },
    }
    get = mocker.patch("nefelibata.assistants.archive_links.ClientSession.get")
    get.return_value.__aenter__.return_value.links = links

    assistant = ArchiveLinksAssistant(root, config)

    response = await assistant.get_post_metadata(post)
    assert response == {
        "https://nefelibata.readthedocs.io/": (
            "https://web.archive.org/web/20211003154602/"
            "https://nefelibata.readthedocs.io/"
        ),
    }

    mocker.patch(
        "nefelibata.assistants.archive_links.extract_links",
        return_value=[URL("gemini://example.com/")],
    )
    response = await assistant.get_post_metadata(post)
    assert response == {}


@pytest.mark.asyncio
async def test_sleep(
    mocker: MockerFixture,
    root: Path,
    config: Config,
    post: Post,
) -> None:
    """
    Test that we ``sleep`` between URLs.
    """
    get = mocker.patch("nefelibata.assistants.archive_links.ClientSession.get")
    get.return_value.__aenter__.return_value.links = {}

    sleep = mocker.patch("nefelibata.assistants.archive_links.asyncio.sleep")

    mocker.patch(
        "nefelibata.assistants.archive_links.extract_links",
        return_value=[URL("https://example.com/foo"), URL("https://example.com/bar")],
    )

    assistant = ArchiveLinksAssistant(root, config)
    await assistant.get_post_metadata(post)

    sleep.assert_called_with(12.0)
