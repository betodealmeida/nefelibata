"""
Tests for ``nefelibata.assistants.rsvp_calendar``.
"""
# pylint: disable=redefined-outer-name

from datetime import datetime, timezone
from pathlib import Path

import pytest
from freezegun import freeze_time
from icalendar import Event
from pytest_mock import MockerFixture
from yarl import URL

from nefelibata.assistants.rsvp_calendar import (
    RSVPCalendarAssistant,
    fetch_event,
    update_calendar,
)
from nefelibata.config import Config
from nefelibata.post import Post


@pytest.mark.asyncio
async def test_fetch_event_no_events(mocker: MockerFixture) -> None:
    """
    Test ``fetch_event`` when no events are found.
    """
    _logger = mocker.patch("nefelibata.assistants.rsvp_calendar._logger")

    get = mocker.patch("nefelibata.assistants.rsvp_calendar.ClientSession.get")
    get.return_value.__aenter__.return_value.text.return_value = "<p>Hello!</p>"

    event = await fetch_event(URL("https://example.com/events"))
    assert event is None
    _logger.warning.assert_called_with(
        "No events found on %s",
        URL("https://example.com/events"),
    )


@pytest.mark.asyncio
async def test_fetch_event_multiple_events(mocker: MockerFixture) -> None:
    """
    Test ``fetch_event`` when multiple events are found.
    """
    _logger = mocker.patch("nefelibata.assistants.rsvp_calendar._logger")

    get = mocker.patch("nefelibata.assistants.rsvp_calendar.ClientSession.get")
    get.return_value.__aenter__.return_value.text.return_value = """
<div class="h-event">
  <h1 class="p-name">Microformats Meetup</h1>
  <p>From
    <time class="dt-start" datetime="2013-06-30 12:00">30<sup>th</sup> June 2013, 12:00</time>
    to <time class="dt-end" datetime="2013-06-30 18:00">18:00</time>
    at <span class="p-location">Some bar in SF</span></p>
  <p class="p-summary">Get together and discuss all things microformats-related.</p>
</div>

<div class="h-event">
  <h1 class="p-name">Microformats Meetup</h1>
  <p>From
    <time class="dt-start" datetime="2013-06-30 12:00">30<sup>th</sup> June 2013, 12:00</time>
    to <time class="dt-end" datetime="2013-06-30 18:00">18:00</time>
    at <span class="p-location">Some bar in SF</span></p>
  <p class="p-summary">Get together and discuss all things microformats-related.</p>
</div>
    """

    event = await fetch_event(URL("https://example.com/events"))
    assert event is None
    _logger.warning.assert_called_with(
        "Multiple events found on %s",
        URL("https://example.com/events"),
    )


@pytest.mark.asyncio
async def test_fetch_event_simple_event(mocker: MockerFixture) -> None:
    """
    Test ``fetch_event``.
    """
    get = mocker.patch("nefelibata.assistants.rsvp_calendar.ClientSession.get")
    get.return_value.__aenter__.return_value.text.return_value = """
<div class="h-event">
  <h1 class="p-name">Microformats Meetup</h1>
  <p>From
    <time class="dt-start" datetime="2013-06-30 12:00">30<sup>th</sup> June 2013, 12:00</time>
    to <time class="dt-end" datetime="2013-06-30 18:00">18:00</time>
    at <span class="p-location">Some bar in SF</span></p>
  <p class="p-summary">Get together and discuss all things microformats-related.</p>
</div>
    """

    with freeze_time("2021-01-01T00:00:00Z"):
        event = await fetch_event(URL("https://example.com/events"))
    assert (
        event.to_ical()
        == b"""BEGIN:VEVENT\r
SUMMARY:Microformats Meetup\r
DTSTART;VALUE=DATE-TIME:20130630T120000\r
DTEND;VALUE=DATE-TIME:20130630T180000\r
DTSTAMP;VALUE=DATE-TIME:20210101T000000Z\r
END:VEVENT\r
"""
    )


@pytest.mark.asyncio
async def test_fetch_event_full_event(mocker: MockerFixture) -> None:
    """
    Test ``fetch_event``.
    """
    get = mocker.patch("nefelibata.assistants.rsvp_calendar.ClientSession.get")
    get.return_value.__aenter__.return_value.text.return_value = """
<div class="h-event">
  <img src="logo.png" class="u-featured">
  <h1 class="p-name"><a href="https://example.com/events" class="u-url">Microformats Meetup</a></h1>
  <ul>
    <li><span class="p-category">indieweb</span></li>
    <li><span class="p-category">microformats</span></li>
  </ul>
  <p>From
    <time class="dt-start" datetime="2013-06-30 12:00">30<sup>th</sup> June 2013, 12:00</time>
    to <time class="dt-end" datetime="2013-06-30 18:00">18:00</time>
    at <span class="p-location">Some bar in SF</span></p>
  <p class="p-summary">Get together and discuss all things microformats-related.</p>
  <p class="e-content">This is the content.</p>
</div>
    """

    with freeze_time("2021-01-01T00:00:00Z"):
        event = await fetch_event(URL("https://example.com/events"))
    assert (
        event.to_ical()
        == b"""BEGIN:VEVENT\r
SUMMARY:Microformats Meetup\r
DTSTART;VALUE=DATE-TIME:20130630T120000\r
DTEND;VALUE=DATE-TIME:20130630T180000\r
DTSTAMP;VALUE=DATE-TIME:20210101T000000Z\r
ATTACH:https://example.com/logo.png\r
CATEGORIES:indieweb,microformats\r
DESCRIPTION:This is the content.\r
URL:https://example.com/events\r
END:VEVENT\r
"""
    )


def test_update_calendar(mocker: MockerFixture) -> None:
    """
    Test ``update_calendar``.
    """
    client = mocker.MagicMock()
    calendar = client.principal.return_value.calendar.return_value

    event = Event()
    event.add("summary", "A summary")
    event.add("dtstart", datetime(2021, 1, 1, 12, tzinfo=timezone.utc))
    event.add("dtend", datetime(2021, 1, 1, 14, tzinfo=timezone.utc))

    update_calendar(client, "Personal", event)

    calendar.save_event.assert_called_with(
        b"""BEGIN:VCALENDAR\r
VERSION:2.0\r
PRODID:-//Nefelibata Corp.//CalDAV Client//EN\r
X-WR-CALNAME:Personal\r
BEGIN:VEVENT\r
SUMMARY:A summary\r
DTSTART;TZID=UTC;VALUE=DATE-TIME:20210101T120000Z\r
DTEND;TZID=UTC;VALUE=DATE-TIME:20210101T140000Z\r
END:VEVENT\r
END:VCALENDAR\r
""",
    )


def test_update_calendar_create(mocker: MockerFixture) -> None:
    """
    Test ``update_calendar`` when the calendar doesn't exist.
    """
    client = mocker.MagicMock()
    client.principal.return_value.calendar.side_effect = Exception("Not found")
    mocker.patch(
        "nefelibata.assistants.rsvp_calendar.caldav.error.NotFoundError",
        Exception,
    )

    event = mocker.MagicMock()

    update_calendar(client, "Personal", event)

    client.principal.return_value.make_calendar.assert_called_with(name="Personal")


def test_update_calendar_update_event(mocker: MockerFixture) -> None:
    """
    Test ``update_calendar`` when the event already exists.
    """
    client = mocker.MagicMock()
    calendar = client.principal.return_value.calendar.return_value
    existing_event = mocker.MagicMock()
    calendar.date_search.return_value = [existing_event]

    event = Event()
    event.add("summary", "A summary")
    event.add("dtstart", datetime(2021, 1, 1, 12, tzinfo=timezone.utc))
    event.add("dtend", datetime(2021, 1, 1, 14, tzinfo=timezone.utc))
    event.add("url", "https://example.com/events")

    update_calendar(client, "Personal", event)
    existing_event.delete.assert_not_called()

    existing_event.vobject_instance.vevent.url.value = "https://example.com/events"
    update_calendar(client, "Personal", event)
    existing_event.delete.assert_called_with()


@pytest.mark.asyncio
async def test_assistant(
    mocker: MockerFixture,
    root: Path,
    config: Config,
    post: Post,
) -> None:
    """
    Test the assistant.
    """
    assistant = RSVPCalendarAssistant(
        root,
        config,
        "https://calendar.example.com/",
        "username",
        "password",
        "Personal",
    )

    # not an RSVP post
    metadata = await assistant.get_post_metadata(post)
    assert metadata == {}

    # RSVP post without h-event
    post.type = "rsvp"
    post.metadata["rsvp-url"] = "https://example.com/events"
    fetch_event = mocker.patch("nefelibata.assistants.rsvp_calendar.fetch_event")
    fetch_event.return_value = None
    update_calendar = mocker.patch(
        "nefelibata.assistants.rsvp_calendar.update_calendar",
    )

    metadata = await assistant.get_post_metadata(post)
    assert metadata == {"event": "https://example.com/events"}
    update_calendar.assert_not_called()

    # RSVP post with h-event
    fetch_event.return_value = True
    await assistant.get_post_metadata(post)
    update_calendar.assert_called_with(assistant.client, "Personal", True)
