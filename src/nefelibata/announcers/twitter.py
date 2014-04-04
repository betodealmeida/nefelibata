"""Twitter announcer.

This module implements a Twitter announcer, for publishing a post summary to
Twitter and aggregating replies.

"""
from __future__ import absolute_import

import operator

import twitter
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

    def __init__(
            self, post, config, username,
            consumer_key, consumer_secret, oauth_token, oauth_secret):
        """Twitter interaction for a given post."""
        self.post = post
        self.config = config

        # create twitter communicator
        auth = twitter.OAuth(
            oauth_token, oauth_secret, consumer_key, consumer_secret)
        self.twitter = twitter.Twitter(auth=auth)

    def announce(self):
        """Publish the summary of a post to Twitter."""
        if 'twitter-id' not in self.post.post:
            link = "%s%s" % (self.config['url'], self.post.url)
            # shorten url? XXX
            status = "%s %s" % (self.post.summary[:140-1-len(link)], link)
            response = self.twitter.statuses.update(status=status)
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
