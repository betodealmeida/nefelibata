"""
Tests for ``nefelibata.publishers.base``.
"""
# pylint: disable=invalid-name
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Type

import pytest
from freezegun import freeze_time
from pyfakefs.fake_filesystem import FakeFilesystem
from pytest_mock import MockerFixture

from nefelibata.publishers.base import Publisher, get_publishers
from nefelibata.typing import Config

from ..conftest import MockEntryPoint


def test_get_publishers(
    mocker: MockerFixture,
    make_entry_point: Type[MockEntryPoint],
    root: Path,
) -> None:
    """
    Test ``get_publishers``.
    """

    class DummyPublisher(Publisher):
        """
        A dummy publisher.
        """

        async def publish(
            self,
            since: Optional[datetime] = None,
            force: bool = False,
        ) -> None:
            pass

    entry_points = [make_entry_point("dummy_publisher", DummyPublisher)]
    mocker.patch(
        "nefelibata.publishers.base.iter_entry_points",
        return_value=entry_points,
    )

    config = {
        "publishers": {"dummy": {"plugin": "dummy_publisher"}},
    }
    publishers = get_publishers(root, config)
    assert len(publishers) == 1
    assert isinstance(publishers["dummy"], DummyPublisher)

    config = {
        "publishers": {"invalid": {"invalid": "dummy_publisher"}},
    }
    with pytest.raises(Exception) as excinfo:
        get_publishers(root, config)
    assert (
        str(excinfo.value)
        == """Invalid configuration, missing "plugin": {'invalid': 'dummy_publisher'}"""
    )


def test_find_modified_files(
    fs: FakeFilesystem,
    root: Path,
    config: Config,
) -> None:
    """
    Test ``find_modified_files``.
    """
    publisher = Publisher(root, config)

    fs.create_dir(root / "build/subdir")
    with freeze_time("2021-01-01T00:00:00Z"):
        (root / "build/one").touch()
    with freeze_time("2021-01-02T00:00:00Z"):
        (root / "build/subdir/two").touch()

    since = datetime(2021, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    modified_files = list(publisher.find_modified_files(force=False, since=since))
    assert modified_files == [Path("/path/to/blog/build/subdir/two")]

    since = datetime(2021, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
    modified_files = list(publisher.find_modified_files(force=False, since=since))
    assert modified_files == []

    since = datetime(2021, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
    modified_files = list(publisher.find_modified_files(force=True, since=since))
    assert modified_files == [
        Path("/path/to/blog/build/one"),
        Path("/path/to/blog/build/subdir/two"),
    ]
