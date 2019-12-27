import json
import logging
import operator
from typing import Any, Dict

import dateutil.parser
import twitter

from nefelibata.announcers import Announcer
from nefelibata.post import Post

_logger = logging.getLogger("nefelibata")

max_length = 280


def reply_from_mention(tweet: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a standard reply from a Tweet.

    Args:
      tweet (Dict[str, any]): The tweet response from the Twitter API
    """
    return {
        "source": "Twitter",
        "color": "#00acee",
        "id": f'twitter:{tweet["id_str"]}',
        "timestamp": dateutil.parser(tweet["created_at"]).timestamp(),
        "user": {
            "name": tweet["user"]["name"],
            "image": tweet["user"]["profile_image_url_https"],
            "url": tweet["user"]["url"],
            "description": tweet["user"]["description"],
        },
        "comment": {
            "text": tweet["text"],
            "url": f'https://twitter.com/{tweet["user"]["screen_name"]}/status/{tweet["id_str"]}',
        },
    }


class TwitterAnnouncer(Announcer):

    """A Twitter announcer/collector.

    The configuration in nefelibata.yaml should look like this:

        twitter:
            consumer_key: XXX
            consumer_secret: XXX
            oauth_token: XXX
            oauth_secret: XXX

    In order to create consumer_key and consumer_secret you must visit
    https://dev.twitter.com/apps/new and register a new application. Then
    you should run the following script to get oauth_token and oauth_secret:

        import os
        from twitter import *

        CONSUMER_KEY = "XXX"
        CONSUMER_SECRET = "XXX"
        oauth_dance("My App Name", CONSUMER_KEY, CONSUMER_SECRET, "secret.txt")

    After running the script and following the instructions oauth_token and
    oauth_secret will be stored in `secret.txt`.

    """

    name = "Twitter"

    def __init__(
        self,
        post: Post,
        config: Dict[str, Any],
        consumer_key: str,
        consumer_secret: str,
        oauth_token: str,
        oauth_secret: str,
    ):
        self.post = post
        self.config = config

        auth = twitter.OAuth(oauth_token, oauth_secret, consumer_key, consumer_secret)
        self.client = twitter.Twitter(auth=auth)

    def announce(self) -> None:
        """Publish the summary of a post to Twitter.
        """
        if "twitter-url" not in self.post.parsed:
            _logger.info("Announcing post on Twitter")
            link = "%s%s" % (self.config["url"], self.post.url)
            status = "%s %s" % (self.post.summary[: max_length - 1 - len(link)], link)
            response = self.client.statuses.update(status=status)
            self.post.parsed[
                "twitter-url"
            ] = f'https://twitter.com/{response["user"]["screen_name"]}/status/{response["id_str"]}'
            self.post.save()
            _logger.info("Success!")

    def collect(self) -> None:
        """Collect responses to a given tweet.

        Amazingly there's no support in the API to fetch all replies to a given
        tweet id, so we need to fetch all mentions and see which of them are
        a reply.
        """
        _logger.info("Collecting replies from Twitter")

        if "twitter-url" not in self.post.parsed:
            return

        post_directory = self.post.file_path.parent
        storage = post_directory / "replies.json"
        if storage.exists():
            with open(storage) as fp:
                replies = json.load(fp)
        else:
            replies = []
        count = len(replies)

        tweet_url = self.post.parsed["twitter-url"]
        tweet_id = tweet_url.rstrip("/").rsplit("/", 1)[1]
        try:
            mentions = self.client.statuses.mentions_timeline(
                count=200,
                since_id=tweet_id,
                trim_user=False,
                contributor_details=True,
                include_entities=True,
            )
        except twitter.api.TwitterHTTPError:
            return

        ids = {reply["id"] for reply in replies}
        for mention in mentions:
            if (
                mention["in_reply_to_status_id_str"] == tweet_id
                and mention["id"] not in ids
            ):
                replies.append(reply_from_tweet(mention))

        if len(replies) > count:
            replies.sort(key=operator.itemgetter("timestamp"))
            with open(storage, "w") as fp:
                json.dump(replies, fp)
            self.post.save()
