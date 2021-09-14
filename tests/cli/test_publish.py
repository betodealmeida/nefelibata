"""
Test ``nefelibata.cli.publish``.
"""
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from nefelibata.cli import publish


@pytest.mark.asyncio
async def test_run(
    mocker: MockerFixture,
    root: Path,
) -> None:
    """
    Test ``publish``.
    """
    publisher = mocker.MagicMock()
    publisher.publish = mocker.AsyncMock()

    mocker.patch("nefelibata.cli.publish.get_config")
    mocker.patch("nefelibata.cli.publish.get_publishers", return_value=[publisher])

    await publish.run(root)

    publisher.publish.assert_called_with(False)
