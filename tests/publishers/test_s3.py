from unittest import mock

from botocore.exceptions import ClientError
from nefelibata.publishers.s3 import S3Publisher

__author__ = "Beto Dealmeida"
__copyright__ = "Beto Dealmeida"
__license__ = "mit"


def test_create_bucket():
    publisher = S3Publisher(
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
    publisher = S3Publisher(
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
    publisher = S3Publisher(
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
    publisher = S3Publisher(
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
    publisher = S3Publisher(
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
    publisher = S3Publisher(
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
    publisher = S3Publisher(
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
    publisher = S3Publisher(
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
