"""
Shared Google OAuth credential management.

Both gmail_service.py and calendar_service.py authenticate against the
same Google Cloud project / OAuth client, so credentials and scopes are
managed in one place.

Scopes (kept minimal, as required by the project's safety rules):
  - gmail.readonly      : list/read messages
  - gmail.compose       : create draft replies (never send automatically)
  - calendar.events     : create calendar events

Only used when DEMO_MODE=false.
"""

import logging
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from app.config import settings

logger = logging.getLogger("email_automation.google_auth")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/calendar.events",
]


class GoogleAuthError(Exception):
    """Raised when Google OAuth credentials cannot be obtained."""


def get_credentials() -> Credentials:
    """Load cached OAuth credentials, refreshing or re-authenticating as needed."""
    creds: Optional[Credentials] = None
    token_file = settings.gmail_token_file

    try:
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    except FileNotFoundError:
        creds = None
    except Exception as exc:
        logger.warning("Could not load token file %s: %s", token_file, exc)
        creds = None

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(creds, token_file)
            return creds
        except Exception as exc:
            logger.warning("Token refresh failed, re-authenticating: %s", exc)

    if not settings.google_client_id or not settings.google_client_secret:
        raise GoogleAuthError(
            "Google credentials are not configured. Set GOOGLE_CLIENT_ID and "
            "GOOGLE_CLIENT_SECRET in .env, or set DEMO_MODE=true to use sample data."
        )

    client_config = {
        "installed": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.google_redirect_uri],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0)
    _save_token(creds, token_file)
    return creds


def _save_token(creds: Credentials, token_file: str) -> None:
    with open(token_file, "w") as f:
        f.write(creds.to_json())


def build_service(api_name: str, api_version: str):
    """Build an authenticated Google API client, e.g. build_service('gmail', 'v1')."""
    creds = get_credentials()
    return build(api_name, api_version, credentials=creds)
