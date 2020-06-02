from pathlib import Path
from unittest.mock import MagicMock

from nefelibata.console import main

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


def test_console_init(mocker):
    arguments = {
        "--loglevel": "debug",
        "init": True,
        "new": False,
        "build": False,
        "preview": False,
        "publish": False,
        "DIRECTORY": None,
    }
    mocker.patch("nefelibata.console.docopt", return_value=arguments)

    mock_init = MagicMock()
    mocker.patch("nefelibata.console.init", mock_init)

    main()

    mock_init.run.assert_called_with(Path("."))


def test_console_init_with_directory(mocker):
    arguments = {
        "--loglevel": "debug",
        "init": True,
        "new": False,
        "build": False,
        "preview": False,
        "publish": False,
        "DIRECTORY": "/path/to/blog",
    }
    mocker.patch("nefelibata.console.docopt", return_value=arguments)

    mock_init = MagicMock()
    mocker.patch("nefelibata.console.init", mock_init)

    main()

    mock_init.run.assert_called_with(Path("/path/to/blog"))


def test_console_new(mocker):
    arguments = {
        "--loglevel": "debug",
        "init": False,
        "new": True,
        "build": False,
        "preview": False,
        "publish": False,
        "DIRECTORY": None,
        "POST": "Hello, world!",
    }
    mocker.patch("nefelibata.console.docopt", return_value=arguments)

    mock_new = MagicMock()
    mocker.patch("nefelibata.console.new", mock_new)
    mocker.patch(
        "nefelibata.console.find_directory", return_value=Path("/path/to/blog"),
    )

    main()

    mock_new.run.assert_called_with(Path("/path/to/blog"), "Hello, world!")


def test_console_build(mocker):
    arguments = {
        "--loglevel": "debug",
        "init": False,
        "new": False,
        "build": True,
        "preview": False,
        "publish": False,
        "DIRECTORY": None,
        "--force": True,
        "--no-collect": True,
    }
    mocker.patch("nefelibata.console.docopt", return_value=arguments)

    mock_build = MagicMock()
    mocker.patch("nefelibata.console.build", mock_build)
    mocker.patch(
        "nefelibata.console.find_directory", return_value=Path("/path/to/blog"),
    )

    main()

    mock_build.run.assert_called_with(Path("/path/to/blog"), True, False)


def test_console_preview(mocker):
    arguments = {
        "--loglevel": "debug",
        "init": False,
        "new": False,
        "build": False,
        "preview": True,
        "publish": False,
        "DIRECTORY": None,
        "-p": 8001,
    }
    mocker.patch("nefelibata.console.docopt", return_value=arguments)

    mock_preview = MagicMock()
    mocker.patch("nefelibata.console.preview", mock_preview)
    mocker.patch(
        "nefelibata.console.find_directory", return_value=Path("/path/to/blog"),
    )

    main()

    mock_preview.run.assert_called_with(Path("/path/to/blog"), 8001)


def test_console_publish(mocker):
    arguments = {
        "--loglevel": "debug",
        "init": False,
        "new": False,
        "build": False,
        "preview": False,
        "publish": True,
        "DIRECTORY": None,
        "--force": True,
    }
    mocker.patch("nefelibata.console.docopt", return_value=arguments)

    mock_publish = MagicMock()
    mocker.patch("nefelibata.console.publish", mock_publish)
    mocker.patch(
        "nefelibata.console.find_directory", return_value=Path("/path/to/blog"),
    )

    main()

    mock_publish.run.assert_called_with(Path("/path/to/blog"), True)


def test_console_bogus(mocker):
    arguments = {
        "--loglevel": "debug",
        "init": False,
        "new": False,
        "build": False,
        "preview": False,
        "publish": False,
        "DIRECTORY": None,
    }
    mocker.patch("nefelibata.console.docopt", return_value=arguments)
    mocker.patch(
        "nefelibata.console.find_directory", return_value=Path("/path/to/blog"),
    )

    main()

    assert True
