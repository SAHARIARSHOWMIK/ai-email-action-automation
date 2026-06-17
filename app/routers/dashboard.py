"""
Dashboard support endpoints:
  GET /dashboard/metrics  - summary counts for the dashboard home page
  GET /audit-logs         - full audit trail, most recent first
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Email, EmailAnalysis, Action, ActionStatus, AuditLog
from app.schemas import DashboardMetrics, AuditLogOut

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/metrics", response_model=DashboardMetrics)
def get_metrics(db: Session = Depends(get_db)):
    """Summary counts used by the dashboard home page."""
    total_emails = db.query(Email).count()
    emails_analyzed = db.query(EmailAnalysis).count()

    pending_actions = (
        db.query(Action)
        .filter(Action.status.in_([ActionStatus.PENDING, ActionStatus.EDITED]))
        .count()
    )
    approved_actions = db.query(Action).filter(Action.status == ActionStatus.APPROVED).count()
    executed_actions = db.query(Action).filter(Action.status == ActionStatus.EXECUTED).count()
    escalated_emails = db.query(Action).filter(Action.status == ActionStatus.ESCALATED).count()

    return DashboardMetrics(
        total_emails=total_emails,
        emails_analyzed=emails_analyzed,
        pending_actions=pending_actions,
        approved_actions=approved_actions,
        executed_actions=executed_actions,
        escalated_emails=escalated_emails,
    )


@router.get("/audit-logs", response_model=list[AuditLogOut])
def list_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Full audit trail, most recent first."""
    return (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
