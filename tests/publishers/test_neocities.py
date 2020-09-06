from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any
from typing import Dict
from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time
from nefelibata.publishers.neocities import NeocitiesPublisher

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


config: Dict[str, Any] = {}


def test_publish(fs, mocker):
    root = Path("/path/to/blog")
    fs.create_dir(root)

    publisher = NeocitiesPublisher(root, config, api_key="XXX")

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

    mock_requests = MagicMock()
    mocker.patch("nefelibata.publishers.neocities.requests", mock_requests)
    mocker.patch(
        "nefelibata.publishers.neocities.open",
        side_effect=lambda filename, mode: filename,
    )
    with freeze_time("2020-01-03T00:00:00Z"):
        publisher.publish()

    # the markdown files are *not* uploaded, since Neocities rejects them
    mock_requests.post.assert_called_with(
        "https://neocities.org/api/upload",
        files={"two/index.html": Path(root / "build/two/index.html")},
        headers={"Authorization": "Bearer XXX"},
    )

    mtime = (root / "last_published").stat().st_mtime
    assert (
        datetime.fromtimestamp(mtime).astimezone(timezone.utc).isoformat()
        == "2020-01-03T00:00:00+00:00"
    )

    with freeze_time("2020-01-04T00:00:00Z"):
        publisher.publish()

    mtime = (root / "last_published").stat().st_mtime
    assert (
        datetime.fromtimestamp(mtime).astimezone(timezone.utc).isoformat()
        == "2020-01-03T00:00:00+00:00"
    )


def test_publish_no_last_published(fs, mocker):
    root = Path("/path/to/blog")
    fs.create_dir(root)

    publisher = NeocitiesPublisher(root, config, api_key="XXX")

    # create 2 posts
    fs.create_dir(root / "build")
    with freeze_time("2019-12-31T00:00:00Z"):
        fs.create_dir(root / "build/one")
        fs.create_file(root / "build/one/index.html")
    with freeze_time("2020-01-02T00:00:00Z"):
        fs.create_dir(root / "build/two")
        fs.create_file(root / "build/two/index.html")

    mock_requests = MagicMock()
    mocker.patch("nefelibata.publishers.neocities.requests", mock_requests)
    mocker.patch(
        "nefelibata.publishers.neocities.open",
        side_effect=lambda filename, mode: filename,
    )
    with freeze_time("2020-01-03T00:00:00Z"):
        publisher.publish()

    mock_requests.post.assert_called_with(
        "https://neocities.org/api/upload",
        files={
            "one/index.html": Path(root / "build/one/index.html"),
            "two/index.html": Path(root / "build/two/index.html"),
        },
        headers={"Authorization": "Bearer XXX"},
    )

    mtime = (root / "last_published").stat().st_mtime
    assert (
        datetime.fromtimestamp(mtime).astimezone(timezone.utc).isoformat()
        == "2020-01-03T00:00:00+00:00"
    )


def test_publish_username_password(fs, requests_mock):
    root = Path("/path/to/blog")
    fs.create_dir(root)

    requests_mock.get(
        "https://username:password@neocities.org/api/key",
        json={"result": "success", "api_key": "XXX"},
    )

    publisher = NeocitiesPublisher(root, config, "username", "password")

    assert publisher.headers == {"Authorization": "Bearer XXX"}


def test_publish_username_password_and_api_key(fs):
    root = Path("/path/to/blog")
    fs.create_dir(root)

    with pytest.raises(Exception) as excinfo:
        NeocitiesPublisher(root, config, "username", "password", "XXX")

    assert (
        str(excinfo.value)
        == "You must provide exactly ONE of username/password or API key"
    )
