"""
A Geminispace (gemini://geminispace.info) announcer.
"""
import logging
import re
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from aiogemini.client import Client
from aiogemini.security import TOFUContext
from yarl import URL

from nefelibata.announcers.base import Announcement, Announcer, Interaction, Scope
from nefelibata.builders.base import Builder
from nefelibata.config import Config
from nefelibata.post import Post

_logger = logging.getLogger(__name__)


class GeminispaceAnnouncer(Announcer):

    """
    A Geminispace (gemini://geminispace.info) announcer.
    """

    scopes = [Scope.POST, Scope.SITE]

    def __init__(
        self, root: Path, config: Config, builders: List[Builder], **kwargs: Any
    ):
        super().__init__(root, config, builders, **kwargs)

        self.client = Client(TOFUContext({}))

    async def announce_site(self) -> Optional[Announcement]:
        """
        Add capsule to Geminispace.
        """
        for builder in self.builders:
            if builder.home.scheme != "gemini":
                raise Exception(
                    "Geminispace announcer only works with `gemini://` builds",
                )

            capsule_url = urllib.parse.quote_plus(str(builder.home))
            url = f"gemini://geminispace.info/add-seed?{capsule_url}"

            _logger.info("Announcing capsule %s to Geminispace", capsule_url)
            await self.client.get(URL(url))

        return Announcement(
            url="gemini://geminispace.info/",
            timestamp=datetime.now(timezone.utc),
            grace_seconds=timedelta(days=365).total_seconds(),
        )

    async def collect_post(self, post: Post) -> Dict[str, Interaction]:
        """
        Collect backlinks for a given post.
        """
        interactions: Dict[str, Interaction] = {}

        for builder in self.builders:
            if builder.home.scheme != "gemini":
                raise Exception(
                    "Geminispace announcer only works with `gemini://` builds",
                )

            post_url = urllib.parse.quote_plus(str(builder.absolute_url(post)))
            url = f"gemini://geminispace.info/backlinks?{post_url}"

            response = await self.client.get(URL(url))
            payload = await response.read()
            content = payload.decode("utf-8")

            state = 0
            for line in content.split("\n"):
                if line.startswith("###"):
                    state = 1 if "cross-capsule backlinks" in line else 2
                if state == 1 and line.startswith("=>"):
                    _, url, name = re.split(r"\s+", line, 2)

                    id_ = f"backlink,{url}"
                    interactions[id_] = Interaction(
                        id=id_,
                        name=name,
                        url=url,
                        type="backlink",
                    )

        return interactions
