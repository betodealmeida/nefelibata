"""
Assistant for saving external links in https://archive.org/.
"""

import asyncio
import logging
from datetime import timedelta
from typing import Any, Dict, Iterator

import marko
from aiohttp import ClientSession

from nefelibata.announcers.base import Scope
from nefelibata.assistants.base import Assistant
from nefelibata.post import Post

_logger = logging.getLogger(__name__)


# API is restricted to 5 requests per minute, see
# https://rationalwiki.org/wiki/Internet_Archive#Restrictions
lock = asyncio.Lock()
SLEEP = timedelta(seconds=12)


def extract_links(content: str) -> Iterator[str]:
    """
    Extract all links from a Markdown document.
    """
    tree = marko.parse(content)
    queue = [tree]
    while queue:
        element = queue.pop()

        if isinstance(element, marko.inline.Link):
            yield element.dest
        elif hasattr(element, "children"):
            queue.extend(element.children)


class ArchiveLinksAssistant(Assistant):
    """
    Assistant for saving external links in https://archive.org/.
    """

    name = "saved_links"
    scopes = [Scope.POST]

    async def get_post_metadata(self, post: Post) -> Dict[str, Any]:
        saved_links = {}

        async with ClientSession() as session:
            for url in extract_links(post.content):
                _logger.info("Saving URL %s", url)
                save_url = f"https://web.archive.org/save/{url}"
                async with lock:
                    async with session.get(save_url) as response:
                        for rel, params in response.links.items():
                            if rel == "memento":
                                saved_links[url] = str(params["url"])
                    await asyncio.sleep(SLEEP.total_seconds())

        return saved_links
