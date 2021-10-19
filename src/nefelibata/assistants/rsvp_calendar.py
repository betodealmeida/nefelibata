"""
Assistant for syncing events to a calendar.
"""

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import caldav
import dateutil.parser
import mf2py
from aiohttp import ClientSession
from caldav import DAVClient
from icalendar import Calendar, Event
from yarl import URL

from nefelibata.announcers.base import Scope
from nefelibata.assistants.base import Assistant
from nefelibata.config import Config
from nefelibata.post import Post

_logger = logging.getLogger(__name__)


async def fetch_event(url: URL) -> Optional[Event]:
    """
    Extract a event from a page.

    We assume the event is represented as an h-event in the URL.
    """
    async with ClientSession() as session:
        async with session.get(url) as response:
            content = await response.text()

        parser = mf2py.Parser(content)
        hevents = parser.to_dict(filter_by_type="h-event")

        if not hevents:
            _logger.warning("No events found on %s", url)
            return None
        if len(hevents) > 1:
            _logger.warning("Multiple events found on %s", url)
            return None
        hevent = hevents[0]

        event = Event()
        event.add("summary", hevent["properties"]["name"][0])
        event.add("dtstart", dateutil.parser.parse(hevent["properties"]["start"][0]))
        event.add("dtend", dateutil.parser.parse(hevent["properties"]["end"][0]))
        event.add("dtstamp", datetime.now(timezone.utc))

        if "url" in hevent["properties"]:
            event.add("url", hevent["properties"]["url"][0])

        if "content" in hevent["properties"]:
            event.add("description", hevent["properties"]["content"][0]["value"])

        if "category" in hevent["properties"]:
            event.add("categories", hevent["properties"]["category"])

        if "featured" in hevent["properties"]:
            attachment_url = url.join(URL(hevent["properties"]["featured"][0]))
            event.add("attach", attachment_url)

    return event


def update_calendar(client: DAVClient, calendar_name: str, event: Event) -> None:
    """
    Create or update an event in a calendar.
    """
    principal = client.principal()
    try:
        calendar = principal.calendar(name=calendar_name)
    except caldav.error.NotFoundError:
        calendar = principal.make_calendar(name=calendar_name)

    # delete existing event, identified by URL
    if "url" in event:
        # pad search, otherwise it will return nothing
        existing_events = calendar.date_search(
            start=event["dtstart"].dt.date(),
            end=event["dtend"].dt.date() + timedelta(days=1),
            expand=False,
        )
        for existing_event in existing_events:
            vevent = existing_event.vobject_instance.vevent
            if hasattr(vevent, "url") and vevent.url.value == event["url"]:
                _logger.info("Found existing event, deleting")
                existing_event.delete()

    # wrap in BEGIN:VCALENDAR
    component = Calendar()
    component.add("prodid", "-//Nefelibata Corp.//CalDAV Client//EN")
    component.add("version", "2.0")
    component.add("x-wr-calname", calendar_name)
    component.add_component(event)

    _logger.info("Creating event")
    calendar.save_event(component.to_ical())


class RSVPCalendarAssistant(Assistant):
    """
    An assistant that adds RSVP'd events to a Caldav calendar.
    """

    name = "rsvp_calendar"
    scopes = [Scope.POST]

    def __init__(  # pylint: disable=too-many-arguments
        self,
        root: Path,
        config: Config,
        url: str,
        username: str,
        password: str,
        calendar: str,
        **kwargs: Any
    ):
        super().__init__(root, config, **kwargs)

        self.client = DAVClient(url=url, username=username, password=password)
        self.calendar = calendar

    async def get_post_metadata(self, post: Post) -> Dict[str, Any]:
        if post.type != "rsvp":
            return {}

        url = post.metadata["rsvp-url"]
        event = await fetch_event(URL(url))
        if event:
            update_calendar(self.client, self.calendar, event)

        return {"event": url}
