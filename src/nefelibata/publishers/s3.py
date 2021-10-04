"""
An S3 publisher.
"""
import logging
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import boto3
from botocore.exceptions import ClientError

from nefelibata.config import Config
from nefelibata.publishers.base import Publisher, Publishing

_logger = logging.getLogger(__name__)


class S3Publisher(Publisher):

    """
    A publisher that uploads the blog to an S3 service
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        root: Path,
        config: Config,
        path: str,
        access_key_id: str,
        secret_access_key: str,
        bucket: str,
        region: str = "us-east-1",
        **kwargs: Any,
    ):
        super().__init__(root, config, path, **kwargs)

        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region,
        )

    async def publish(
        self,
        since: Optional[datetime] = None,
        force: bool = False,
    ) -> Optional[Publishing]:
        build = self.root / "build" / self.path

        modified_files = list(self.find_modified_files(force, since))

        for path in modified_files:
            key = str(path.relative_to(build))
            self._upload_file(path, key)

        if modified_files:
            return Publishing(timestamp=datetime.now(timezone.utc))

        return None

    def _upload_file(self, path: Path, key: str) -> None:
        """
        Upload a file to S3.
        """
        extra_args = {"ACL": "public-read"}
        mimetype = mimetypes.guess_type(str(path))[0]
        if mimetype:
            extra_args["ContentType"] = mimetype

        _logger.info("Uploading %s to %s in S3", path, self.bucket)
        try:
            self.client.upload_file(str(path), self.bucket, key, ExtraArgs=extra_args)
        except ClientError as ex:
            _logger.exception("An error occurred")
            raise ex
