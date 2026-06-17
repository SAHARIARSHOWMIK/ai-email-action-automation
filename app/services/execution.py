"""
Execution service.

This is the only place in the system where approved actions actually do
something external (or internal, for tasks). It enforces:

    AI recommends. Human approves. System executes.

via `assert_can_execute` (Phase 5), then dispatches based on action_type:

    CREATE_GMAIL_DRAFT     -> Gmail draft (real or mock)
    CREATE_CALENDAR_EVENT  -> Calendar event (real or mock)
    CREATE_TASK            -> internal Task row (always real, no external API)
    ESCALATE               -> marks the action as escalated (human review record)
    IGNORE                 -> marks the action as executed/ignored, no side effects

On success: status -> EXECUTED (or ESCALATED for ESCALATE actions),
execution_result populated, executed_at set, audit log written.

On failure: status -> FAILED, execution_result contains the error,
audit log written. The action can be retried via the same endpoint
(see approval.assert_can_execute, which permits FAILED -> execute).
"""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Action, ActionStatus, ActionType, Task
from app.services.approval import assert_can_execute, ApprovalError
from app.services.audit import log_event
from app.services.calendar_service import create_event, CalendarServiceError
from app.services.gmail_service import create_draft_reply, GmailServiceError
from app.services.mock_execution import mock_create_draft, mock_create_calendar_event

logger = logging.getLogger("email_automation.execution")


class ExecutionError(Exception):
    """Raised for execution failures that aren't ApprovalError (approval gate)."""


def _execute_gmail_draft(action: Action) -> dict:
    payload = action.payload or {}
    if settings.demo_mode:
        return mock_create_draft(payload)

    draft = create_draft_reply(
        to=payload.get("to", ""),
        subject=payload.get("subject", ""),
        body_text=payload.get("reply_text", ""),
    )
    return {"mode": "gmail", "draft_id": draft.get("id"), "to": payload.get("to"), "subject": payload.get("subject")}


def _execute_calendar_event(action: Action) -> dict:
    payload = action.payload or {}
    if settings.demo_mode:
        return mock_create_calendar_event(payload)

    event = create_event(
        summary=payload.get("summary", ""),
        description=payload.get("description", ""),
        date=payload.get("date"),
        time=payload.get("time"),
        attendees=payload.get("attendees"),
    )
    return {
        "mode": "calendar",
        "event_id": event.get("id"),
        "html_link": event.get("htmlLink"),
        "start": event.get("start"),
    }


def _execute_create_task(db: Session, action: Action) -> dict:
    payload = action.payload or {}

    existing_task = db.query(Task).filter(Task.action_id == action.id).first()
    if existing_task:
        task = existing_task
    else:
        task = Task(
            action_id=action.id,
            title=payload.get("title", "Untitled task")[:255],
            description=payload.get("description", ""),
            due_date=payload.get("due_date"),
            status="open",
        )
        db.add(task)
        db.flush()

    return {"mode": "internal", "task_id": task.id, "title": task.title, "due_date": task.due_date}


def _execute_escalate(action: Action) -> dict:
    return {
        "mode": "internal",
        "escalated": True,
        "reason": action.reason,
    }


def _execute_ignore(action: Action) -> dict:
    return {"mode": "internal", "ignored": True}


def execute_action(db: Session, action_id: int) -> Action:
    """Execute a single approved (or previously-failed) action.

    Raises:
        ApprovalError: if the action's status doesn't permit execution
            (e.g. still 'pending', or already 'executed'/'rejected').
    """
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise ApprovalError(f"Action {action_id} not found")

    assert_can_execute(action)

    try:
        if action.action_type == ActionType.CREATE_GMAIL_DRAFT:
            result = _execute_gmail_draft(action)
        elif action.action_type == ActionType.CREATE_CALENDAR_EVENT:
            result = _execute_calendar_event(action)
        elif action.action_type == ActionType.CREATE_TASK:
            result = _execute_create_task(db, action)
        elif action.action_type == ActionType.ESCALATE:
            result = _execute_escalate(action)
        elif action.action_type == ActionType.IGNORE:
            result = _execute_ignore(action)
        else:
            raise ExecutionError(f"Unknown action_type: {action.action_type}")

    except (GmailServiceError, CalendarServiceError, ExecutionError, ValueError) as exc:
        action.status = ActionStatus.FAILED
        action.execution_result = {"error": str(exc)}
        db.commit()
        db.refresh(action)

        log_event(
            db,
            event_type="action_execution_failed",
            message=f"Execution failed for action {action_id} ({action.action_type.value}): {exc}",
            related_email_id=action.email_id,
            related_action_id=action.id,
            details={"error": str(exc)},
        )
        return action

    # Success
    action.status = (
        ActionStatus.ESCALATED if action.action_type == ActionType.ESCALATE else ActionStatus.EXECUTED
    )
    action.execution_result = result
    action.executed_at = datetime.utcnow()
    db.commit()
    db.refresh(action)

    log_event(
        db,
        event_type="action_executed",
        message=f"Action {action_id} ({action.action_type.value}) executed successfully.",
        related_email_id=action.email_id,
        related_action_id=action.id,
        details=result,
    )

    return action
