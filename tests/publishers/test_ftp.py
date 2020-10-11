from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any
from typing import Dict
from unittest.mock import call
from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time
from nefelibata.publishers.ftp import FTPPublisher

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


config: Dict[str, Any] = {}


def test_publish(fs, mocker):
    root = Path("/path/to/blog")
    fs.create_dir(root)

    publisher = FTPPublisher(
        root,
        config,
        host="ftp.example.com",
        username="anonymous",
        password="test",
        basedir="public",
    )

    with freeze_time("2020-01-01T00:00:00Z"):
        fs.create_file(root / "last_published")

    # create 2 posts, 1 of them up-to-date
    fs.create_dir(root / "build")
    with freeze_time("2019-12-31T00:00:00Z"):
        fs.create_dir(root / "build/one")
        fs.create_file(root / "build/one/index.mkd")
        fs.create_file(root / "build/one/index.html")
    with freeze_time("2020-01-02T00:00:00Z"):
        fs.create_dir(root / "build/two")
        fs.create_file(root / "build/two/index.mkd")
        fs.create_file(root / "build/two/index.html")

    mock_ftp = MagicMock()
    mock_ftp.return_value.__enter__.return_value.pwd.return_value = "/home/public"
    mocker.patch("nefelibata.publishers.ftp.FTP", mock_ftp)
    mocker.patch(
        "nefelibata.publishers.ftp.open", side_effect=lambda filename, mode: filename,
    )
    with freeze_time("2020-01-03T00:00:00Z"):
        publisher.publish()

    mock_ftp.assert_called_with("ftp.example.com", "anonymous", "test")
    mock_ftp.return_value.__enter__.return_value.cwd.assert_has_calls(
        [call("public"), call("two")],
    )

    mtime = (root / "last_published").stat().st_mtime
    assert (
        datetime.fromtimestamp(mtime).astimezone(timezone.utc).isoformat()
        == "2020-01-03T00:00:00+00:00"
    )


def test_publish_no_last_published(fs, mocker):
    root = Path("/path/to/blog")
    fs.create_dir(root)

    publisher = FTPPublisher(
        root,
        config,
        host="ftp.example.com",
        username="anonymous",
        password="test",
        basedir="public",
    )

    # create 2 posts, 1 of them up-to-date
    fs.create_dir(root / "build")
    with freeze_time("2019-12-31T00:00:00Z"):
        fs.create_dir(root / "build/one")
        fs.create_file(root / "build/one/index.mkd")
        fs.create_file(root / "build/one/index.html")
    with freeze_time("2020-01-02T00:00:00Z"):
        fs.create_dir(root / "build/two")
        fs.create_file(root / "build/two/index.mkd")
        fs.create_file(root / "build/two/index.html")

    mock_ftp = MagicMock()
    mock_ftp.return_value.__enter__.return_value.pwd.return_value = "/home/public"
    mocker.patch("nefelibata.publishers.ftp.FTP", mock_ftp)
    mocker.patch(
        "nefelibata.publishers.ftp.open", side_effect=lambda filename, mode: filename,
    )
    with freeze_time("2020-01-03T00:00:00Z"):
        publisher.publish()

    mock_ftp.return_value.__enter__.return_value.cwd.assert_has_calls(
        [call("public"), call("one"), call("/home/public"), call("two")],
    )

    mtime = (root / "last_published").stat().st_mtime
    assert (
        datetime.fromtimestamp(mtime).astimezone(timezone.utc).isoformat()
        == "2020-01-03T00:00:00+00:00"
    )


def test_publish_no_basedir(fs, mocker):
    root = Path("/path/to/blog")
    fs.create_dir(root)

    publisher = FTPPublisher(
        root, config, host="ftp.example.com", username="anonymous", password="test",
    )

    with freeze_time("2020-01-01T00:00:00Z"):
        fs.create_file(root / "last_published")

    # create 2 posts, 1 of them up-to-date
    fs.create_dir(root / "build")
    with freeze_time("2019-12-31T00:00:00Z"):
        fs.create_dir(root / "build/one")
        fs.create_file(root / "build/one/index.mkd")
        fs.create_file(root / "build/one/index.html")
    with freeze_time("2020-01-02T00:00:00Z"):
        fs.create_dir(root / "build/two")
        fs.create_file(root / "build/two/index.mkd")
        fs.create_file(root / "build/two/index.html")

    mock_ftp = MagicMock()
    mock_ftp.return_value.__enter__.return_value.pwd.return_value = "/"
    mocker.patch("nefelibata.publishers.ftp.FTP", mock_ftp)
    mocker.patch(
        "nefelibata.publishers.ftp.open", side_effect=lambda filename, mode: filename,
    )
    with freeze_time("2020-01-03T00:00:00Z"):
        publisher.publish()

    mock_ftp.return_value.__enter__.return_value.cwd.assert_has_calls([call("two")])


def test_publish_create_dir(fs, mocker):
    root = Path("/path/to/blog")
    fs.create_dir(root)

    publisher = FTPPublisher(
        root, config, host="ftp.example.com", username="anonymous", password="test",
    )

    with freeze_time("2020-01-01T00:00:00Z"):
        fs.create_file(root / "last_published")

    # create 2 posts, 1 of them up-to-date
    fs.create_dir(root / "build")
    with freeze_time("2019-12-31T00:00:00Z"):
        fs.create_dir(root / "build/one")
        fs.create_file(root / "build/one/index.mkd")
        fs.create_file(root / "build/one/index.html")
    with freeze_time("2020-01-02T00:00:00Z"):
        fs.create_dir(root / "build/two")
        fs.create_file(root / "build/two/index.mkd")
        fs.create_file(root / "build/two/index.html")

    mock_ftp = MagicMock()
    mock_ftp.return_value.__enter__.return_value.pwd.return_value = "/"
    mock_ftp.return_value.__enter__.return_value.cwd.side_effect = [
        Exception("Directory doesn't exist!"),
        True,
    ]
    mocker.patch("nefelibata.publishers.ftp.FTP", mock_ftp)
    mocker.patch(
        "nefelibata.publishers.ftp.open", side_effect=lambda filename, mode: filename,
    )
    with freeze_time("2020-01-03T00:00:00Z"):
        publisher.publish()

    mock_ftp.return_value.__enter__.return_value.mkd.assert_called_with("two")
