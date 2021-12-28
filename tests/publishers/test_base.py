"""
Tests for ``nefelibata.publishers.base``.
"""
# pylint: disable=invalid-name
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Type

from freezegun import freeze_time
from pyfakefs.fake_filesystem import FakeFilesystem
from pytest_mock import MockerFixture

from nefelibata.config import BuilderModel, Config, PublisherModel
from nefelibata.publishers.base import Publisher, get_publishers

from ..conftest import MockEntryPoint


def test_get_publishers(
    mocker: MockerFixture,
    make_entry_point: Type[MockEntryPoint],
    root: Path,
    config: Config,
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

    config.publishers = {"dummy": PublisherModel(plugin="dummy_publisher")}
    config.builders = {
        "site_builder": BuilderModel(
            **{
                "plugin": "site_builder",
                "announce-on": [],
                "publish-to": ["dummy"],
                "home": "https://example.com/",
                "path": "site",
            }
        ),
    }
    publishers = get_publishers(root, config)
    assert len(publishers) == 1
    assert isinstance(publishers["site_builder => dummy"], DummyPublisher)


def test_find_modified_files(
    fs: FakeFilesystem,
    root: Path,
    config: Config,
) -> None:
    """
    Test ``find_modified_files``.
    """
    publisher = Publisher(root, config, "generic")

    fs.create_dir(root / "build/generic")
    fs.create_dir(root / "build/generic/subdir")
    with freeze_time("2021-01-01T00:00:00Z"):
        (root / "build/generic/one").touch()
    with freeze_time("2021-01-02T00:00:00Z"):
        (root / "build/generic/subdir/two").touch()

    since = datetime(2021, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    modified_files = list(publisher.find_modified_files(force=False, since=since))
    assert modified_files == [Path("/path/to/blog/build/generic/subdir/two")]

    since = datetime(2021, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
    modified_files = list(publisher.find_modified_files(force=False, since=since))
    assert modified_files == []

    since = datetime(2021, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
    modified_files = list(publisher.find_modified_files(force=True, since=since))
    assert modified_files == [
        Path("/path/to/blog/build/generic/one"),
        Path("/path/to/blog/build/generic/subdir/two"),
    ]
