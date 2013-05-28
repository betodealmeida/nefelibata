from boto.s3.connection import S3Connection
from boto.route53.connection import Route53Connection
from boto.route53.record import ResourceRecordSets
from boto.s3.key import Key


class S3(object):
    """
    Publish blog to an S3 bucket.

    TODO: specify region (https://gist.github.com/garnaat/833135)

    """
    def __init__(self, bucket, configure_website, configure_route53,
            AWS_ACCESS_KEY_ID=None, AWS_SECRET_ACCESS_KEY=None):
        self.bucket = bucket
        self.configure_website = configure_website
        self.configure_route53 = configure_route53
        self.AWS_ACCESS_KEY_ID = AWS_ACCESS_KEY_ID
        self.AWS_SECRET_ACCESS_KEY = AWS_SECRET_ACCESS_KEY

    def publish(self, build):
        # publish files
        conn = S3Connection(
                self.AWS_ACCESS_KEY_ID, self.AWS_SECRET_ACCESS_KEY)
        bucket = conn.create_bucket(self.bucket, policy='public-read')
        for filepath in build.walkfiles():
            k = Key(bucket)
            k.key = filepath[len(build)+1:]  # relative path
            k.set_contents_from_filename(filepath, policy='public-read')

        # configure site
        if self.configure_website:
            bucket.configure_website('index.html')

        # configure DNS
        if self.configure_route53:
            # we'll create a CNAME record
            name = self.configure_route53 + '.'
            value = bucket.get_website_endpoint()
            route53 = Route53Connection(
                    self.AWS_ACCESS_KEY_ID, self.AWS_SECRET_ACCESS_KEY)
            zones = route53.get_all_hosted_zones()
            for zone in zones['ListHostedZonesResponse']['HostedZones']:
                if name.endswith(zone['Name']):
                    zone_id = zone['Id'].split('/')[-1]

                    # check for pre-existing records
                    records = []
                    for rrset in route53.get_all_rrsets(zone_id):
                        if rrset.name == name:
                            records = rrset.resource_records
                            ttl = rrset.ttl
                    changes = ResourceRecordSets(route53, zone_id)

                    # check if we need to set a record
                    if value not in records:
                        # delete old records
                        for record in records:
                            change = changes.add_change(
                                    "DELETE", name, "CNAME", ttl=ttl)
                            change.add_value(record)

                        # add new
                        change = changes.add_change("CREATE", name, "CNAME")
                        change.add_value(value)
                        changes.commit()

        print 'Published!'
