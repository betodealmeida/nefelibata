from pathlib import Path
from unittest.mock import MagicMock

from freezegun import freeze_time
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
        "ROOT_DIR": None,
        "-s": None,
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
        "ROOT_DIR": "/path/to/blog",
        "-s": None,
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
        "ROOT_DIR": None,
        "-s": None,
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
        "ROOT_DIR": None,
        "-s": None,
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

    mock_build.run.assert_called_with(Path("/path/to/blog"), None, True, False)


def test_console_build_single_post(mocker, mock_post):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: This is your first post
        keywords: welcome, blog
        summary: Hello, world!

        # Welcome #

        This is your first post. It should be written using Markdown.
        """,
        )

    mocker.patch("nefelibata.console.Post", return_value=post)

    arguments = {
        "--loglevel": "debug",
        "init": False,
        "new": False,
        "build": True,
        "preview": False,
        "publish": False,
        "ROOT_DIR": None,
        "-s": "/path/to/blog/posts/first",
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

    mock_build.run.assert_called_with(Path("/path/to/blog"), post, True, False)


def test_console_preview(mocker):
    arguments = {
        "--loglevel": "debug",
        "init": False,
        "new": False,
        "build": False,
        "preview": True,
        "publish": False,
        "ROOT_DIR": None,
        "-s": None,
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
        "ROOT_DIR": None,
        "-s": None,
        "--force": True,
    }
    mocker.patch("nefelibata.console.docopt", return_value=arguments)

    mock_publish = MagicMock()
    mocker.patch("nefelibata.console.publish", mock_publish)
    mocker.patch(
        "nefelibata.console.find_directory", return_value=Path("/path/to/blog"),
    )

    main()

    mock_publish.run.assert_called_with(Path("/path/to/blog"), None, True)


def test_console_publish_single_post(mocker, mock_post):
    with freeze_time("2020-01-01T00:00:00Z"):
        post = mock_post(
            """
        subject: This is your first post
        keywords: welcome, blog
        summary: Hello, world!

        # Welcome #

        This is your first post. It should be written using Markdown.
        """,
        )

    mocker.patch("nefelibata.console.Post", return_value=post)

    arguments = {
        "--loglevel": "debug",
        "init": False,
        "new": False,
        "build": False,
        "preview": False,
        "publish": True,
        "ROOT_DIR": None,
        "-s": "/path/to/blog/posts/first/index.mkd",
        "--force": True,
    }
    mocker.patch("nefelibata.console.docopt", return_value=arguments)

    mock_publish = MagicMock()
    mocker.patch("nefelibata.console.publish", mock_publish)
    mocker.patch(
        "nefelibata.console.find_directory", return_value=Path("/path/to/blog"),
    )

    main()

    mock_publish.run.assert_called_with(Path("/path/to/blog"), post, True)


def test_console_bogus(mocker):
    arguments = {
        "--loglevel": "debug",
        "init": False,
        "new": False,
        "build": False,
        "preview": False,
        "publish": False,
        "ROOT_DIR": None,
        "-s": None,
    }
    mocker.patch("nefelibata.console.docopt", return_value=arguments)
    mocker.patch(
        "nefelibata.console.find_directory", return_value=Path("/path/to/blog"),
    )

    main()

    assert True
