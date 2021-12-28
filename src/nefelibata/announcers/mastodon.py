"""
A Mastodon announcer.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from mastodon import Mastodon, MastodonNotFoundError

from nefelibata.announcers.base import (
    Announcement,
    Announcer,
    Author,
    Interaction,
    Scope,
)
from nefelibata.builders.base import Builder
from nefelibata.config import Config
from nefelibata.post import Post

_logger = logging.getLogger(__name__)

VALID_MIMETYPES = {"audio/mpeg", "image/jpeg"}
MAX_NUMBER_OF_ENCLOSURES = 4


class MastodonAnnouncer(Announcer):

    """
    A Mastodon announcer.
    """

    scopes = [Scope.POST]

    def __init__(  # pylint: disable=too-many-arguments
        self,
        root: Path,
        config: Config,
        builders: List[Builder],
        access_token: str,
        base_url: str,
        **kwargs: Any,
    ):
        super().__init__(root, config, builders, **kwargs)

        self.base_url = base_url

        self.client = Mastodon(
            access_token=access_token,
            api_base_url=base_url,
        )

    async def announce_post(self, post: Post) -> Optional[Announcement]:
        valid_enclosures = [
            enclosure
            for enclosure in post.enclosures
            if enclosure.type in VALID_MIMETYPES
        ]
        if len(valid_enclosures) > MAX_NUMBER_OF_ENCLOSURES:
            _logger.warning(
                "Found more than %d media enclosures in post %s. Only the first "
                "%d will be uploaded.",
                MAX_NUMBER_OF_ENCLOSURES,
                post.path,
                MAX_NUMBER_OF_ENCLOSURES,
            )

        media_ids = []
        for enclosure in valid_enclosures[:MAX_NUMBER_OF_ENCLOSURES]:
            _logger.info("Uploading post enclosure %s", enclosure.path)

            media_dict = self.client.media_post(
                str(enclosure.path),
                enclosure.type,
                enclosure.description,
            )
            media_ids.append(media_dict)

        language = post.metadata.get("language") or self.config.language
        summary = post.metadata.get("summary") or post.title
        urls = "\n".join(
            builder.absolute_url(post).human_repr() for builder in self.builders
        )
        status = f"{summary}\n\n{urls}"

        _logger.info("Announcing post %s on Mastodon", post.path)
        toot_dict = self.client.status_post(
            status=status,
            visibility="public",
            media_ids=media_ids,
            language=language,
            idempotency_key=str(post.path),
        )

        return Announcement(
            url=toot_dict.url,
            timestamp=toot_dict.created_at,
        )

    async def collect_post(self, post: Post) -> Dict[str, Interaction]:
        interactions: Dict[str, Interaction] = {}

        announcements = post.metadata.get("announcements", {})
        for announcement in announcements.values():
            if not announcement["url"].startswith(self.base_url):
                continue

            url = announcement["url"]
            id_ = int(url.rstrip("/").rsplit("/", 1)[1])
            try:
                context = self.client.status_context(id_)
            except MastodonNotFoundError:
                _logger.warning("Toot %s not found", url)
                continue

            # map from instance ID to URL
            id_map = {id_: url}

            for descendant in context["descendants"]:
                id_ = descendant["url"]
                id_map[descendant["id"]] = id_
                interactions[str(id_)] = Interaction(
                    id=descendant["uri"],
                    name=descendant["url"],
                    summary=None,
                    content=descendant["content"],
                    published=descendant["created_at"],
                    updated=None,
                    author=Author(
                        name=descendant["account"]["display_name"],
                        url=descendant["account"]["url"],
                        avatar=descendant["account"]["avatar"],
                        note=descendant["account"]["note"],
                    ),
                    url=descendant["url"],
                    in_reply_to=id_map[descendant["in_reply_to_id"]],
                    type="reply",
                )

        return interactions
