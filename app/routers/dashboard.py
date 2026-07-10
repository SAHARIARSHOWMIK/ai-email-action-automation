"""Dashboard analytics and audit endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Email,
    EmailAnalysis,
    Action,
    ActionStatus,
    AuditLog,
    Task,
    PriorityLevel,
)
from app.schemas import DashboardMetrics, DashboardOverview, AuditLogOut

router = APIRouter(tags=["dashboard"])


def _metrics(db: Session) -> DashboardMetrics:
    return DashboardMetrics(
        total_emails=db.query(Email).count(),
        emails_analyzed=db.query(EmailAnalysis).count(),
        pending_actions=db.query(Action)
        .filter(Action.status.in_([ActionStatus.PENDING, ActionStatus.EDITED]))
        .count(),
        approved_actions=db.query(Action).filter(Action.status == ActionStatus.APPROVED).count(),
        executed_actions=db.query(Action).filter(Action.status == ActionStatus.EXECUTED).count(),
        escalated_emails=db.query(Action).filter(Action.status == ActionStatus.ESCALATED).count(),
    )


@router.get("/dashboard/metrics", response_model=DashboardMetrics)
def get_metrics(db: Session = Depends(get_db)):
    return _metrics(db)


@router.get("/dashboard/overview", response_model=DashboardOverview)
def get_overview(db: Session = Depends(get_db)):
    metrics = _metrics(db)
    total_actions = db.query(Action).count()
    terminal_actions = (
        db.query(Action)
        .filter(
            Action.status.in_(
                [
                    ActionStatus.EXECUTED,
                    ActionStatus.ESCALATED,
                    ActionStatus.REJECTED,
                ]
            )
        )
        .count()
    )
    automated_actions = db.query(Action).filter(Action.status == ActionStatus.EXECUTED).count()

    average_confidence = db.query(func.avg(EmailAnalysis.confidence_score)).scalar() or 0.0
    high_priority_emails = (
        db.query(EmailAnalysis)
        .filter(EmailAnalysis.priority == PriorityLevel.HIGH)
        .count()
    )
    open_tasks = db.query(Task).filter(Task.status == "open").count()

    intent_distribution = {
        str(intent.value if hasattr(intent, "value") else intent): count
        for intent, count in db.query(EmailAnalysis.intent, func.count(EmailAnalysis.id))
        .group_by(EmailAnalysis.intent)
        .all()
    }
    priority_distribution = {
        str(priority.value if hasattr(priority, "value") else priority): count
        for priority, count in db.query(EmailAnalysis.priority, func.count(EmailAnalysis.id))
        .group_by(EmailAnalysis.priority)
        .all()
    }
    action_status_distribution = {
        str(status.value if hasattr(status, "value") else status): count
        for status, count in db.query(Action.status, func.count(Action.id))
        .group_by(Action.status)
        .all()
    }
    action_type_distribution = {
        str(action_type.value if hasattr(action_type, "value") else action_type): count
        for action_type, count in db.query(Action.action_type, func.count(Action.id))
        .group_by(Action.action_type)
        .all()
    }

    recent_activity = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(10)
        .all()
    )

    return DashboardOverview(
        metrics=metrics,
        analysis_rate=round((metrics.emails_analyzed / metrics.total_emails * 100), 1)
        if metrics.total_emails
        else 0.0,
        completion_rate=round((terminal_actions / total_actions * 100), 1)
        if total_actions
        else 0.0,
        automation_rate=round((automated_actions / total_actions * 100), 1)
        if total_actions
        else 0.0,
        average_confidence=round(float(average_confidence), 3),
        high_priority_emails=high_priority_emails,
        open_tasks=open_tasks,
        intent_distribution=intent_distribution,
        priority_distribution=priority_distribution,
        action_status_distribution=action_status_distribution,
        action_type_distribution=action_type_distribution,
        recent_activity=recent_activity,
    )


@router.get("/audit-logs", response_model=list[AuditLogOut])
def list_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    event_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(AuditLog)
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
    return query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
