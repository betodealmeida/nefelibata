"""
Assistant for saving external links in https://archive.org/.
"""

import asyncio
import logging
from datetime import timedelta
from typing import Any, Dict

from aiohttp import ClientSession

from nefelibata.announcers.base import Scope
from nefelibata.assistants.base import Assistant
from nefelibata.post import Post, extract_links

_logger = logging.getLogger(__name__)


# API is restricted to 5 requests per minute, see
# https://rationalwiki.org/wiki/Internet_Archive#Restrictions
lock = asyncio.Lock()
SLEEP = timedelta(seconds=12)


class ArchiveLinksAssistant(Assistant):
    """
    Assistant for saving external links in https://archive.org/.
    """

    name = "saved_links"
    scopes = [Scope.POST]

    async def get_post_metadata(self, post: Post) -> Dict[str, Any]:
        saved_links = {}

        async with ClientSession() as session:
            for i, url in enumerate(extract_links(post)):
                if url.scheme not in {"http", "https"}:
                    continue

                _logger.info("Saving URL %s", url)
                save_url = f"https://web.archive.org/save/{url}"
                async with lock:
                    if i > 0:
                        await asyncio.sleep(SLEEP.total_seconds())

                    async with session.get(save_url) as response:
                        for rel, params in response.links.items():
                            if rel == "memento":
                                saved_links[str(url)] = str(params["url"])

        return saved_links
