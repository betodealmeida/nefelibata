"""
An announcer for webmentions.
"""

import logging
from typing import Literal, Optional

from aiohttp import ClientResponseError, ClientSession
from bs4 import BeautifulSoup
from pydantic import BaseModel
from yarl import URL

from nefelibata.announcers.base import Announcement, Announcer
from nefelibata.post import Post
from nefelibata.utils import extract_links, update_yaml

_logger = logging.getLogger(__name__)


class Webmention(BaseModel):
    """
    A webmention.
    """

    source: str
    target: str
    status: Literal["success", "queue", "invalid", "error"]
    location: Optional[str] = None


async def get_webmention_endpoint(session: ClientSession, target: URL) -> Optional[URL]:
    """
    Given a target URL, find the webmention endpoint, if any.
    """
    async with session.head(target) as response:
        for rel, params in response.links.items():
            if rel == "webmention":
                return target.join(URL(params["url"]))

        if "text/html" not in response.headers.get("content-type", ""):
            return None

    async with session.get(target) as response:
        html = await response.text()

    soup = BeautifulSoup(html, "html.parser")
    link = soup.find(rel="webmention")
    if link:
        return target.join(URL(link["href"]))

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
        return Webmention(source=str(source), target=str(target), status="invalid")

    payload = {"source": source, "target": target}
    async with session.post(endpoint, data=payload) as response:
        try:
            response.raise_for_status()
        except ClientResponseError:
            _logger.error("Error sending webmention")
            return Webmention(source=str(source), target=str(target), status="error")

        if response.status == 201:
            return Webmention(
                source=str(source),
                target=str(target),
                status="queue",
                location=response.headers["location"],
            )

    return Webmention(source=str(source), target=str(target), status="success")


async def update_webmention(
    session: ClientSession,
    source: URL,
    target: URL,
    location: URL,
) -> Webmention:
    """
    Update the status on a queued webmention.
    """
    async with session.get(location) as response:
        status = "success" if response.ok else "queue"

    return Webmention(source=str(source), target=str(target), status=status)


class WebmentionAnnouncer(Announcer):

    """
    An announcer for Webmention (https://indieweb.org/Webmention).
    """

    async def announce_post(self, post: Post) -> Optional[Announcement]:
        path = post.path.parent / "webmentions.yaml"

        with update_yaml(path) as webmentions:
            async with ClientSession() as session:
                for target in extract_links(post.content):
                    for builder in self.builders:
                        source = builder.absolute_url(post)
                        key = str(source)

                        if key not in webmentions:
                            webmentions[key] = (
                                await send_webmention(
                                    session,
                                    source,
                                    target,
                                )
                            ).dict()

                        elif webmentions[key]["status"] == "queue":
                            webmentions[key] = (
                                await update_webmention(
                                    session,
                                    source,
                                    target,
                                    webmentions[key]["location"],
                                )
                            ).dict()

        # don't return anything, so we check queued webmentions on every publish
        return None
