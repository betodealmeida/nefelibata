import logging
from typing import Any, Dict, List

import mastodon
from nefelibata.announcers import Announcer
from nefelibata.post import Post

_logger = logging.getLogger("nefelibata")


def get_reply_from_toot(toot: mastodon.AttribAccessDict) -> Dict[str, Any]:
    return {
        "source": "Mastodon",
        "color": "#2b90d9",
        "id": f'mastodon:{toot["uri"]}',
        "timestamp": toot.created_at.timestamp(),
        "user": {
            "name": toot.account.display_name,
            "image": toot.account.avatar,
            "url": toot.account.url,
            "description": toot.account.note,
        },
        "comment": {"text": toot.content, "url": toot.url},
    }


class MastodonAnnouncer(Announcer):

    name = "Mastodon"
    url_header = "mastodon-url"

    def __init__(
        self, post: Post, config: Dict[str, Any], access_token: str, base_url: str
    ):
        super().__init__(post, config)

        self.base_url = base_url

        self.client = mastodon.Mastodon(
            access_token=access_token, api_base_url=base_url
        )

    def announce(self) -> str:
        _logger.info(f"Posting to Mastodon ({self.base_url})")

        language = self.post.parsed.get("language") or self.config["language"]
        post_url = f'{self.config["url"]}{self.post.url}'

        toot = self.client.status_post(
            status=f"{self.post.summary}\n\n{post_url}",
            visibility="public",
            language=language,
            idempotency_key=str(self.post.file_path),
        )
        _logger.info("Success!")

        return toot["url"]

    def collect(self) -> List[Dict[str, Any]]:
        _logger.info(f"Collecting replies from Mastodon ({self.base_url})")

        toot_url = self.post.parsed[self.url_header]
        toot_id = toot_url.rstrip("/").rsplit("/", 1)[1]
        context = self.client.status_context(toot_id)

        replies = []
        for toot in context["descendants"]:
            reply = get_reply_from_toot(toot)
            reply["url"] = toot_url
            replies.append(reply)

        _logger.info("Success!")

        return replies
