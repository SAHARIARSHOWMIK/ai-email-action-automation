"""One-click demo workspace bootstrap endpoint.

The endpoint is intentionally available only when DEMO_MODE=true. It syncs the
controlled sample inbox, analyzes every email, and creates proposed actions.
It does not approve or execute anything, preserving the human-in-the-loop rule.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Email
from app.schemas import DemoBootstrapResult
from app.services.email_sync import sync_emails
from app.services.ai_analysis import analyze_email_content
from app.models import EmailAnalysis
from app.services.action_planner import create_actions_for_email
from app.services.audit import log_event

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/bootstrap", response_model=DemoBootstrapResult)
def bootstrap_demo(db: Session = Depends(get_db)):
    if not settings.demo_mode:
        raise HTTPException(status_code=403, detail="Demo bootstrap is disabled outside demo mode")

    sync_result = sync_emails(db, max_results=50)
    emails = db.query(Email).order_by(Email.id.asc()).all()
    analyzed = 0
    actions_created = 0

    for email in emails:
        analysis = db.query(EmailAnalysis).filter(EmailAnalysis.email_id == email.id).first()
        if analysis is None:
            result, raw = analyze_email_content(email.sender, email.subject, email.body)
            analysis = EmailAnalysis(
                email_id=email.id,
                intent=result.intent,
                priority=result.priority,
                requires_reply=result.requires_reply,
                requested_action=result.requested_action,
                confidence_score=result.confidence_score,
                summary=result.summary,
                suggested_reply=result.suggested_reply,
                deadline=result.deadline,
                meeting_date=result.meeting_date,
                meeting_time=result.meeting_time,
                raw_ai_response=raw,
            )
            db.add(analysis)
            db.commit()
            db.refresh(analysis)
            analyzed += 1
            log_event(
                db,
                event_type="email_analyzed",
                message="Email analyzed during demo bootstrap.",
                related_email_id=email.id,
                details={"mode": raw.get("mode", "mock")},
            )

        before = len(email.actions)
        created = create_actions_for_email(db, email.id, force=False)
        if before == 0:
            actions_created += len(created)

    log_event(
        db,
        event_type="demo_workspace_ready",
        message="Demo workspace synced, analyzed, and planned.",
        details={"emails": len(emails), "analyzed": analyzed, "actions_created": actions_created},
    )

    return DemoBootstrapResult(
        emails_total=len(emails),
        emails_added=sync_result.new,
        emails_analyzed=analyzed,
        actions_created=actions_created,
        message="Demo workspace is ready for human review.",
    )
