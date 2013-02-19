from twitter import Twitter as Twitter_
from twitter import OAuth
from facepy import GraphAPI


class Twitter(object):
    """
    Update Twitter status.

    The configuration in nefelibata.yaml should look like this:

        twitter:
            CONSUMER_KEY: XXX
            CONSUMER_SECRET: XXX
            oauth_token: XXX
            oauth_secret: XXX

    In order to create CONSUMER_KEY and CONSUMER_SECRET you must visit
    https://dev.twitter.com/apps/new and register a new application. There you
    can also request oauth_token and oauth_secret.

    """
    def __init__(self, config):
        self.config = config

    def __call__(self, message):
        twitter = Twitter_(auth=OAuth(**self.config))
        return twitter.statuses.update(message)


class Facebook(object):
    """
    Publish post to facebook.

    The configuration in nefelibata.yaml should look like this:

        facebook:
            access_token: XXX

    Request an access_token at https://developers.facebook.com/tools/explorer/.

    """
    def __init__(self, config):
        self.config = config

    def __call__(self, message):
        graph = GraphAPI(self.config['access_token'])
        return graph.post(path='me/feed', message=message)

