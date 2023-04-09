"""
Tests for ``nefelibata.publishers.s3``.
"""
# pylint: disable=invalid-name
from datetime import datetime, timezone
from pathlib import Path

import pytest
from botocore.exceptions import ClientError
from freezegun import freeze_time
from pyfakefs.fake_filesystem import FakeFilesystem
from pytest_mock import MockerFixture

from nefelibata.config import Config
from nefelibata.publishers.s3 import S3Publisher


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
        S3Publisher,
        "find_modified_files",
        return_value=iter(
            [
                root / "build/generic/one/index.html",
                root / "build/generic/one/photo.jpg",
                root / "build/generic/one/blob",
            ],
        ),
    )
    boto3 = mocker.patch("nefelibata.publishers.s3.boto3")

    fs.create_file(root / "build/generic/one", contents="Hello, world!")

    publisher = S3Publisher(
        root,
        config,
        "generic",
        "KEY",
        "SECRET",
        "example.com",
    )

    with freeze_time("2021-01-01T00:00:00Z"):
        publishing = await publisher.publish()
    assert publishing.dict() == {
        "timestamp": datetime(2021, 1, 1, 0, 0, tzinfo=timezone.utc),
    }
    boto3.client.return_value.upload_file.assert_has_calls(
        [
            mocker.call(
                "/path/to/blog/build/generic/one/index.html",
                "example.com",
                "one/index.html",
                ExtraArgs={"ACL": "public-read", "ContentType": "text/html"},
            ),
            mocker.call(
                "/path/to/blog/build/generic/one/photo.jpg",
                "example.com",
                "one/photo.jpg",
                ExtraArgs={"ACL": "public-read", "ContentType": "image/jpeg"},
            ),
            mocker.call(
                "/path/to/blog/build/generic/one/blob",
                "example.com",
                "one/blob",
                ExtraArgs={"ACL": "public-read"},
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
        S3Publisher,
        "find_modified_files",
        return_value=iter([]),
    )
    mocker.patch("nefelibata.publishers.s3.boto3")

    publisher = S3Publisher(
        root,
        config,
        "generic",
        "KEY",
        "SECRET",
        "example.com",
    )

    with freeze_time("2021-01-01T00:00:00Z"):
        publishing = await publisher.publish()
    assert publishing is None


@pytest.mark.asyncio
async def test_publish_error(
    mocker: MockerFixture,
    root: Path,
    config: Config,
) -> None:
    """
    Test ``publish`` when an error occurs.
    """
    mocker.patch.object(
        S3Publisher,
        "find_modified_files",
        return_value=iter([root / "build/generic/one/index.html"]),
    )
    boto3 = mocker.patch("nefelibata.publishers.s3.boto3")
    boto3.client.return_value.upload_file.side_effect = ClientError(
        operation_name="upload_file",
        error_response={"Error": {"Code": 42, "Message": "A wild exception appears!"}},
    )
    _logger = mocker.patch("nefelibata.publishers.s3._logger")

    publisher = S3Publisher(
        root,
        config,
        "generic",
        "KEY",
        "SECRET",
        "example.com",
    )

    with pytest.raises(ClientError) as excinfo:
        await publisher.publish()
    assert str(excinfo.value) == (
        "An error occurred (42) when calling the upload_file operation: "
        "A wild exception appears!"
    )
    _logger.exception.assert_called_with("An error occurred")
