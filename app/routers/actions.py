"""
Action endpoints:
  POST /emails/{id}/plan  - run the action planner for an email and persist proposed action(s)
  GET  /actions           - list actions (optionally filtered by status)
  GET  /actions/{id}      - get a single action

Approval/rejection/editing endpoints are added in Phase 5,
and execution endpoints in Phase 6.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Action, ActionStatus, Email, EmailAnalysis
from app.schemas import ActionOut, ActionEditRequest, ActionRejectRequest, ActionDecisionResponse
from app.services.action_planner import create_actions_for_email
from app.services.approval import (
    approve_action,
    reject_action,
    edit_action_payload,
    ApprovalError,
)
from app.services.execution import execute_action

router = APIRouter(tags=["actions"])


@router.post("/emails/{email_id}/plan", response_model=list[ActionOut])
def plan_email_actions(
    email_id: int,
    force: bool = Query(False, description="Re-run the planner even if actions already exist"),
    db: Session = Depends(get_db),
):
    """Run the action planner for an analyzed email.

    Returns the proposed action(s). If actions already exist for this email
    and `force` is not set, the existing actions are returned unchanged.
    """
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    analysis = db.query(EmailAnalysis).filter(EmailAnalysis.email_id == email_id).first()
    if not analysis:
        raise HTTPException(status_code=400, detail="This email has not been analyzed yet. Call /emails/{id}/analyze first.")

    return create_actions_for_email(db, email_id, force=force)


@router.get("/actions", response_model=list[ActionOut])
def list_actions(
    status: Optional[ActionStatus] = Query(None, description="Filter by action status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List actions, most recently created first. Optionally filter by status,
    e.g. ?status=pending to get the approval queue."""
    query = db.query(Action)
    if status is not None:
        query = query.filter(Action.status == status)
    return query.order_by(Action.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/actions/{action_id}", response_model=ActionOut)
def get_action(action_id: int, db: Session = Depends(get_db)):
    """Get a single action by ID."""
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return action


@router.post("/actions/{action_id}/approve", response_model=ActionDecisionResponse)
def approve(action_id: int, db: Session = Depends(get_db)):
    """Approve a pending or edited action, making it eligible for execution.

    Only actions with status 'pending' or 'edited' can be approved.
    """
    try:
        action = approve_action(db, action_id)
    except ApprovalError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return ActionDecisionResponse(action=action, message=f"Action {action_id} approved.")


@router.post("/actions/{action_id}/reject", response_model=ActionDecisionResponse)
def reject(action_id: int, body: ActionRejectRequest = ActionRejectRequest(), db: Session = Depends(get_db)):
    """Reject a pending or edited action. Rejected actions are never executed."""
    try:
        action = reject_action(db, action_id, reason=body.reason)
    except ApprovalError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return ActionDecisionResponse(action=action, message=f"Action {action_id} rejected.")


@router.patch("/actions/{action_id}", response_model=ActionDecisionResponse)
def edit(action_id: int, body: ActionEditRequest, db: Session = Depends(get_db)):
    """Edit a pending action's payload before approval (e.g. tweak a draft
    reply's text, or correct a meeting time). Sets status to 'edited' -
    the action must still be approved afterwards before it can execute.
    """
    try:
        action = edit_action_payload(db, action_id, body.payload)
    except ApprovalError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return ActionDecisionResponse(action=action, message=f"Action {action_id} updated.")


@router.post("/actions/{action_id}/execute", response_model=ActionDecisionResponse)
def execute(action_id: int, db: Session = Depends(get_db)):
    """Execute an approved action.

    - CREATE_GMAIL_DRAFT: creates a Gmail draft (real or mock)
    - CREATE_CALENDAR_EVENT: creates a Calendar event (real or mock)
    - CREATE_TASK: creates an internal Task record
    - ESCALATE: marks the action as escalated (status -> 'escalated')
    - IGNORE: marks the action as handled with no side effects

    Only actions with status 'approved' can be executed. An action with
    status 'failed' can be retried by calling this endpoint again.
    On failure, status is set to 'failed' and execution_result contains
    the error - no exception is raised to the caller in that case.
    """
    try:
        action = execute_action(db, action_id)
    except ApprovalError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if action.status == ActionStatus.FAILED:
        message = f"Action {action_id} execution failed: {action.execution_result.get('error')}"
    elif action.status == ActionStatus.ESCALATED:
        message = f"Action {action_id} escalated for human review."
    else:
        message = f"Action {action_id} executed successfully."

    return ActionDecisionResponse(action=action, message=message)
