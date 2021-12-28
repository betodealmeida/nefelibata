"""
An announcer for webmentions.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Literal, Optional, TypedDict

import dateutil.parser
from aiohttp import ClientResponseError, ClientSession
from bs4 import BeautifulSoup
from pydantic import BaseModel
from yarl import URL

from nefelibata.announcers.base import (
    Announcement,
    Announcer,
    Author,
    Interaction,
    Scope,
)
from nefelibata.post import Post, extract_links
from nefelibata.utils import update_yaml

_logger = logging.getLogger(__name__)


# map from wm-property to ``Interaction.type``
INTERACTION_TYPES = {
    "in-reply-to": "reply",
    "mention-of": "mention",
    "like-of": "like",
}


class Webmention(BaseModel):
    """
    A webmention.
    """

    source: str
    target: str
    status: Literal["success", "queue", "invalid", "error"]
    location: Optional[str] = None


class WebmentionType(TypedDict, total=False):
    """
    Type for ``Webmention.dict()``.
    """

    source: str
    target: str
    status: Literal["success", "queue", "invalid", "error"]
    location: str


async def get_webmention_endpoint(session: ClientSession, target: URL) -> Optional[URL]:
    """
    Given a target URL, find the webmention endpoint, if any.
    """
    if target.scheme not in {"http", "https"}:
        return None

    async with session.head(target) as response:
        for rel, params in response.links.items():
            if "webmention" in rel.split(" "):
                return target.join(URL(params["url"]))

        if "text/html" not in response.headers.get("content-type", ""):
            return None

    async with session.get(target) as response:
        try:
            html = await response.text()
        except UnicodeDecodeError:
            return None

    soup = BeautifulSoup(html, "html.parser")
    link = soup.find(rel="webmention", href=True)
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
        return Webmention(
            source=str(source),
            target=str(target),
            status="invalid",
        )

    _logger.info("Sending webmention to %s", endpoint)
    payload = {"source": source, "target": target}
    async with session.post(endpoint, data=payload) as response:
        try:
            response.raise_for_status()
        except ClientResponseError:
            _logger.error("Error sending webmention")
            return Webmention(
                source=str(source),
                target=str(target),
                status="error",
            )

        if response.status == 201:
            return Webmention(
                source=str(source),
                target=str(target),
                status="queue",
                location=response.headers["location"],
            )

    return Webmention(
        source=str(source),
        target=str(target),
        status="success",
    )


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

    return Webmention(
        source=str(source),
        target=str(target),
        status=status,
    )


async def collect_webmentions(
    session: ClientSession,
    source: URL,
    target: URL,
    webmentions: Dict[str, WebmentionType],
) -> None:
    """
    Helper function to collect webmentions.
    """
    key = f"{source} => {target}"
    if key not in webmentions:
        webmention = await send_webmention(session, source, target)
        webmentions[key] = webmention.dict()
    elif webmentions[key]["status"] == "queue":
        location = webmentions[key]["location"]
        webmention = await update_webmention(session, source, target, location)
        webmentions[key] = webmention.dict()


class WebmentionAnnouncer(Announcer):

    """
    An announcer for Webmention (https://indieweb.org/Webmention).
    """

    scopes = [Scope.POST]

    async def announce_post(self, post: Post) -> Optional[Announcement]:
        path = post.path.parent / "webmentions.yaml"

        tasks = []
        with update_yaml(path) as webmentions:
            async with ClientSession() as session:
                for target in extract_links(post):
                    for builder in self.builders:
                        source = builder.absolute_url(post)
                        task = asyncio.create_task(
                            collect_webmentions(session, source, target, webmentions),
                        )
                        tasks.append(task)

                await asyncio.gather(*tasks)

        if any(webmention["status"] == "queue" for webmention in webmentions.values()):
            # return nothing so we can check queued webmentions on next publish
            return None

        return Announcement(
            url=post.url,
            timestamp=datetime.now(timezone.utc),
        )

    async def collect_post(self, post: Post) -> Dict[str, Interaction]:
        interactions: Dict[str, Interaction] = {}

        async with ClientSession() as session:
            for builder in self.builders:
                target = builder.absolute_url(post)
                payload = {"target": target}

                async with session.get(
                    "https://webmention.io/api/mentions.jf2",
                    data=payload,
                ) as response:
                    try:
                        response.raise_for_status()
                    except ClientResponseError:
                        _logger.error("Error fetching webmentions")
                        continue

                    payload = await response.json()

                for entry in payload["children"]:
                    if entry["type"] != "entry":
                        continue

                    interactions[entry["wm-id"]] = Interaction(
                        id=entry["wm-id"],
                        name=entry.get("name", entry["wm-source"]),
                        summary=entry.get("summary", {}).get("value"),
                        content=entry["content"]["text"],
                        published=dateutil.parser.parse(entry["published"]),
                        updated=None,
                        author=Author(
                            name=entry["author"]["name"],
                            url=entry["author"]["url"],
                            avatar=entry["author"]["photo"],
                            note=entry["author"].get("note", ""),
                        ),
                        url=entry["wm-source"],
                        in_reply_to_id=None,
                        type=INTERACTION_TYPES[entry["wm-property"]],
                    )

        return interactions
