from boto.s3.connection import S3Connection
from boto.s3.key import Key


class S3(object):
    """
    Publish blog to an S3 bucket.

    """
    def __init__(self, bucket, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY):
        self.bucket = bucket
        self.AWS_ACCESS_KEY_ID = AWS_ACCESS_KEY_ID
        self.AWS_SECRET_ACCESS_KEY = AWS_SECRET_ACCESS_KEY

    def publish(self, build):
        conn = S3Connection()
        bucket = conn.create_bucket(self.bucket, policy='public-read')

        for filepath in build.walkfiles():
            k = Key(bucket)
            k.key = filepath
            k.set_contents_from_filename(filepath, policy='public-read')

        bucket.configure_website('index.html')
