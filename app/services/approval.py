"""
Approval workflow service.

This is the human-in-the-loop gate: nothing proposed by the planner can be
executed until it passes through here.

Valid status transitions:
    PENDING  -> APPROVED   (approve)
    PENDING  -> REJECTED   (reject)
    PENDING  -> EDITED     (edit payload)
    EDITED   -> APPROVED   (approve after edit)
    EDITED   -> REJECTED   (reject after edit)
    EDITED   -> EDITED     (edit again)

Any other transition (e.g. approving an already-executed or rejected
action) raises ApprovalError, which the router turns into a 400 response.

`assert_can_execute` is the gate used by the execution service in Phase 6
to enforce: "AI recommends. Human approves. System executes."
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Action, ActionStatus
from app.services.audit import log_event


class ApprovalError(Exception):
    """Raised when an approval-workflow transition is not allowed."""


_EDITABLE_STATUSES = {ActionStatus.PENDING, ActionStatus.EDITED}
_DECIDABLE_STATUSES = {ActionStatus.PENDING, ActionStatus.EDITED}


def get_action_or_raise(db: Session, action_id: int) -> Action:
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise ApprovalError(f"Action {action_id} not found")
    return action


def approve_action(db: Session, action_id: int) -> Action:
    """Approve a pending (or edited) action, making it eligible for execution."""
    action = get_action_or_raise(db, action_id)

    if action.status not in _DECIDABLE_STATUSES:
        raise ApprovalError(
            f"Action {action_id} cannot be approved from status '{action.status.value}'. "
            f"Only actions with status 'pending' or 'edited' can be approved."
        )

    action.status = ActionStatus.APPROVED
    action.approved_at = datetime.utcnow()
    db.commit()
    db.refresh(action)

    log_event(
        db,
        event_type="action_approved",
        message=f"Action {action_id} ({action.action_type.value}) approved.",
        related_email_id=action.email_id,
        related_action_id=action.id,
    )

    return action


def reject_action(db: Session, action_id: int, reason: Optional[str] = None) -> Action:
    """Reject a pending (or edited) action. Rejected actions are never executed."""
    action = get_action_or_raise(db, action_id)

    if action.status not in _DECIDABLE_STATUSES:
        raise ApprovalError(
            f"Action {action_id} cannot be rejected from status '{action.status.value}'. "
            f"Only actions with status 'pending' or 'edited' can be rejected."
        )

    action.status = ActionStatus.REJECTED
    if reason:
        action.reason = reason
    db.commit()
    db.refresh(action)

    log_event(
        db,
        event_type="action_rejected",
        message=f"Action {action_id} ({action.action_type.value}) rejected.",
        related_email_id=action.email_id,
        related_action_id=action.id,
        details={"reason": reason} if reason else None,
    )

    return action


def edit_action_payload(db: Session, action_id: int, new_payload: dict) -> Action:
    """Edit a pending action's payload before approval (e.g. tweak a draft
    reply or change a meeting time). Sets status to EDITED; the action must
    still be explicitly approved afterwards.
    """
    action = get_action_or_raise(db, action_id)

    if action.status not in _EDITABLE_STATUSES:
        raise ApprovalError(
            f"Action {action_id} cannot be edited from status '{action.status.value}'. "
            f"Only actions with status 'pending' or 'edited' can be edited."
        )

    old_payload = action.payload
    action.payload = new_payload
    action.status = ActionStatus.EDITED
    db.commit()
    db.refresh(action)

    log_event(
        db,
        event_type="action_edited",
        message=f"Action {action_id} ({action.action_type.value}) payload edited.",
        related_email_id=action.email_id,
        related_action_id=action.id,
        details={"old_payload": old_payload, "new_payload": new_payload},
    )

    return action


_EXECUTABLE_STATUSES = {ActionStatus.APPROVED, ActionStatus.FAILED}


def assert_can_execute(action: Action) -> None:
    """Gate used by the execution service (Phase 6).

    Raises ApprovalError if the action is not in a state that allows execution.
    This is the concrete enforcement of:
        "No external action can happen unless the user approves it."

    FAILED is also allowed so a failed execution can be retried without
    re-running the approval step.
    """
    if action.status not in _EXECUTABLE_STATUSES:
        raise ApprovalError(
            f"Action {action.id} cannot be executed: status is '{action.status.value}', "
            f"but execution requires status 'approved' (or 'failed', for a retry)."
        )
