"""
A Geminispace (gemini://geminispace.info) announcer.
"""
import logging
import re
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from aiogemini.client import Client
from aiogemini.security import TOFUContext
from yarl import URL

from nefelibata.announcers.base import Announcement, Announcer, Interaction
from nefelibata.builders.base import Scope
from nefelibata.post import Post
from nefelibata.typing import Config

_logger = logging.getLogger(__name__)


class GeminispaceAnnouncer(Announcer):

    """
    A Geminispace (gemini://geminispace.info) announcer.
    """

    scopes = [Scope.POST, Scope.SITE]

    def __init__(self, root: Path, config: Config, **kwargs: Any):
        super().__init__(root, config, **kwargs)
        self.client = Client(TOFUContext({}))

    async def announce_post(self, post: Post) -> Optional[Announcement]:
        pass

    async def announce_site(self) -> Optional[Announcement]:
        """
        Add capsule to Geminispace.
        """
        # Potentially a user could have multiple Gemini builders configured,
        # so we announce all of them.
        for name, builder in self.config["builders"].items():
            if builder["plugin"] == "gemini":
                home = builder["home"].rstrip("/")

                capsule_url = urllib.parse.quote_plus(home)
                url = f"gemini://geminispace.info/add-seed?{capsule_url}"

                _logger.info(
                    "Announcing capsule %s (%s) to Geminispace",
                    capsule_url,
                    name,
                )
                await self.client.get(URL(url))

        return Announcement(
            uri="gemini://geminispace.info/",
            timestamp=datetime.now(timezone.utc),
        )

    async def collect_post(self, post: Post) -> Dict[str, Interaction]:
        """
        Collect backlinks for a given post.
        """
        interactions: Dict[str, Interaction] = {}

        # Potentially a user could have multiple Gemini builders configured,
        # so we announce all of them.
        for name, builder in self.config["builders"].items():
            if builder["plugin"] == "gemini":
                home = builder["home"].rstrip("/")

                post_url = urllib.parse.quote_plus(f"{home}/{post.url}.gmi")
                uri = f"gemini://geminispace.info/backlinks?{post_url}"

                response = await self.client.get(URL(uri))
                payload = await response.read()
                content = payload.decode("utf-8")

                state = 0
                for line in content.split("\n"):
                    if line.startswith("###"):
                        state = 1 if "cross-capsule backlinks" in line else 2
                    if state == 1 and line.startswith("=>"):
                        _, uri, name = re.split(r"\s+", line, 2)

                        id_ = f"backlink,{uri}"
                        interactions[id_] = Interaction(
                            id=id_,
                            name=name,
                            uri=uri,
                            type="backlink",
                        )

        return interactions

    async def collect_site(self) -> Dict[Path, Dict[str, Interaction]]:
        return {}
