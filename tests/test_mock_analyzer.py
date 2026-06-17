"""
Tests for the mock analyzer (app.services.mock_analyzer), run against the
demo seed emails. These ensure DEMO_MODE produces sensible, varied
classifications without any AI credentials.
"""

from app.models import ActionType, IntentType
from app.services.demo_emails import get_demo_emails
from app.services.mock_analyzer import analyze_email_mock

EXPECTED_INTENTS = {
    "demo-001": IntentType.MEETING_REQUEST,      # kickoff meeting
    "demo-002": IntentType.INVOICE_PAYMENT,       # invoice due
    "demo-003": IntentType.CUSTOMER_COMPLAINT,    # urgent, never arrived, refund
    "demo-004": IntentType.JOB_RECRUITMENT,       # application received
    "demo-005": IntentType.PROJECT_UPDATE,        # sprint update
    "demo-006": IntentType.DEADLINE_REMINDER,     # contract renewal deadline
    "demo-007": IntentType.SPAM_OR_IGNORE,        # 50% off sale
    "demo-008": IntentType.GENERAL_INFORMATION,   # quick question
}


def _demo_email_by_id(message_id: str) -> dict:
    return next(e for e in get_demo_emails() if e["gmail_message_id"] == message_id)


def test_all_demo_emails_have_an_expected_intent_mapping():
    demo_ids = {e["gmail_message_id"] for e in get_demo_emails()}
    assert demo_ids == set(EXPECTED_INTENTS.keys())


def test_each_demo_email_classifies_as_expected():
    for message_id, expected_intent in EXPECTED_INTENTS.items():
        email = _demo_email_by_id(message_id)
        result = analyze_email_mock(email["sender"], email["subject"], email["body"])
        assert result.intent == expected_intent, f"{message_id} expected {expected_intent}, got {result.intent}"


def test_meeting_email_extracts_date_and_time():
    email = _demo_email_by_id("demo-001")
    result = analyze_email_mock(email["sender"], email["subject"], email["body"])

    assert result.requested_action == ActionType.CREATE_CALENDAR_EVENT
    assert result.meeting_date is not None
    assert result.meeting_time is not None


def test_invoice_email_extracts_deadline():
    email = _demo_email_by_id("demo-002")
    result = analyze_email_mock(email["sender"], email["subject"], email["body"])

    assert result.deadline == "2026-06-20"


def test_urgent_complaint_has_high_priority_and_escalates():
    email = _demo_email_by_id("demo-003")
    result = analyze_email_mock(email["sender"], email["subject"], email["body"])

    assert result.priority.value == "high"
    assert result.requested_action == ActionType.ESCALATE
    assert result.requires_reply is True


def test_spam_email_is_ignored_with_high_confidence():
    email = _demo_email_by_id("demo-007")
    result = analyze_email_mock(email["sender"], email["subject"], email["body"])

    assert result.requested_action == ActionType.IGNORE
    assert result.confidence_score >= 0.75


def test_unrecognized_text_falls_back_to_unknown_and_escalates():
    result = analyze_email_mock("someone@example.com", "asdf", "qwerty zzzz nothing matches")

    assert result.intent == IntentType.UNKNOWN
    assert result.requested_action == ActionType.ESCALATE
    assert result.confidence_score < 0.75  # below threshold -> planner will escalate too
