"""
Small text-extraction helpers used by the mock analyzer (and useful as a
sanity-check / fallback even when the real AI is used).

These are deliberately simple regex-based heuristics - they are NOT meant
to replace the LLM's understanding, only to give the demo/mock analyzer
something plausible to extract from the seed emails.
"""

import re
from datetime import datetime, timedelta
from typing import Optional

_ISO_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")

_WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

# Matches things like "Tuesday at 3pm", "Friday at 10:30 AM", "Monday at 9 am"
_MEETING_RE = re.compile(
    r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b\s+at\s+"
    r"(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM))",
    re.IGNORECASE,
)


_TIME_RE = re.compile(r"(\d{1,2})(?::(\d{2}))?\s*(AM|PM)", re.IGNORECASE)


def combine_date_time(date_str: Optional[str], time_str: Optional[str]) -> Optional[datetime]:
    """Combine an ISO date ('2026-06-21') and a time string ('3:00PM' / '3 PM')
    into a single datetime. Returns None if either piece is missing or
    can't be parsed.
    """
    if not date_str or not time_str:
        return None

    try:
        base_date = datetime.fromisoformat(date_str).date()
    except ValueError:
        return None

    match = _TIME_RE.search(time_str)
    if not match:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    meridiem = match.group(3).upper()

    if meridiem == "PM" and hour != 12:
        hour += 12
    if meridiem == "AM" and hour == 12:
        hour = 0

    return datetime(base_date.year, base_date.month, base_date.day, hour, minute)


def extract_iso_date(text: str) -> Optional[str]:
    """Return the first YYYY-MM-DD date found in the text, if any."""
    match = _ISO_DATE_RE.search(text)
    return match.group(1) if match else None


def extract_meeting_datetime(text: str) -> tuple[Optional[str], Optional[str]]:
    """Find a 'Weekday at TIME' pattern and resolve the weekday to the next
    upcoming date (relative to now). Returns (meeting_date_iso, meeting_time)
    or (None, None) if no match is found.
    """
    match = _MEETING_RE.search(text)
    if not match:
        return None, None

    weekday_name = match.group(1).lower()
    time_str = match.group(2).upper().replace(" ", "")

    target_weekday = _WEEKDAYS[weekday_name]
    today = datetime.utcnow().date()
    days_ahead = (target_weekday - today.weekday()) % 7
    days_ahead = days_ahead or 7  # always the *next* occurrence, not today
    meeting_date = today + timedelta(days=days_ahead)

    return meeting_date.isoformat(), time_str
