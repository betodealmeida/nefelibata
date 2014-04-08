"""Facebook announcer.

This module implements a Facebook announcer, for publishing a  post summary to
Facebook and aggregating replies.

"""
import operator

from facepy import GraphAPI
from simplejson import load, dump


class Facebook(object):

    """
    Publish post to facebook.

    The configuration in nefelibata.yaml should look like this:

        facebook:
            access_token: XXX

    Request an access_token at https://developers.facebook.com/tools/explorer/.

    More info on the API here:

        https://developers.facebook.com/docs/graph-api/reference/user/feed

    """

    def __init__(self, post, config, username, access_token):
        """Facebook interaction for a given post."""
        self.post = post
        self.config = config
        self.graph = GraphAPI(access_token)

    def announce(self):
        """Publish the summary of a post to Facebook."""
        if 'facebook-id' not in self.post.post:
            # grab post img
            img = self.post.parsed.xpath('//img')
            if img:
                picture = img[0].attrib['src']
            else:
                picture = None

            response = self.graph.post(
                path='me/feed',
                message=self.post.summary,
                link="%s/%s" % (self.config['url'], self.post.url),
                name=self.post.title,
                picture=picture,
            )
            self.post.post['facebook-id'] = response['id']
            self.post.save()

    def collect(self):
        """Collect responses to a given post."""
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
        if "comments" not in result:
            return

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
