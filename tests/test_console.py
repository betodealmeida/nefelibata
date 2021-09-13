"""
Tests for ``nefelibata.console``.
"""
import asyncio
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from nefelibata import console


@pytest.mark.asyncio
async def test_main_init(mocker: MockerFixture) -> None:
    """
    Test ``main`` with the "init" action.
    """
    init = mocker.patch("nefelibata.console.init")
    init.run = mocker.AsyncMock()

    mocker.patch(
        "nefelibata.console.docopt",
        return_value={
            "--loglevel": "debug",
            "build": False,
            "init": True,
            "ROOT_DIR": "/path/to/blog",
            "--force": False,
        },
    )
    await console.main()
    init.run.assert_called_with(Path("/path/to/blog"), False)


@pytest.mark.asyncio
async def test_main_build(mocker: MockerFixture) -> None:
    """
    Test ``main`` with the "build" action.
    """
    build = mocker.patch("nefelibata.console.build")
    build.run = mocker.AsyncMock()

    mocker.patch(
        "nefelibata.console.docopt",
        return_value={
            "--loglevel": "debug",
            "build": True,
            "init": False,
            "ROOT_DIR": "/path/to/blog",
            "--force": False,
        },
    )
    await console.main()
    build.run.assert_called_with(Path("/path/to/blog"), False)

    mocker.patch(
        "nefelibata.console.docopt",
        return_value={
            "--loglevel": "debug",
            "build": True,
            "init": False,
            "ROOT_DIR": "/path/to/blog",
            "--force": True,
        },
    )
    await console.main()
    build.run.assert_called_with(Path("/path/to/blog"), True)

    mocker.patch(
        "nefelibata.console.docopt",
        return_value={
            "--loglevel": "debug",
            "build": True,
            "init": False,
            "ROOT_DIR": None,
            "--force": True,
        },
    )
    mocker.patch(
        "nefelibata.console.find_directory",
        return_value=Path("/path/to/blog"),
    )
    await console.main()
    build.run.assert_called_with(Path("/path/to/blog"), True)


@pytest.mark.asyncio
async def test_main_no_action(mocker: MockerFixture) -> None:
    """
    Test ``main`` without any actions -- should not happen.
    """
    mocker.patch(
        "nefelibata.console.docopt",
        return_value={
            "--loglevel": "debug",
            "build": False,
            "init": False,
            "ROOT_DIR": "/path/to/blog",
            "--force": False,
        },
    )
    await console.main()


@pytest.mark.asyncio
async def test_main_canceled(mocker) -> None:
    """
    Test canceling the ``main`` coroutine.
    """
    build = mocker.patch("nefelibata.console.build")
    build.run = mocker.AsyncMock(side_effect=asyncio.CancelledError("Canceled"))
    _logger = mocker.patch("nefelibata.console._logger")

    mocker.patch(
        "nefelibata.console.docopt",
        return_value={
            "--loglevel": "debug",
            "build": True,
            "init": False,
            "ROOT_DIR": "/path/to/blog",
            "--force": False,
        },
    )
    await console.main()

    _logger.info.assert_called_with("Canceled")


def test_run(mocker: MockerFixture) -> None:
    """
    Test ``run``.
    """
    main = mocker.AsyncMock()
    mocker.patch("nefelibata.console.main", main)

    console.run()

    main.assert_called()


def test_interrupt(mocker: MockerFixture) -> None:
    """
    Test that ``CTRL-C`` stops the CLI.
    """
    main = mocker.AsyncMock(side_effect=KeyboardInterrupt())
    mocker.patch("nefelibata.console.main", main)
    _logger = mocker.patch("nefelibata.console._logger")

    console.run()

    _logger.info.assert_called_with("Stopping Nefelibata")
