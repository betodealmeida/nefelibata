import operator 

import twitter
from facepy import GraphAPI
from simplejson import load, dump


class Twitter(object):
    """
    Update Twitter status.

    The configuration in nefelibata.yaml should look like this:

        twitter:
            consumer_key: XXX
            consumer_secret: XXX
            oauth_token: XXX
            oauth_secret: XXX

    In order to create consumer_key and consumer_secret you must visit
    https://dev.twitter.com/apps/new and register a new application. There you
    can also request oauth_token and oauth_secret.

    """
    def __init__(self, post, config, username,
            consumer_key, consumer_secret, oauth_token, oauth_secret):
        self.post = post
        self.config = config

        # create twitter communicator
        auth = twitter.OAuth(
                oauth_token, oauth_secret, consumer_key, consumer_secret)
        self.twitter = twitter.Twitter(auth=auth)

    def announce(self):
        """
        Publish the summary of a post to Twitter.

        """
        if 'twitter-id' not in self.post.post:
            response = self.twitter.statuses.update(
                    status=self.post.summary[:140])
            self.post.post['twitter-id'] = response['id_str']
            self.post.save()

    def collect(self):
        """
        Collect responses to a given tweet.

        Amazingly there's no support in the API to fetch all replies to a given
        tweet id, so we need to fetch all mentions and see which of them are
        a reply.

        """
        if 'twitter-id' not in self.post.post:
            return

        # load replies
        directory = self.post.file_path.dirname()
        storage = directory/'twitter.json'
        if storage.exists():
            with open(storage) as fp:
                replies = load(fp)
        else:
            replies = []
        count = len(replies)

        tweet = self.post.post['twitter-id']
        try:
            mentions = self.twitter.statuses.mentions_timeline(
                    count=200,
                    since_id=tweet,
                    trim_user=False,
                    contributor_details=True,
                    include_entities=True)
        except twitter.api.TwitterHTTPError:
            return

        ids = [reply['id'] for reply in replies]
        for mention in mentions:
            if mention['in_reply_to_status_id_str'] == tweet:
                if mention['id'] not in ids:
                    replies.append(mention)

        # save replies
        replies.sort(key=operator.itemgetter('id_str'))
        with open(storage, 'w') as fp:
            dump(replies, fp)

        # touch post for rebuild
        if count < len(replies):
            self.post.save()


class Facebook(object):
    """
    Publish post to facebook.

    The configuration in nefelibata.yaml should look like this:

        facebook:
            access_token: XXX

    Request an access_token at https://developers.facebook.com/tools/explorer/.

    """
    def __init__(self, post, config, username, access_token):
        self.post = post
        self.config = config
        self.graph = GraphAPI(access_token)

    def announce(self):
        if 'facebook-id' not in self.post.post:
            response = self.graph.post(
                path='me/feed',
                message="%s\n\n-- %s%s" % (
                    self.post.summary, self.config['url'], self.post.url))
            self.post.post['facebook-id'] = response['id']
            self.post.save()

    def collect(self):
        if 'facebook-id' not in self.post.post:
            return

        # load replies
        directory = self.post.file_path.dirname()
        storage = directory/'facebook.json'
        if storage.exists():
            with open(storage) as fp:
                replies = load(fp)
        else:
            replies = []
        count = len(replies)
        ids = [reply['id'] for reply in replies]

        post = self.post.post['facebook-id']
        result = self.graph.get(path='/%s' % post)
        for comment in result['comments']['data']:
            # add user info and picture
            comment['from']['info'] = self.graph.get(
                    path='/%s' % comment['from']['id'])
            comment['from']['picture'] = \
                    "http://graph.facebook.com/%s/picture" % (
                            comment['from']['info']['username'])

            if comment['id'] not in ids:
                replies.append(comment)

        # save replies
        replies.sort(key=operator.itemgetter('id'))
        with open(storage, 'w') as fp:
            dump(replies, fp)

        # touch post for rebuild
        if count < len(replies):
            self.post.save()
