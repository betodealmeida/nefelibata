import logging
import urllib.parse
from datetime import timezone
from pathlib import Path
from typing import Any
from typing import cast
from typing import Dict
from typing import List

import mastodon
from nefelibata.announcers import Announcer
from nefelibata.announcers import Response
from nefelibata.post import Post

_logger = logging.getLogger(__name__)


def get_response_from_toot(toot: mastodon.AttribAccessDict) -> Response:
    return {
        "source": "Mastodon",
        "color": "#2b90d9",
        "id": f'mastodon:{toot["uri"]}',
        "timestamp": toot.created_at.astimezone(timezone.utc).isoformat(),
        "user": {
            "name": toot.account.display_name,
            "image": toot.account.avatar,
            "url": toot.account.url,
            "description": toot.account.note,
        },
        "comment": {"text": toot.content, "url": toot.url},
    }


class MastodonAnnouncer(Announcer):

    id = "mastodon"
    name = "Mastodon"
    url_header = "mastodon-url"

    def __init__(
        self, root: Path, config: Dict[str, Any], access_token: str, base_url: str,
    ):
        super().__init__(root, config)

        self.base_url = base_url

        self.client = mastodon.Mastodon(
            access_token=access_token, api_base_url=base_url,
        )

    def announce(self, post: Post) -> str:
        _logger.info(f"Posting to Mastodon ({self.base_url})")

        language = post.parsed.get("language") or self.config["language"]
        post_url = urllib.parse.urljoin(self.config["url"], post.url)

        toot = self.client.status_post(
            status=f"{post.summary}\n\n{post_url}",
            visibility="public",
            language=language,
            idempotency_key=str(post.file_path),
        )
        _logger.info("Success!")

        return cast(str, toot["url"])

    def collect(self, post: Post) -> List[Response]:
        _logger.info(f"Collecting replies from Mastodon ({self.base_url})")

        toot_url = post.parsed[self.url_header]
        toot_id = toot_url.rstrip("/").rsplit("/", 1)[1]
        context = self.client.status_context(toot_id)

        responses = []
        for toot in context["descendants"]:
            response = get_response_from_toot(toot)
            response["url"] = toot_url
            responses.append(response)

        _logger.info("Success!")

        return responses
