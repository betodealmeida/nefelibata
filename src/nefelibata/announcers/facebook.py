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

    """
    def __init__(self, post, config, username, access_token):
        self.post = post
        self.config = config
        self.graph = GraphAPI(access_token)

    def announce(self):
        if 'facebook-id' not in self.post.post:
            response = self.graph.post(
                path='me/feed',
                message="%s\n\n%s%s" % (
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
