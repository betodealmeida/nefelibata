import logging
from pathlib import Path
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

from nefelibata.publishers import Publisher


class S3Publisher(Publisher):
    def __init__(
        self,
        bucket: str,
        AWS_ACCESS_KEY_ID: str,
        AWS_SECRET_ACCESS_KEY: str,
        configure_website: bool = False,
        configure_route53: str = None,
        region: str = None,
    ):
        self.bucket = bucket
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=region,
        )
        self.configure_website = configure_website
        self.configure_route53 = configure_route53
        self.region = region

    def publish(self, root: Path) -> None:
        self._create_bucket()

        build = root / "build"
        queue = [build]
        # manually walk, since `glob("**/*")` doesn't follow symlinks
        while queue:
            current = queue.pop()
            for path in current.glob("*"):
                if path.is_dir():
                    queue.append(path)
                else:
                    key = str(path.relative_to(build))
                    self._upload_file(path, key)

        if self.configure_website:
            website_configuration = {
                'IndexDocument': {'Suffix': 'index.html'},
            }
            self.s3_client.put_bucket_website(
                Bucket=self.bucket,
                WebsiteConfiguration=website_configuration
            )

        if self.configure_route53:
            pass


    def _upload_file(self, path: Path, key: str) -> bool:
        logging.info(f"Uploading {path}")
        try:
            self.s3_client.upload_file(str(path), self.bucket, key, ExtraArgs={'ACL': 'public-read'})
        except ClientError as e:
            logging.error(e)
            return False
        return True

    def _create_bucket(self) -> bool:
        logging.info(f"Creating bucket {self.bucket}")
        try:
            if self.region is None:
                self.s3_client.create_bucket(
                    Bucket=self.bucket, ACL="public-read"
                )
            else:
                location = {"LocationConstraint": region}
                self.s3_client.create_bucket(
                    Bucket=self.bucket,
                    CreateBucketConfiguration=location,
                    ACL="public-read",
                )
        except ClientError as e:
            logging.error(e)
            return False
        return True
