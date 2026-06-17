"""
Demo email provider.

Used when DEMO_MODE=true (the default). Returns a fixed set of sample
emails covering every supported intent, so the entire pipeline -
sync -> analyze -> plan -> approve -> execute - can be exercised end
to end without any Gmail credentials.

Each item uses the same shape that the real Gmail service returns from
`fetch_unread_emails`, so downstream code (email_sync.py) doesn't need
to know whether the data came from Gmail or from here.
"""

from datetime import datetime, timedelta


def _iso(days_from_now: int, hour: int = 9) -> str:
    dt = datetime.utcnow() + timedelta(days=days_from_now)
    return dt.replace(hour=hour, minute=0, second=0, microsecond=0).isoformat()


def get_demo_emails() -> list[dict]:
    """Return a fixed list of demo emails (id -> demo-001 ... demo-008)."""
    return [
        {
            "gmail_message_id": "demo-001",
            "sender": "client.acme@example.com",
            "subject": "Project kickoff meeting next week",
            "body": (
                "Hi team,\n\nCan we set up a kickoff call for the new project? "
                "I'm thinking Tuesday at 3pm if that works. We need to align on "
                "scope and timeline before starting development.\n\nThanks,\nJordan"
            ),
            "received_at": _iso(0),
        },
        {
            "gmail_message_id": "demo-002",
            "sender": "billing@vendorsupplies.com",
            "subject": "Invoice #4471 - Payment due June 20",
            "body": (
                "Dear customer,\n\nThis is a reminder that invoice #4471 for "
                "$2,450.00 is due on 2026-06-20. Please process payment via "
                "your usual method or contact us with any questions.\n\n"
                "Vendor Supplies Billing Team"
            ),
            "received_at": _iso(0),
        },
        {
            "gmail_message_id": "demo-003",
            "sender": "angry.customer@example.com",
            "subject": "URGENT: Order #88213 never arrived and no response!",
            "body": (
                "I have emailed twice already and nobody has responded. My order "
                "was supposed to arrive a week ago and I have heard nothing. "
                "This is unacceptable. I want a refund or an explanation "
                "immediately."
            ),
            "received_at": _iso(0),
        },
        {
            "gmail_message_id": "demo-004",
            "sender": "careers@techstartup.io",
            "subject": "Application received - Backend Engineer role",
            "body": (
                "Thank you for applying to the Backend Engineer position at "
                "TechStartup. Our recruiting team will review your application "
                "and get back to you within two weeks."
            ),
            "received_at": _iso(0),
        },
        {
            "gmail_message_id": "demo-005",
            "sender": "pm.lead@example.com",
            "subject": "Weekly project update - Sprint 14",
            "body": (
                "Hi all,\n\nQuick update: Sprint 14 is on track. The API "
                "integration work is 80% complete and QA will begin testing "
                "on Thursday. No blockers at this time.\n\nBest,\nPM Lead"
            ),
            "received_at": _iso(0),
        },
        {
            "gmail_message_id": "demo-006",
            "sender": "contracts@partnerfirm.com",
            "subject": "Reminder: contract renewal deadline approaching",
            "body": (
                "This is a reminder that the service contract renewal deadline "
                "is 2026-06-25. Please review the attached terms and confirm "
                "renewal before this date to avoid service interruption."
            ),
            "received_at": _iso(0),
        },
        {
            "gmail_message_id": "demo-007",
            "sender": "newsletter@randomdeals.net",
            "subject": "50% OFF everything this weekend only!!!",
            "body": (
                "Don't miss our biggest sale of the year! Click here to save "
                "50% on all items. Limited time offer, shop now!"
            ),
            "received_at": _iso(0),
        },
        {
            "gmail_message_id": "demo-008",
            "sender": "colleague@example.com",
            "subject": "Quick question about the API docs",
            "body": (
                "Hey, do you know where the latest version of the API "
                "documentation is hosted? I couldn't find it in the shared "
                "drive. Thanks!"
            ),
            "received_at": _iso(0),
        },
    ]
