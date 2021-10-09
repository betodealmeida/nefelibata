"""
An announcer for webmentions.
"""

import logging
from pathlib import Path
from typing import Any, List, Literal, Optional

from aiohttp import ClientResponseError, ClientSession
from bs4 import BeautifulSoup
from pydantic import BaseModel
from yarl import URL

from nefelibata.announcers.base import Announcement, Announcer
from nefelibata.builders.base import Builder
from nefelibata.config import Config
from nefelibata.post import Post
from nefelibata.utils import extract_links, update_yaml

_logger = logging.getLogger(__name__)


class Webmention(BaseModel):
    """
    A webmention.
    """

    source: URL
    target: URL
    status: Literal["success", "queue", "invalid", "error"]
    location: Optional[URL] = None


async def get_webmention_endpoint(session: ClientSession, target: URL) -> Optional[URL]:
    """
    Given a target URL, find the webmention endpoint, if any.
    """
    async with session.head(target) as response:
        for rel, params in response.links.items():
            if rel == "webmention":
                return URL(params["url"])

        if "text/html" not in response.headers.get("Content-Type", ""):
            return None

    async with session.get(target) as response:
        html = await response.text()

    soup = BeautifulSoup(html, "html.parser")
    link = soup.find(rel="webmention")
    if link:
        return target.join(URL(link))

    return None


async def send_webmention(
    session: ClientSession,
    source: URL,
    target: URL,
) -> Webmention:
    """
    Send a webmention to a target.
    """
    endpoint = await get_webmention_endpoint(session, target)
    if not endpoint:
        _logger.info("No endpoint found")
        return Webmention(source=source, target=target, status="invalid")

    payload = {"source": source, "target": target}
    async with session.post(endpoint, data=payload) as response:
        try:
            response.raise_for_status()
        except ClientResponseError:
            _logger.error("Error sending webmention")
            return Webmention(source=source, target=target, status="error")

        if response.status == 201:
            return Webmention(
                source=source,
                target=target,
                status="queue",
                location=response.headers["Location"],
            )

    return Webmention(source=source, target=target, status="success")


async def update_webmention(
    source: URL,
    target: URL,
    session: ClientSession,
    location: URL,
) -> Webmention:
    """
    Update the status on a queued webmention.
    """
    async with session.get(location) as response:
        status = "success" if response.ok else "queue"

    return Webmention(source=source, target=target, status=status)


class WebmentionAnnouncer(Announcer):

    """
    An announcer for Webmention (https://indieweb.org/Webmention).
    """

    def __init__(
        self,
        root: Path,
        config: Config,
        builders: List[Builder],
        endpoint: URL,
        **kwargs: Any,
    ):
        super().__init__(root, config, builders, **kwargs)

        self.endpoint = endpoint

    async def announce_post(self, post: Post) -> Optional[Announcement]:
        path = post.path.parent / "webmentions.yaml"

        with update_yaml(path) as webmentions:
            async with ClientSession() as session:
                for target in extract_links(post.content):
                    for builder in self.builders:
                        source = builder.absolute_url(post)

                        if source not in webmentions:
                            webmentions[str(source)] = (
                                await send_webmention(
                                    session,
                                    source,
                                    target,
                                )
                            ).dict()

                        elif webmentions[source]["status"] == "queue":
                            webmentions[str(source)] = (
                                await update_webmention(
                                    session,
                                    source,
                                    target,
                                    webmentions[source]["location"],
                                )
                            ).dict()

        return None
