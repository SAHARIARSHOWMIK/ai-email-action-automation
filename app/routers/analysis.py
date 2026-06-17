"""
Email analysis endpoints:
  POST /emails/{id}/analyze   - run AI analysis on an email and save the result
  GET  /emails/{id}/analysis  - retrieve a previously saved analysis
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Email, EmailAnalysis
from app.schemas import EmailAnalysisOut
from app.services.ai_analysis import analyze_email_content
from app.services.audit import log_event

router = APIRouter(prefix="/emails", tags=["analysis"])


@router.post("/{email_id}/analyze", response_model=EmailAnalysisOut)
def analyze_email(email_id: int, db: Session = Depends(get_db)):
    """Run AI analysis on the given email and save (or update) the result.

    Re-running this on an already-analyzed email overwrites the previous
    analysis - useful if the AI prompt/model changes.
    """
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    result, raw_response = analyze_email_content(email.sender, email.subject, email.body)

    existing = db.query(EmailAnalysis).filter(EmailAnalysis.email_id == email_id).first()

    if existing:
        analysis = existing
    else:
        analysis = EmailAnalysis(email_id=email_id)
        db.add(analysis)

    analysis.intent = result.intent
    analysis.priority = result.priority
    analysis.requires_reply = result.requires_reply
    analysis.requested_action = result.requested_action
    analysis.confidence_score = result.confidence_score
    analysis.summary = result.summary
    analysis.suggested_reply = result.suggested_reply
    analysis.deadline = result.deadline
    analysis.meeting_date = result.meeting_date
    analysis.meeting_time = result.meeting_time
    analysis.raw_ai_response = raw_response

    db.commit()
    db.refresh(analysis)

    log_event(
        db,
        event_type="email_analyzed",
        message=f"Email analyzed: intent={result.intent.value}, "
        f"confidence={result.confidence_score:.2f}, action={result.requested_action.value}",
        related_email_id=email_id,
        details={"mode": raw_response.get("mode")},
    )

    return analysis


@router.get("/{email_id}/analysis", response_model=EmailAnalysisOut)
def get_analysis(email_id: int, db: Session = Depends(get_db)):
    """Get the saved analysis for an email, if it has been analyzed."""
    analysis = db.query(EmailAnalysis).filter(EmailAnalysis.email_id == email_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="This email has not been analyzed yet")
    return analysis
