"""
A CAPCOM (gemini://gemini.circumlunar.space/capcom/) announcer.
"""
import logging
import re
import ssl
import urllib.parse
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from aiogemini.client import Client
from aiogemini.security import TOFUContext
from yarl import URL

from nefelibata.announcers.base import Announcement, Announcer, Interaction
from nefelibata.builders.base import Builder, Scope
from nefelibata.post import Post, get_posts
from nefelibata.typing import Config

_logger = logging.getLogger(__name__)


class CAPCOMAnnouncer(Announcer):

    """
    A CAPCOM (gemini://gemini.circumlunar.space/capcom/) announcer.

    This requires the Gemini builder, and assumes that the Gemlog feed is
    at ``{builder.home}/feed{builder.extension}``.
    """

    scopes = [Scope.SITE]

    def __init__(
        self, root: Path, config: Config, builders: List[Builder], **kwargs: Any
    ):
        super().__init__(root, config, builders, **kwargs)

        self.client = Client(TOFUContext({}))

    async def announce_post(self, post: Post) -> Optional[Announcement]:
        pass

    async def announce_site(self) -> Optional[Announcement]:
        """
        Send the link to CAPCOM.
        """
        for builder in self.builders:
            if not builder.home.startswith("gemini://"):
                raise Exception("CAPCOM announcer only works with `gemini://` builds")

            feed_url = urllib.parse.quote_plus(
                f"{builder.home}/feed{builder.extension}",
            )
            url = f"gemini://gemini.circumlunar.space/capcom/submit?{feed_url}"

            _logger.info("Announcing feed %s to CAPCOM", feed_url)
            await self.client.get(URL(url))

        return Announcement(
            uri="gemini://gemini.circumlunar.space/capcom/",
            timestamp=datetime.now(timezone.utc),
        )

    async def collect_post(self, post: Post) -> Dict[str, Interaction]:
        return {}

    async def collect_site(self) -> Dict[Path, Dict[str, Interaction]]:
        """
        Return replies to posts.

        This is done by scraping CAPCOM and searching for "Re: " posts.
        """
        response = await self.client.get(
            URL("gemini://gemini.circumlunar.space/capcom/"),
        )
        payload = await response.read()
        content = payload.decode("utf-8")

        posts = get_posts(self.root, self.config)

        interactions: Dict[Path, Dict[str, Interaction]] = defaultdict(dict)
        for line in content.split("\n"):
            if not line.startswith("=>"):
                continue

            _, uri, name = re.split(r"\s+", line, 2)
            for post in posts:
                reply = f"Re: {post.title}"
                if reply in name and await self._link_in_post(post.url, uri):
                    id_ = f"reply,{uri}"
                    interactions[post.path][id_] = Interaction(
                        id=id_,
                        name=name,
                        uri=uri,
                        type="reply",
                    )

        return interactions

    async def _link_in_post(self, post_url: str, uri: str) -> bool:
        """
        Check that a given URI actually links to the post URL.
        """
        try:
            response = await self.client.get(URL(uri))
        except ssl.SSLCertVerificationError:
            return True

        payload = await response.read()
        content = payload.decode("utf-8")

        for line in content.split("\n"):
            if line.startswith("=>") and post_url in line:
                return True

        return False
