"""
Google Calendar integration.

Only used when DEMO_MODE=false. Requires the same OAuth client as Gmail
(see google_auth.py) with the calendar.events scope.

Events default to a 1-hour duration starting at the extracted meeting time.
"""

import logging
from datetime import timedelta
from typing import Optional

from googleapiclient.errors import HttpError

from app.services.google_auth import build_service, GoogleAuthError
from app.services.text_extraction import combine_date_time

logger = logging.getLogger("email_automation.calendar")

DEFAULT_EVENT_DURATION = timedelta(hours=1)
DEFAULT_TIMEZONE = "UTC"


class CalendarServiceError(Exception):
    """Raised when the Calendar API cannot be reached, returns an error,
    or the event payload is missing required date/time information."""


def _calendar_service():
    try:
        return build_service("calendar", "v3")
    except GoogleAuthError as exc:
        raise CalendarServiceError(str(exc)) from exc


def create_event(
    summary: str,
    description: str = "",
    date: Optional[str] = None,
    time: Optional[str] = None,
    attendees: Optional[list[str]] = None,
) -> dict:
    """Create a calendar event on the primary calendar.

    `date` must be an ISO date (YYYY-MM-DD) and `time` a human-readable
    time (e.g. "3:00 PM"). If either is missing/unparseable, raises
    CalendarServiceError - the planner is supposed to avoid this case
    (see action_planner: meeting date unclear -> draft instead), but the
    execution layer double-checks rather than silently guessing.
    """
    start_dt = combine_date_time(date, time)
    if start_dt is None:
        raise CalendarServiceError(
            f"Cannot create calendar event: date/time could not be parsed (date={date!r}, time={time!r})"
        )

    end_dt = start_dt + DEFAULT_EVENT_DURATION

    event_body = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": DEFAULT_TIMEZONE},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": DEFAULT_TIMEZONE},
    }
    if attendees:
        event_body["attendees"] = [{"email": a} for a in attendees if a]

    try:
        service = _calendar_service()
        event = service.events().insert(calendarId="primary", body=event_body).execute()
        return event
    except HttpError as exc:
        raise CalendarServiceError(f"Calendar API error: {exc}") from exc
    except CalendarServiceError:
        raise
    except Exception as exc:
        raise CalendarServiceError(f"Unexpected Calendar error: {exc}") from exc
