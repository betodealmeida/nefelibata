import logging
import urllib.parse
from datetime import timezone
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List

import dateutil.parser
import twitter
from nefelibata.announcers import Announcer
from nefelibata.announcers import Response
from nefelibata.post import Post

_logger = logging.getLogger(__name__)

max_length = 280


def get_response_from_mention(tweet: Dict[str, Any]) -> Response:
    """Generate a standard reply from a Tweet.
    """
    return {
        "source": "Twitter",
        "color": "#00acee",
        "id": f'twitter:{tweet["id_str"]}',
        "timestamp": dateutil.parser.parse(tweet["created_at"])
        .astimezone(timezone.utc)
        .isoformat(),
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

    id = "twitter"
    name = "Twitter"
    url_header = "twitter-url"

    def __init__(
        self,
        root: Path,
        config: Dict[str, Any],
        handle: str,
        consumer_key: str,
        consumer_secret: str,
        oauth_token: str,
        oauth_secret: str,
    ):
        super().__init__(root, config)

        self.oauth_token = oauth_token
        self.oauth_secret = oauth_secret
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret

    def announce(self, post: Post) -> str:
        """Publish the summary of a post to Twitter.
        """
        _logger.info("Posting to Twitter")

        auth = twitter.OAuth(
            self.oauth_token,
            self.oauth_secret,
            self.consumer_key,
            self.consumer_secret,
        )
        client = twitter.Twitter(auth=auth)

        post_url = urllib.parse.urljoin(self.config["url"], post.url)
        if "twitter_card" in self.config["assistants"]:
            status = post_url
        else:
            status = f"{post.summary[: max_length - 1 - len(post_url)]} {post_url}"
        response = client.statuses.update(status=status)
        _logger.info("Success!")

        return f'https://twitter.com/{response["user"]["screen_name"]}/status/{response["id_str"]}'

    def collect(self, post: Post) -> List[Response]:
        """Collect responses to a given tweet.

        Amazingly there's no support in the API to fetch all replies to a given
        tweet id, so we need to fetch all mentions and see which of them are
        a reply.
        """
        _logger.info("Collecting replies from Twitter")

        auth = twitter.OAuth(
            self.oauth_token,
            self.oauth_secret,
            self.consumer_key,
            self.consumer_secret,
        )
        client = twitter.Twitter(auth=auth)

        tweet_url = post.parsed[self.url_header]
        tweet_id = tweet_url.rstrip("/").rsplit("/", 1)[1]
        try:
            mentions = client.statuses.mentions_timeline(
                count=200,
                since_id=tweet_id,
                trim_user=False,
                contributor_details=True,
                include_entities=True,
            )
        except Exception:
            return []

        responses = []
        for mention in mentions:
            if mention["in_reply_to_status_id_str"] == tweet_id:
                response = get_response_from_mention(mention)
                response["url"] = tweet_url
                responses.append(response)

        _logger.info("Success!")

        return responses
