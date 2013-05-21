from twitter import Twitter as Twitter_
from twitter import OAuth
from facepy import GraphAPI


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
    def __init__(self, post,
            consumer_key, consumer_secret, oauth_token, oauth_secret):
        self.post = post

        # create twitter communicator
        auth = OAuth(oauth_token, oauth_secret, consumer_key, consumer_secret)
        self.twitter = Twitter_(auth=auth)

    def announce(self):
        """
        Publish the summary of a post to Twitter.

        """
        if 'twitter-id' not in self.post.post:
            response = self.twitter.statuses.update(
                    status=self.post.summary[:140])
            self.post.post['twitter-id'] = response['id']
            self.post.save()

    def collect(self):
        """
        Collect responses to a given tweet.

        Amazingly there's no support in the API to fetch all replies to a given
        tweet id, so we need to fetch all mentions and see which of them are
        a reply.

        """
        mentions = self.twitter.statuses.mentions_timeline(
                count=200,
                since_id=self.post.post['twitter-id'],
                trim_user=False,
                contributor_details=True,
                include_entities=True)
        for mention in mentions:
            if mention['in_reply_to_status_id_str'] == post:
                mention


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


if __name__ == '__main__':
    t = Twitter(dict(
        consumer_key="2paRtbx3rihL6Bbl54aAw",
        consumer_secret="rUblWfCCDtIXn2IidQMSjRN5Hx8xfkZcGAsf6xhOD54",
        oauth_token="569313051-oFVOkxMQFxus0PjRuED7uvxgb9201DeM9YEf22tt",
        oauth_secret="GygkFTMCulXnhGtlbhCcnuivm2YtrJbbVgmxzpwhHc"))
    t.collect("335472083901497345")
    #result = t('again testing... 1... 2... 3.')
    #print result
    #{u'favorited': False, u'contributors': None, u'truncated': False, u'text': u'again testing... 1... 2... 3.', u'in_reply_to_status_id': None, u'user': {u'follow_request_sent': False, u'profile_use_background_image': True, u'id': 569313051, u'description': None, u'verified': False, u'profile_text_color': u'333333', u'profile_image_url_https': u'https://si0.twimg.com/sticky/default_profile_images/default_profile_6_normal.png', u'profile_sidebar_fill_color': u'DDEEF6', u'is_translator': False, u'entities': {u'description': {u'urls': []}}, u'followers_count': 4, u'protected': False, u'location': None, u'default_profile_image': True, u'listed_count': 0, u'utc_offset': None, u'statuses_count': 2, u'profile_background_color': u'C0DEED', u'friends_count': 0, u'profile_background_image_url_https': u'https://si0.twimg.com/images/themes/theme1/bg.png', u'profile_link_color': u'0084B4', u'profile_image_url': u'http://a0.twimg.com/sticky/default_profile_images/default_profile_6_normal.png', u'notifications': False, u'geo_enabled': False, u'id_str': u'569313051', u'profile_background_image_url': u'http://a0.twimg.com/images/themes/theme1/bg.png', u'screen_name': u'zen_of_data', u'lang': u'en', u'profile_background_tile': False, u'favourites_count': 0, u'name': u'Zen of Data', u'url': None, u'created_at': u'Wed May 02 16:27:34 +0000 2012', u'contributors_enabled': False, u'time_zone': None, u'profile_sidebar_border_color': u'C0DEED', u'default_profile': True, u'following': False}, u'geo': None, u'in_reply_to_user_id_str': None, u'source': u'<a href="http://pypi.python.org/pypi/nefelibata" rel="nofollow">Test nefelibate</a>', u'created_at': u'Fri May 17 19:09:12 +0000 2013', u'retweeted': False, u'coordinates': None, u'id': 335472083901497345, u'entities': {u'user_mentions': [], u'hashtags': [], u'urls': []}, u'in_reply_to_status_id_str': None, u'in_reply_to_screen_name': None, u'in_reply_to_user_id': None, u'place': None, u'retweet_count': 0, u'id_str': u'335472083901497345'}

