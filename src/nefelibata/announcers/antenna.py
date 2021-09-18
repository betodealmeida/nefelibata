"""
An Antenna (gemini://warmedal.se/~antenna/) announcer.
"""
import logging
import re
import urllib.parse
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from aiogemini.client import Client
from aiogemini.security import TOFUContext
from yarl import URL

from nefelibata.announcers.base import Announcement, Announcer, Interaction
from nefelibata.builders.base import Scope
from nefelibata.post import Post, get_posts
from nefelibata.typing import Config

_logger = logging.getLogger(__name__)


class AntennaAnnouncer(Announcer):

    """
    An Antenna (gemini://warmedal.se/~antenna/) announcer.

    This requires the Gemini builder, and assumes that the Gemlog feed is
    at ``{home}/feed.gmi``.
    """

    scopes = [Scope.SITE]

    def __init__(self, root: Path, config: Config, **kwargs: Any):
        super().__init__(root, config, **kwargs)
        self.client = Client(TOFUContext({}))

    async def announce_post(self, post: Post) -> Optional[Announcement]:
        pass

    async def announce_site(self) -> Optional[Announcement]:
        """
        Send the link to Antenna.
        """
        # Potentially a user could have multiple Gemini builders configured,
        # so we announce all of them.
        for name, builder in self.config["builders"].items():
            if builder["plugin"] == "gemini":
                home = builder["home"].rstrip("/")

                feed_url = urllib.parse.quote_plus(f"{home}/feed.gmi")
                url = f"gemini://warmedal.se/~antenna/submit?{feed_url}"

                _logger.info("Announcing feed %s (%s) to Antenna", feed_url, name)
                await self.client.get(URL(url))

        return Announcement(
            uri="gemini://warmedal.se/~antenna/",
            timestamp=datetime.now(timezone.utc),
        )

    async def collect_post(self, post: Post) -> Dict[str, Interaction]:
        return {}

    async def collect_site(self) -> Dict[Path, Dict[str, Interaction]]:
        """
        Return replies to posts.

        This is done by scraping Antenna and searching for "Re: " posts.
        """
        response = await self.client.get(URL("gemini://warmedal.se/~antenna/"))
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
                if reply in name:
                    # XXX fetch site and check that it points to the blog
                    id_ = uri
                    interactions[post.path][id_] = Interaction(
                        id=id_,
                        name=name,
                        uri=uri,
                        type="reply",
                    )

        return interactions
