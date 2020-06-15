from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any
from typing import Dict
from unittest.mock import call
from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time
from nefelibata.publishers.ipfs import IPFSPublisher

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


config: Dict[str, Any] = {
    "url": "https://blog.example.com/",
}


def test_publish(fs, mocker):
    root = Path("/path/to/blog")
    fs.create_dir(root)

    publisher = IPFSPublisher(root, config, "ipfs", "ipfs.example.com")

    with freeze_time("2020-01-01T00:00:00Z"):
        fs.create_file(root / "last_published")

    mock_subprocess = MagicMock()
    mock_subprocess.check_output.return_value = (
        "added Qmem4gvHMQXXKKyGtw9UzP3gvFe7J5EbKhmHfnEnaVQStk blog.example.com/first/index.html\n"
        "added QmTH1NAu8YV751j5fjvkj3hvP5D3b1pGgPu1tPmJXhNzLQ blog.example.com/first\n"
        "added QmQdQe72M4KsYdoUDKmUfpV6K2YHaRHFbv5MPDEscGaGzp blog.example.com"
    )
    mocker.patch("nefelibata.publishers.ipfs.subprocess", mock_subprocess)
    with freeze_time("2020-01-03T00:00:00Z"):
        publisher.publish()

    mock_subprocess.run.assert_has_calls(
        [
            call(
                [
                    "rsync",
                    "-rL",
                    "/path/to/blog/build/",
                    "ipfs@ipfs.example.com:blog.example.com/",
                ],
            ),
            call(
                [
                    "ssh",
                    "ipfs@ipfs.example.com",
                    "ipfs",
                    "name",
                    "publish",
                    "QmQdQe72M4KsYdoUDKmUfpV6K2YHaRHFbv5MPDEscGaGzp",
                ],
            ),
        ],
    )
    mock_subprocess.check_output.assert_called_with(
        ["ssh", "ipfs@ipfs.example.com", "ipfs", "add", "-r", "blog.example.com"],
        text=True,
    )

    mtime = (root / "last_published").stat().st_mtime
    assert (
        datetime.fromtimestamp(mtime).astimezone(timezone.utc).isoformat()
        == "2020-01-03T00:00:00+00:00"
    )


def test_publish_no_last_published(fs, mocker):
    root = Path("/path/to/blog")
    fs.create_dir(root)

    publisher = IPFSPublisher(root, config, "ipfs", "ipfs.example.com")

    mock_subprocess = MagicMock()
    mock_subprocess.check_output.return_value = (
        "added Qmem4gvHMQXXKKyGtw9UzP3gvFe7J5EbKhmHfnEnaVQStk blog.example.com/first/index.html\n"
        "added QmTH1NAu8YV751j5fjvkj3hvP5D3b1pGgPu1tPmJXhNzLQ blog.example.com/first\n"
        "added QmQdQe72M4KsYdoUDKmUfpV6K2YHaRHFbv5MPDEscGaGzp blog.example.com"
    )
    mocker.patch("nefelibata.publishers.ipfs.subprocess", mock_subprocess)
    with freeze_time("2020-01-03T00:00:00Z"):
        publisher.publish()

    mtime = (root / "last_published").stat().st_mtime
    assert (
        datetime.fromtimestamp(mtime).astimezone(timezone.utc).isoformat()
        == "2020-01-03T00:00:00+00:00"
    )


def test_publish_no_new_hash(fs, mocker):
    root = Path("/path/to/blog")
    fs.create_dir(root)

    publisher = IPFSPublisher(root, config, "ipfs", "ipfs.example.com")

    with freeze_time("2020-01-01T00:00:00Z"):
        fs.create_file(root / "last_published")

    mock_subprocess = MagicMock()
    mock_subprocess.check_output.return_value = ""
    mocker.patch("nefelibata.publishers.ipfs.subprocess", mock_subprocess)
    with freeze_time("2020-01-03T00:00:00Z"):
        publisher.publish()

    mtime = (root / "last_published").stat().st_mtime
    assert (
        datetime.fromtimestamp(mtime).astimezone(timezone.utc).isoformat()
        == "2020-01-01T00:00:00+00:00"
    )
