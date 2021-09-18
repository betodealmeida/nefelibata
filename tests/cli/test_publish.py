"""
Test ``nefelibata.cli.publish``.
"""
from datetime import datetime
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from nefelibata.cli import publish
from nefelibata.publishers.base import Publishing


@pytest.mark.asyncio
async def test_run(
    mocker: MockerFixture,
    root: Path,
) -> None:
    """
    Test ``publish``.
    """
    publisher = mocker.MagicMock()
    publisher.publish = mocker.AsyncMock(
        return_value=Publishing(timestamp=datetime(2021, 1, 1)),
    )

    mocker.patch("nefelibata.cli.publish.get_config")
    mocker.patch(
        "nefelibata.cli.publish.get_publishers",
        return_value={"publisher": publisher},
    )

    await publish.run(root)

    publisher.publish.assert_called_with(None, False)
