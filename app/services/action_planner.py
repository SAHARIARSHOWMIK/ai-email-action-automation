"""
Action planner.

Converts a validated AI analysis into one or more proposed Action records.
This is the component that encodes the project's safety/business rules -
it decides *what the system would do*, but never executes anything itself.

Planning rules implemented:
  - Confidence below CONFIDENCE_THRESHOLD            -> ESCALATE
  - Urgent customer complaint                        -> ESCALATE + draft reply
  - Meeting requested but date/time unclear          -> draft asking for clarification
                                                         (no calendar event created)
  - requested_action == CREATE_GMAIL_DRAFT           -> draft reply action
  - requested_action == CREATE_TASK                  -> internal task action
  - requested_action == CREATE_CALENDAR_EVENT (+date)-> calendar event action
  - requested_action == ESCALATE                     -> escalation action
  - requested_action == IGNORE / spam                -> ignore action

Every action created here starts with status=PENDING. Nothing is executed
until a human approves it (Phase 5) and the execution service runs it (Phase 6).
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Action, ActionStatus, ActionType, Email, EmailAnalysis, IntentType, PriorityLevel
from app.services.audit import log_event


class ActionSpec:
    """Lightweight in-memory representation of a proposed action, before
    it's persisted as an Action row."""

    def __init__(self, action_type: ActionType, payload: Optional[dict] = None, reason: Optional[str] = None):
        self.action_type = action_type
        self.payload = payload or {}
        self.reason = reason


def _draft_payload(email: Email, reply_text: str) -> dict:
    subject = email.subject or ""
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"
    return {
        "to": email.sender,
        "subject": subject,
        "reply_text": reply_text,
    }


def _calendar_payload(email: Email, analysis: EmailAnalysis) -> dict:
    return {
        "summary": f"Meeting with {email.sender}",
        "description": analysis.summary,
        "date": analysis.meeting_date,
        "time": analysis.meeting_time,
        "attendees": [email.sender],
    }


def _task_payload(email: Email, analysis: EmailAnalysis) -> dict:
    title = f"{analysis.intent.value.replace('_', ' ').title()}: {email.subject}".strip()
    return {
        "title": title[:255],
        "description": analysis.summary,
        "due_date": analysis.deadline,
    }


def plan_actions(email: Email, analysis: EmailAnalysis) -> list[ActionSpec]:
    """Pure planning function: AI analysis -> list of ActionSpec.

    No database access here, so this is easy to unit test in isolation.
    """
    # --- Rule 1: low confidence always escalates -------------------------
    if analysis.confidence_score < settings.confidence_threshold:
        return [
            ActionSpec(
                ActionType.ESCALATE,
                payload={"intent": analysis.intent.value, "summary": analysis.summary},
                reason=(
                    f"Confidence score {analysis.confidence_score:.2f} is below the "
                    f"threshold of {settings.confidence_threshold:.2f}."
                ),
            )
        ]

    # --- Rule 2: urgent customer complaint -> escalate + draft reply ------
    if analysis.intent == IntentType.CUSTOMER_COMPLAINT and analysis.priority == PriorityLevel.HIGH:
        specs = [
            ActionSpec(
                ActionType.ESCALATE,
                payload={"intent": analysis.intent.value, "summary": analysis.summary},
                reason="Urgent customer complaint requires human review.",
            )
        ]
        if analysis.requires_reply and analysis.suggested_reply:
            specs.append(
                ActionSpec(
                    ActionType.CREATE_GMAIL_DRAFT,
                    payload=_draft_payload(email, analysis.suggested_reply),
                    reason="Draft prepared so a response can go out quickly once reviewed.",
                )
            )
        return specs

    # --- Rule 3: meeting requested but date/time unclear -------------------
    if analysis.requested_action == ActionType.CREATE_CALENDAR_EVENT and not analysis.meeting_date:
        clarification = (
            analysis.suggested_reply
            or "Could you confirm a specific date and time for the meeting?"
        )
        return [
            ActionSpec(
                ActionType.CREATE_GMAIL_DRAFT,
                payload=_draft_payload(email, clarification),
                reason="Meeting date/time was unclear, so a clarification draft was prepared instead of a calendar event.",
            )
        ]

    # --- Rule 4: calendar event (date is known) -----------------------------
    if analysis.requested_action == ActionType.CREATE_CALENDAR_EVENT:
        return [ActionSpec(ActionType.CREATE_CALENDAR_EVENT, payload=_calendar_payload(email, analysis))]

    # --- Rule 5: draft reply -------------------------------------------------
    if analysis.requested_action == ActionType.CREATE_GMAIL_DRAFT:
        return [
            ActionSpec(
                ActionType.CREATE_GMAIL_DRAFT,
                payload=_draft_payload(email, analysis.suggested_reply or ""),
            )
        ]

    # --- Rule 6: internal task -----------------------------------------------
    if analysis.requested_action == ActionType.CREATE_TASK:
        return [ActionSpec(ActionType.CREATE_TASK, payload=_task_payload(email, analysis))]

    # --- Rule 7: explicit escalation -----------------------------------------
    if analysis.requested_action == ActionType.ESCALATE:
        return [
            ActionSpec(
                ActionType.ESCALATE,
                payload={"intent": analysis.intent.value, "summary": analysis.summary},
                reason=analysis.summary,
            )
        ]

    # --- Rule 8: ignore / spam -------------------------------------------------
    if analysis.requested_action == ActionType.IGNORE:
        return [ActionSpec(ActionType.IGNORE, payload={"summary": analysis.summary})]

    # --- Fallback: anything unhandled escalates -------------------------------
    return [
        ActionSpec(
            ActionType.ESCALATE,
            payload={"intent": analysis.intent.value, "summary": analysis.summary},
            reason="No planning rule matched this analysis; routed to human review.",
        )
    ]


def create_actions_for_email(db: Session, email_id: int, force: bool = False) -> list[Action]:
    """Run the planner for an email and persist the resulting Action rows.

    If the email already has one or more "live" actions (not REJECTED/FAILED)
    and `force` is False, those existing actions are returned unchanged
    instead of creating duplicates.
    """
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise ValueError(f"Email {email_id} not found")

    analysis = db.query(EmailAnalysis).filter(EmailAnalysis.email_id == email_id).first()
    if not analysis:
        raise ValueError(f"Email {email_id} has not been analyzed yet")

    if not force:
        existing = (
            db.query(Action)
            .filter(
                Action.email_id == email_id,
                Action.status.notin_([ActionStatus.REJECTED, ActionStatus.FAILED]),
            )
            .all()
        )
        if existing:
            return existing

    specs = plan_actions(email, analysis)

    created: list[Action] = []
    for spec in specs:
        action = Action(
            email_id=email_id,
            analysis_id=analysis.id,
            action_type=spec.action_type,
            status=ActionStatus.PENDING,
            payload=spec.payload,
            reason=spec.reason,
        )
        db.add(action)
        db.flush()
        created.append(action)

    db.commit()

    for action in created:
        db.refresh(action)
        log_event(
            db,
            event_type="action_proposed",
            message=f"Proposed action: {action.action_type.value} (status=pending)",
            related_email_id=email_id,
            related_action_id=action.id,
            details={"reason": action.reason},
        )

    return created
