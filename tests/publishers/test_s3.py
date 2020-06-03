import os
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any
from typing import Dict
from unittest import mock

from botocore.exceptions import ClientError
from freezegun import freeze_time
from nefelibata.publishers.s3 import S3Publisher

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


config: Dict[str, Any] = {}


def test_create_bucket():
    root = Path("/path/to/blog")

    publisher = S3Publisher(
        root,
        config,
        bucket="blog.example.com",
        AWS_ACCESS_KEY_ID="AWS_ACCESS_KEY_ID",
        AWS_SECRET_ACCESS_KEY="AWS_SECRET_ACCESS_KEY",
        region="us-east-1",
    )

    with mock.patch("nefelibata.publishers.s3.boto3.client") as mock_boto3_client:
        success = publisher._create_bucket()

    assert success
    mock_boto3_client.return_value.create_bucket.assert_called_with(
        Bucket="blog.example.com",
        CreateBucketConfiguration={"LocationConstraint": "us-east-1"},
        ACL="public-read",
    )


def test_create_bucket_error():
    root = Path("/path/to/blog")

    publisher = S3Publisher(
        root,
        config,
        bucket="blog.example.com",
        AWS_ACCESS_KEY_ID="AWS_ACCESS_KEY_ID",
        AWS_SECRET_ACCESS_KEY="AWS_SECRET_ACCESS_KEY",
        region="us-east-1",
    )

    with mock.patch("nefelibata.publishers.s3.boto3.client") as mock_boto3_client:
        mock_boto3_client.return_value.create_bucket.side_effect = ClientError(
            operation_name="create_bucket",
            error_response={"Error": {"Code": "42", "Message": "Some error"}},
        )
        success = publisher._create_bucket()

    assert not success


def test_upload_file():
    root = Path("/path/to/blog")

    publisher = S3Publisher(
        root,
        config,
        bucket="blog.example.com",
        AWS_ACCESS_KEY_ID="AWS_ACCESS_KEY_ID",
        AWS_SECRET_ACCESS_KEY="AWS_SECRET_ACCESS_KEY",
        region="us-east-1",
    )

    file_path = key = "foo/bar.jpg"
    with mock.patch("nefelibata.publishers.s3.boto3.client") as mock_boto3_client:
        success = publisher._upload_file(file_path, key)

    assert success
    mock_boto3_client.return_value.upload_file.assert_called_with(
        "foo/bar.jpg",
        "blog.example.com",
        "foo/bar.jpg",
        ExtraArgs={"ACL": "public-read", "ContentType": "image/jpeg"},
    )


def test_upload_file_no_mimetype():
    root = Path("/path/to/blog")

    publisher = S3Publisher(
        root,
        config,
        bucket="blog.example.com",
        AWS_ACCESS_KEY_ID="AWS_ACCESS_KEY_ID",
        AWS_SECRET_ACCESS_KEY="AWS_SECRET_ACCESS_KEY",
        region="us-east-1",
    )

    file_path = key = "foo/bar"
    with mock.patch("nefelibata.publishers.s3.boto3.client") as mock_boto3_client:
        success = publisher._upload_file(file_path, key)

    assert success
    mock_boto3_client.return_value.upload_file.assert_called_with(
        "foo/bar", "blog.example.com", "foo/bar", ExtraArgs={"ACL": "public-read"},
    )


def test_upload_file_error():
    root = Path("/path/to/blog")

    publisher = S3Publisher(
        root,
        config,
        bucket="blog.example.com",
        AWS_ACCESS_KEY_ID="AWS_ACCESS_KEY_ID",
        AWS_SECRET_ACCESS_KEY="AWS_SECRET_ACCESS_KEY",
        region="us-east-1",
    )

    file_path = key = "foo/bar"
    with mock.patch("nefelibata.publishers.s3.boto3.client") as mock_boto3_client:
        mock_boto3_client.return_value.upload_file.side_effect = ClientError(
            operation_name="upload_file",
            error_response={"Error": {"Code": "42", "Message": "Some error"}},
        )
        success = publisher._upload_file(file_path, key)

    assert not success


def test_configure_website():
    root = Path("/path/to/blog")

    publisher = S3Publisher(
        root,
        config,
        bucket="blog.example.com",
        AWS_ACCESS_KEY_ID="AWS_ACCESS_KEY_ID",
        AWS_SECRET_ACCESS_KEY="AWS_SECRET_ACCESS_KEY",
        region="us-east-1",
    )

    with mock.patch("nefelibata.publishers.s3.boto3.client") as mock_boto3_client:
        publisher._configure_website()

    mock_boto3_client.return_value.put_bucket_website.assert_called_with(
        Bucket="blog.example.com",
        WebsiteConfiguration={"IndexDocument": {"Suffix": "index.html"}},
    )


def test_configure_route53():
    root = Path("/path/to/blog")

    publisher = S3Publisher(
        root,
        config,
        bucket="blog.example.com",
        AWS_ACCESS_KEY_ID="AWS_ACCESS_KEY_ID",
        AWS_SECRET_ACCESS_KEY="AWS_SECRET_ACCESS_KEY",
        region="us-east-1",
    )

    with mock.patch("nefelibata.publishers.s3.boto3.client") as mock_boto3_client:
        mock_boto3_client.return_value.list_hosted_zones.return_value = {
            "HostedZones": [
                {"Name": "foobar.com", "Id": "2"},
                {"Name": "example.com.", "Id": "1"},
            ],
        }
        publisher._configure_route53("blog.example.com.")

    mock_boto3_client.return_value.change_resource_record_sets.assert_called_with(
        HostedZoneId="1",
        ChangeBatch={
            "Changes": [
                {
                    "Action": "UPSERT",
                    "ResourceRecordSet": {
                        "Name": "blog.example.com",
                        "Type": "CNAME",
                        "SetIdentifier": "nefelibata",
                        "Region": "us-east-1",
                        "TTL": 600,
                        "ResourceRecords": [
                            {
                                "Value": "blog.example.com.s3-website-us-east-1.amazonaws.com",
                            },
                        ],
                    },
                },
            ],
        },
    )


def test_configure_route53_no_zone():
    root = Path("/path/to/blog")

    publisher = S3Publisher(
        root,
        config,
        bucket="blog.example.com",
        AWS_ACCESS_KEY_ID="AWS_ACCESS_KEY_ID",
        AWS_SECRET_ACCESS_KEY="AWS_SECRET_ACCESS_KEY",
        region="us-east-1",
    )

    with mock.patch("nefelibata.publishers.s3.boto3.client") as mock_boto3_client:
        mock_boto3_client.return_value.list_hosted_zones.return_value = {
            "HostedZones": [
                {"Name": "foobar.com", "Id": "2"},
                {"Name": "foobaz.com.", "Id": "1"},
            ],
        }
        publisher._configure_route53("blog.example.com.")

    mock_boto3_client.return_value.change_resource_record_sets.assert_not_called()


def test_publish(fs):
    root = Path("/path/to/blog")
    fs.create_dir(root)

    publisher = S3Publisher(
        root,
        config,
        bucket="blog.example.com",
        AWS_ACCESS_KEY_ID="AWS_ACCESS_KEY_ID",
        AWS_SECRET_ACCESS_KEY="AWS_SECRET_ACCESS_KEY",
        configure_website=True,
        configure_route53="blog.example.com.",
        region="us-east-1",
    )

    with freeze_time("2020-01-01T00:00:00Z"):
        fs.create_file(root / "last_published")

    # create 2 posts, 1 of them up-to-date
    fs.create_dir(root / "build")
    with freeze_time("2019-12-31T00:00:00Z"):
        fs.create_dir(root / "build/one")
        fs.create_file(root / "build/one/index.html")
    with freeze_time("2020-01-02T00:00:00Z"):
        fs.create_dir(root / "build/two")
        fs.create_file(root / "build/two/index.html")

    with freeze_time("2020-01-03T00:00:00Z"):
        with mock.patch("nefelibata.publishers.s3.boto3.client") as mock_boto3_client:
            mock_boto3_client.return_value.list_hosted_zones.return_value = {
                "HostedZones": [
                    {"Name": "foobar.com", "Id": "2"},
                    {"Name": "example.com.", "Id": "1"},
                ],
            }
            publisher.publish()

    mock_boto3_client.return_value.upload_file.assert_called_once_with(
        "/path/to/blog/build/two/index.html",
        "blog.example.com",
        "two/index.html",
        ExtraArgs={"ACL": "public-read", "ContentType": "text/html"},
    )
    mtime = (root / "last_published").stat().st_mtime
    assert (
        datetime.fromtimestamp(mtime).astimezone(timezone.utc).isoformat()
        == "2020-01-03T00:00:00+00:00"
    )


def test_publish_no_last_published(fs):
    root = Path("/path/to/blog")
    fs.create_dir(root)

    publisher = S3Publisher(
        root,
        config,
        bucket="blog.example.com",
        AWS_ACCESS_KEY_ID="AWS_ACCESS_KEY_ID",
        AWS_SECRET_ACCESS_KEY="AWS_SECRET_ACCESS_KEY",
        region="us-east-1",
    )

    # create 2 posts
    fs.create_dir(root / "build")
    with freeze_time("2019-12-31T00:00:00Z"):
        fs.create_dir(root / "build/one")
        fs.create_file(root / "build/one/index.html")
    with freeze_time("2020-01-02T00:00:00Z"):
        fs.create_dir(root / "build/two")
        fs.create_file(root / "build/two/index.html")

    with freeze_time("2020-01-03T00:00:00Z"):
        with mock.patch("nefelibata.publishers.s3.boto3.client") as mock_boto3_client:
            publisher.publish()

    mock_boto3_client.return_value.upload_file.assert_has_calls(
        [
            mock.call(
                "/path/to/blog/build/two/index.html",
                "blog.example.com",
                "two/index.html",
                ExtraArgs={"ACL": "public-read", "ContentType": "text/html"},
            ),
            mock.call(
                "/path/to/blog/build/one/index.html",
                "blog.example.com",
                "one/index.html",
                ExtraArgs={"ACL": "public-read", "ContentType": "text/html"},
            ),
        ],
    )
    mtime = (root / "last_published").stat().st_mtime
    assert (
        datetime.fromtimestamp(mtime).astimezone(timezone.utc).isoformat()
        == "2020-01-03T00:00:00+00:00"
    )


def test_publish_broken_symlink(fs):
    root = Path("/path/to/blog")
    fs.create_dir(root)

    publisher = S3Publisher(
        root,
        config,
        bucket="blog.example.com",
        AWS_ACCESS_KEY_ID="AWS_ACCESS_KEY_ID",
        AWS_SECRET_ACCESS_KEY="AWS_SECRET_ACCESS_KEY",
        region="us-east-1",
    )

    # create 2 posts
    fs.create_dir(root / "build")
    with freeze_time("2019-12-31T00:00:00Z"):
        fs.create_dir(root / "build/one")
        fs.create_file(root / "build/one/index.html")
    with freeze_time("2020-01-02T00:00:00Z"):
        fs.create_dir(root / "build/two")
        fs.create_file(root / "build/two/index.html")

    os.symlink(root / "posts/non-existent", root / "build/three")

    with freeze_time("2020-01-03T00:00:00Z"):
        with mock.patch("nefelibata.publishers.s3.boto3.client") as mock_boto3_client:
            publisher.publish()

    mock_boto3_client.return_value.upload_file.assert_has_calls(
        [
            mock.call(
                "/path/to/blog/build/two/index.html",
                "blog.example.com",
                "two/index.html",
                ExtraArgs={"ACL": "public-read", "ContentType": "text/html"},
            ),
            mock.call(
                "/path/to/blog/build/one/index.html",
                "blog.example.com",
                "one/index.html",
                ExtraArgs={"ACL": "public-read", "ContentType": "text/html"},
            ),
        ],
    )

    mtime = (root / "last_published").stat().st_mtime
    assert (
        datetime.fromtimestamp(mtime).astimezone(timezone.utc).isoformat()
        == "2020-01-03T00:00:00+00:00"
    )
