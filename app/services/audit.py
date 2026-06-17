"""
Audit logging helper.

Every meaningful event in the system (sync, analysis, proposal, approval,
execution, failure) should be written here so the full chain is traceable:

    Email received -> AI analyzed -> action proposed -> user approved -> draft created -> log saved
"""

from typing import Optional, Any

from sqlalchemy.orm import Session

from app.models import AuditLog


def log_event(
    db: Session,
    event_type: str,
    message: str,
    related_email_id: Optional[int] = None,
    related_action_id: Optional[int] = None,
    details: Optional[Any] = None,
    commit: bool = True,
) -> AuditLog:
    """Create and persist a single audit log entry.

    event_type examples: "email_synced", "email_sync_failed", "email_analyzed",
    "action_proposed", "action_approved", "action_rejected", "action_edited",
    "action_executed", "action_execution_failed".
    """
    entry = AuditLog(
        event_type=event_type,
        related_email_id=related_email_id,
        related_action_id=related_action_id,
        message=message,
        details=details,
    )
    db.add(entry)
    if commit:
        db.commit()
        db.refresh(entry)
    return entry
