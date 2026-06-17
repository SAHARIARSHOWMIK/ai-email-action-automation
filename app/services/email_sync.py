"""
Email sync orchestration.

Chooses between the demo provider and the real Gmail service based on
DEMO_MODE, stores new emails in the database, skips duplicates (by
gmail_message_id), and writes an audit log entry for the sync run.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Email
from app.schemas import EmailSyncResult
from app.services.audit import log_event
from app.services.demo_emails import get_demo_emails
from app.services.gmail_service import fetch_unread_emails, GmailServiceError

logger = logging.getLogger("email_automation.sync")


def _parse_received_at(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        # Handle both plain ISO strings and ones with timezone offsets.
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def sync_emails(db: Session, max_results: int = 10) -> EmailSyncResult:
    """Fetch emails (demo or real Gmail) and store new ones in the database.

    Raises:
        GmailServiceError: if DEMO_MODE=false and Gmail cannot be reached.
            The caller (router) is expected to catch this and return a
            clean error response while still logging the failure.
    """
    source = "demo" if settings.demo_mode else "gmail"

    if settings.demo_mode:
        raw_emails = get_demo_emails()
    else:
        try:
            raw_emails = fetch_unread_emails(max_results=max_results)
        except GmailServiceError as exc:
            log_event(
                db,
                event_type="email_sync_failed",
                message=f"Gmail sync failed: {exc}",
                details={"source": source},
            )
            raise

    new_count = 0
    duplicate_count = 0
    new_email_ids: list[int] = []

    for raw in raw_emails:
        existing = (
            db.query(Email)
            .filter(Email.gmail_message_id == raw["gmail_message_id"])
            .first()
        )
        if existing:
            duplicate_count += 1
            continue

        email_row = Email(
            gmail_message_id=raw["gmail_message_id"],
            sender=raw.get("sender", ""),
            subject=raw.get("subject", ""),
            body=raw.get("body", ""),
            received_at=_parse_received_at(raw.get("received_at")),
            is_demo=settings.demo_mode,
        )
        db.add(email_row)
        db.flush()  # populate email_row.id without committing yet
        new_email_ids.append(email_row.id)
        new_count += 1

    db.commit()

    for email_id in new_email_ids:
        log_event(
            db,
            event_type="email_synced",
            message="Email synced into the system.",
            related_email_id=email_id,
            details={"source": source},
        )

    log_event(
        db,
        event_type="sync_run_completed",
        message=f"Sync completed: {new_count} new, {duplicate_count} duplicates.",
        details={"source": source, "fetched": len(raw_emails)},
    )

    return EmailSyncResult(
        fetched=len(raw_emails),
        new=new_count,
        duplicates=duplicate_count,
        source=source,
    )
