"""
Email endpoints:
  POST /emails/sync   - fetch new emails (demo or Gmail) into the database
  GET  /emails        - list synced emails
  GET  /emails/{id}   - single email, including analysis if available
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Email
from app.schemas import EmailOut, EmailSyncResult, EmailAnalysisOut
from app.services.email_sync import sync_emails
from app.services.gmail_service import GmailServiceError

router = APIRouter(prefix="/emails", tags=["emails"])


@router.post("/sync", response_model=EmailSyncResult)
def sync(max_results: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    """Fetch unread emails (from Gmail, or demo seed data if DEMO_MODE=true)
    and store any new ones. Duplicate emails (same gmail_message_id) are skipped.
    """
    try:
        return sync_emails(db, max_results=max_results)
    except GmailServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("", response_model=list[EmailOut])
def list_emails(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List synced emails, most recent first."""
    return (
        db.query(Email)
        .order_by(Email.synced_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


class EmailDetail(EmailOut):
    analysis: Optional[EmailAnalysisOut] = None


@router.get("/{email_id}", response_model=EmailDetail)
def get_email(email_id: int, db: Session = Depends(get_db)):
    """Get a single email, including its AI analysis if it has been analyzed."""
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email
