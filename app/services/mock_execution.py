"""
Mock execution providers.

Used when DEMO_MODE=true, so approved actions can be "executed" end to end
without real Gmail/Calendar credentials. Each function returns a result
shaped like the real API would, so the dashboard and audit log look
identical regardless of mode.
"""

import uuid
from datetime import datetime

from app.services.text_extraction import combine_date_time


def mock_create_draft(payload: dict) -> dict:
    """Simulate Gmail draft creation."""
    draft_id = f"demo-draft-{uuid.uuid4().hex[:8]}"
    return {
        "mode": "mock",
        "draft_id": draft_id,
        "to": payload.get("to"),
        "subject": payload.get("subject"),
        "preview": (payload.get("reply_text") or "")[:200],
    }


def mock_create_calendar_event(payload: dict) -> dict:
    """Simulate Calendar event creation. Mirrors the validation done by the
    real calendar_service - raises ValueError if date/time can't be parsed.
    """
    date = payload.get("date")
    time = payload.get("time")

    start_dt = combine_date_time(date, time)
    if start_dt is None:
        raise ValueError(f"Cannot create calendar event: date/time could not be parsed (date={date!r}, time={time!r})")

    event_id = f"demo-event-{uuid.uuid4().hex[:8]}"
    return {
        "mode": "mock",
        "event_id": event_id,
        "summary": payload.get("summary"),
        "start": start_dt.isoformat(),
        "attendees": payload.get("attendees", []),
        "html_link": f"https://calendar.google.com/calendar/event?eid={event_id}",
    }
