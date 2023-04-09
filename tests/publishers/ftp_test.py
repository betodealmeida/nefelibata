"""
Tests for ``nefelibata.publishers.ftp``.
"""
# pylint: disable=invalid-name
import ftplib
from datetime import datetime, timezone
from pathlib import Path

import pytest
from freezegun import freeze_time
from pyfakefs.fake_filesystem import FakeFilesystem
from pytest_mock import MockerFixture

from nefelibata.config import Config
from nefelibata.publishers.ftp import FTPPublisher


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
    FTP = mocker.patch("nefelibata.publishers.ftp.FTP")
    ftp = FTP.return_value.__enter__.return_value
    mocker.patch.object(
        FTPPublisher,
        "find_modified_files",
        return_value=iter([root / "build/generic/one"]),
    )

    fs.create_file(root / "build/generic/one", contents="Hello, world!")

    publisher = FTPPublisher(
        root,
        config,
        "generic",
        "ftp.example.com",
        "username",
        "password",
    )

    await publisher.publish()

    FTP.assert_called_with("ftp.example.com", "username", "password")
    ftp.pwd.assert_called_with()
    ftp.storbinary.assert_called()  # second argument is an internal object


@pytest.mark.asyncio
async def test_publish_last_published(
    mocker: MockerFixture,
    fs: FakeFilesystem,
    root: Path,
    config: Config,
) -> None:
    """
    Test publishing when ``last_published`` is present.
    """
    FTP = mocker.patch("nefelibata.publishers.ftp.FTP")
    ftp = FTP.return_value.__enter__.return_value

    with freeze_time("2021-01-01T00:00:00Z"):
        fs.create_file(root / "build/generic/one", contents="Hello, world!")

    publisher = FTPPublisher(
        root,
        config,
        "generic",
        "ftp.example.com",
        "username",
        "password",
    )

    await publisher.publish(since=datetime(2021, 1, 2, tzinfo=timezone.utc))

    ftp.storbinary.assert_not_called()

    await publisher.publish(force=True)

    ftp.storbinary.assert_called()


@pytest.mark.asyncio
async def test_publish_tls(
    mocker: MockerFixture,
    fs: FakeFilesystem,
    root: Path,
    config: Config,
) -> None:
    """
    Test ``publish`` with TLS.
    """
    FTP_TLS = mocker.patch("nefelibata.publishers.ftp.FTP_TLS")
    ftp = FTP_TLS.return_value.__enter__.return_value
    mocker.patch.object(
        FTPPublisher,
        "find_modified_files",
        return_value=iter([root / "build/generic/one"]),
    )

    fs.create_file(root / "build/generic/one", contents="Hello, world!")

    publisher = FTPPublisher(
        root,
        config,
        "generic",
        "ftp.example.com",
        "username",
        "password",
        use_tls=True,
    )

    await publisher.publish()

    ftp.prot_p.assert_called()


@pytest.mark.asyncio
async def test_publish_with_basedir(
    mocker: MockerFixture,
    fs: FakeFilesystem,
    root: Path,
    config: Config,
) -> None:
    """
    Test ``publish`` when a base directory is specified.
    """
    FTP = mocker.patch("nefelibata.publishers.ftp.FTP")
    ftp = FTP.return_value.__enter__.return_value
    ftp.pwd.return_value = "/ftp/upload"
    mocker.patch.object(
        FTPPublisher,
        "find_modified_files",
        return_value=iter(
            [root / "build/generic/subdir1/one", root / "build/generic/subdir2/two"],
        ),
    )

    fs.create_file(root / "build/generic/subdir1/one", contents="Hello, world!")
    fs.create_file(root / "build/generic/subdir2/two", contents="Goodbye, world!")

    publisher = FTPPublisher(
        root,
        config,
        "generic",
        "ftp.example.com",
        "username",
        "password",
        "ftp/upload",
    )

    await publisher.publish()

    ftp.cwd.assert_has_calls(
        [
            mocker.call("ftp/upload"),
            mocker.call("subdir1"),
            mocker.call("/ftp/upload"),
            mocker.call("subdir2"),
        ],
    )


@pytest.mark.asyncio
async def test_publish_create_directory(
    mocker: MockerFixture,
    fs: FakeFilesystem,
    root: Path,
    config: Config,
) -> None:
    """
    Test ``publish`` when the directories need to be created.
    """
    FTP = mocker.patch("nefelibata.publishers.ftp.FTP")
    ftp = FTP.return_value.__enter__.return_value
    ftp.cwd.side_effect = [ftplib.error_perm, ""]
    mocker.patch.object(
        FTPPublisher,
        "find_modified_files",
        return_value=iter([root / "build/generic/subdir1/one"]),
    )

    fs.create_file(root / "build/generic/subdir1/one", contents="Hello, world!")

    publisher = FTPPublisher(
        root,
        config,
        "generic",
        "ftp.example.com",
        "username",
        "password",
    )

    await publisher.publish()

    ftp.mkd.assert_called_with("subdir1")
