"""
Gmail API integration.

Only used when DEMO_MODE=false. Requires:
  1. A Google Cloud project with the Gmail API enabled.
  2. OAuth client credentials (GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET in .env).
  3. Running this locally at least once so the OAuth consent screen can run
     (google-auth-oauthlib opens a local browser flow). The resulting token
     is cached in GMAIL_TOKEN_FILE for subsequent runs.

Scopes are intentionally minimal:
  - gmail.readonly : list/read messages
  - gmail.compose  : create draft replies (never send automatically)

IMPORTANT SAFETY NOTE:
This service never sends email automatically. Sending requires a separate,
explicit, human-approved action handled in the execution layer (Phase 6).
"""

import base64
import logging
from email.utils import parsedate_to_datetime
from typing import Optional

from googleapiclient.errors import HttpError

from app.services.google_auth import build_service, GoogleAuthError

logger = logging.getLogger("email_automation.gmail")


class GmailServiceError(Exception):
    """Raised when the Gmail API cannot be reached or returns an error."""


def _gmail_service():
    try:
        return build_service("gmail", "v1")
    except GoogleAuthError as exc:
        raise GmailServiceError(str(exc)) from exc


def _decode_body(payload: dict) -> str:
    """Recursively extract a plain-text body from a Gmail message payload."""
    if payload.get("mimeType") == "text/plain" and "data" in payload.get("body", {}):
        data = payload["body"]["data"]
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    # Multipart: prefer text/plain, fall back to text/html stripped of tags.
    for part in payload.get("parts", []) or []:
        if part.get("mimeType") == "text/plain":
            return _decode_body(part)

    for part in payload.get("parts", []) or []:
        if part.get("mimeType") == "text/html":
            html = _decode_body(part)
            return html  # left as-is; AI analysis can handle basic HTML

    # Nested multipart (e.g. multipart/alternative inside multipart/mixed)
    for part in payload.get("parts", []) or []:
        if "parts" in part:
            nested = _decode_body(part)
            if nested:
                return nested

    return ""


def _header(headers: list[dict], name: str) -> str:
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def fetch_unread_emails(max_results: int = 10) -> list[dict]:
    """Fetch unread emails from the connected Gmail account.

    Returns a list of dicts shaped identically to the demo provider:
        {gmail_message_id, sender, subject, body, received_at}
    """
    try:
        service = _gmail_service()

        results = (
            service.users()
            .messages()
            .list(userId="me", labelIds=["UNREAD"], maxResults=max_results)
            .execute()
        )
        messages = results.get("messages", [])

        emails = []
        for msg in messages:
            full = (
                service.users()
                .messages()
                .get(userId="me", id=msg["id"], format="full")
                .execute()
            )
            payload = full.get("payload", {})
            headers = payload.get("headers", [])

            sender = _header(headers, "From")
            subject = _header(headers, "Subject")
            date_str = _header(headers, "Date")

            received_at = None
            if date_str:
                try:
                    received_at = parsedate_to_datetime(date_str).isoformat()
                except (ValueError, TypeError):
                    received_at = None

            body = _decode_body(payload)

            emails.append(
                {
                    "gmail_message_id": full["id"],
                    "sender": sender,
                    "subject": subject,
                    "body": body,
                    "received_at": received_at,
                }
            )

        return emails

    except HttpError as exc:
        raise GmailServiceError(f"Gmail API error: {exc}") from exc
    except GmailServiceError:
        raise
    except Exception as exc:
        raise GmailServiceError(f"Unexpected Gmail error: {exc}") from exc


def create_draft_reply(to: str, subject: str, body_text: str, thread_id: Optional[str] = None) -> dict:
    """Create a Gmail draft. Never sends automatically.

    If `thread_id` is provided, the draft is created as part of that thread
    (a true "reply"). Otherwise a standalone draft is created.

    Returns the Gmail API draft resource (contains 'id').
    """
    import email.mime.text

    try:
        service = _gmail_service()

        message = email.mime.text.MIMEText(body_text)
        message["to"] = to
        message["subject"] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        draft_body: dict = {"message": {"raw": raw}}
        if thread_id:
            draft_body["message"]["threadId"] = thread_id

        draft = service.users().drafts().create(userId="me", body=draft_body).execute()
        return draft

    except HttpError as exc:
        raise GmailServiceError(f"Gmail API error creating draft: {exc}") from exc
    except Exception as exc:
        raise GmailServiceError(f"Unexpected Gmail error creating draft: {exc}") from exc
