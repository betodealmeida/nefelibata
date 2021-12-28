"""
Tests for ``nefelibata.publishers.command``.
"""
# pylint: disable=invalid-name
from datetime import datetime, timezone
from pathlib import Path

import pytest
from freezegun import freeze_time
from pyfakefs.fake_filesystem import FakeFilesystem
from pytest_mock import MockerFixture

from nefelibata.config import Config
from nefelibata.publishers.command import CommandPublisher


@pytest.mark.asyncio
async def test_publish(
    mocker: MockerFixture,
    fs: FakeFilesystem,
    root: Path,
    config: Config,
) -> None:
    """
    Test ``publish``.
    """
    mocker.patch.object(
        CommandPublisher,
        "find_modified_files",
        return_value=iter(
            [
                root / "build/generic/one/index.html",
                root / "build/generic/one/photo.jpg",
                root / "build/generic/one/blob",
            ],
        ),
    )
    subprocess = mocker.patch("nefelibata.publishers.command.subprocess")

    fs.create_file(root / "build/generic/one", contents="Hello, world!")

    publisher = CommandPublisher(
        root,
        config,
        "generic",
        ["touch $path", "cp $path dir/"],
        ["notify.py"],
    )

    with freeze_time("2021-01-01T00:00:00Z"):
        publishing = await publisher.publish()
    assert publishing.dict() == {
        "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
    }
    print(subprocess.run.mock_calls)
    subprocess.run.assert_has_calls(
        [
            mocker.call(
                "touch $path",
                shell=True,
                check=True,
                env={
                    "path": Path("one/index.html"),
                },
            ),
            mocker.call(
                "cp $path dir/",
                shell=True,
                check=True,
                env={
                    "path": Path("one/index.html"),
                },
            ),
            mocker.call(
                "touch $path",
                shell=True,
                check=True,
                env={
                    "path": Path("one/photo.jpg"),
                },
            ),
            mocker.call(
                "cp $path dir/",
                shell=True,
                check=True,
                env={
                    "path": Path("one/photo.jpg"),
                },
            ),
            mocker.call(
                "touch $path",
                shell=True,
                check=True,
                env={
                    "path": Path("one/blob"),
                },
            ),
            mocker.call(
                "cp $path dir/",
                shell=True,
                check=True,
                env={
                    "path": Path("one/blob"),
                },
            ),
            mocker.call(
                "notify.py",
                shell=True,
                check=True,
            ),
        ],
    )


@pytest.mark.asyncio
async def test_publish_no_modified_files(
    mocker: MockerFixture,
    root: Path,
    config: Config,
) -> None:
    """
    Test ``publish`` when no files have been modified.
    """
    mocker.patch.object(
        CommandPublisher,
        "find_modified_files",
        return_value=iter([]),
    )
    mocker.patch("nefelibata.publishers.command.subprocess")

    publisher = CommandPublisher(
        root,
        config,
        "generic",
        ["touch $path", "cp $path dir/"],
        ["notify.py"],
    )

    with freeze_time("2021-01-01T00:00:00Z"):
        publishing = await publisher.publish()
    assert publishing is None
