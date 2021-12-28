"""
An announcer for gemlogs.
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

from nefelibata.announcers.base import Announcement, Announcer, Interaction, Scope
from nefelibata.builders.base import Builder
from nefelibata.config import Config
from nefelibata.post import get_posts

_logger = logging.getLogger(__name__)


class GemlogAnnouncer(Announcer):

    """
    A generic gemlog announcer.

    This requires the Gemini builder, and assumes that the Gemlog feed is
    at ``{builder.home}/feed{builder.extension}``.
    """

    scopes = [Scope.SITE]

    # Replace these with values from the place where you want to announce the
    # feed.
    name = ""
    url = "gemini://example.com/"
    submit_url = "gemini://example.com/submit?"
    # Set up an expiration to prevent the announcement to made too frequently;
    # eg, for CAPCOM we only need announce the feed once, while for Antenna we
    # need to announce it on every change.
    grace_seconds = 0

    # Replace with a specific logger to have better logs
    logger = _logger

    def __init__(
        self, root: Path, config: Config, builders: List[Builder], **kwargs: Any
    ):
        super().__init__(root, config, builders, **kwargs)

        self.client = Client(TOFUContext({}))

    async def announce_site(self) -> Optional[Announcement]:
        """
        Send the link.
        """
        for builder in self.builders:
            if builder.home.scheme != "gemini":
                raise Exception(
                    f"{self.name} announcer only works with `gemini://` builds",
                )

            feed_url = urllib.parse.quote_plus(
                f"{builder.home}/feed{builder.extension}",
            )
            url = self.submit_url + feed_url

            self.logger.info("Announcing feed %s to %s", feed_url, self.name)
            await self.client.get(URL(url))

        return Announcement(
            url=self.url,
            timestamp=datetime.now(timezone.utc),
            grace_seconds=self.grace_seconds,
        )

    async def collect_site(self) -> Dict[Path, Dict[str, Interaction]]:
        """
        Return replies to posts.

        This is done by scraping the capsule and searching for "Re: " posts.
        """
        response = await self.client.get(URL(self.url))
        payload = await response.read()
        content = payload.decode("utf-8")

        posts = get_posts(self.root, self.config)

        interactions: Dict[Path, Dict[str, Interaction]] = defaultdict(dict)
        for line in content.split("\n"):
            if not line.startswith("=>"):
                continue

            _, url, name = re.split(r"\s+", line, 2)
            for post in posts:
                reply = f"Re: {post.title}"
                if reply in name and await self._link_in_post(post.url, url):
                    id_ = f"reply,{url}"
                    interactions[post.path][id_] = Interaction(
                        id=id_,
                        name=name,
                        url=url,
                        type="reply",
                    )

        return interactions

    async def _link_in_post(self, post_url: str, url: str) -> bool:
        """
        Check that a given URL actually links to the post URL.
        """
        try:
            response = await self.client.get(URL(url))
        except ssl.SSLCertVerificationError:
            return True

        payload = await response.read()
        content = payload.decode("utf-8")

        for line in content.split("\n"):
            if line.startswith("=>") and post_url in line:
                return True

        return False
