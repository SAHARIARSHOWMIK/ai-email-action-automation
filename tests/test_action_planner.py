"""
Unit tests for app.services.action_planner.plan_actions.

These operate on plain (unsaved) Email/EmailAnalysis instances, so they
run without touching the database - they test the planning *rules* in
isolation from persistence.
"""

from app.models import ActionType, Email, EmailAnalysis, IntentType, PriorityLevel
from app.services.action_planner import plan_actions


def make_email(**overrides) -> Email:
    defaults = dict(
        gmail_message_id="test-msg",
        sender="sender@example.com",
        subject="Test subject",
        body="Test body",
    )
    defaults.update(overrides)
    return Email(**defaults)


def make_analysis(**overrides) -> EmailAnalysis:
    defaults = dict(
        intent=IntentType.UNKNOWN,
        priority=PriorityLevel.LOW,
        requires_reply=False,
        requested_action=ActionType.IGNORE,
        confidence_score=0.9,
        summary="summary",
        suggested_reply="",
    )
    defaults.update(overrides)
    return EmailAnalysis(**defaults)


def test_low_confidence_always_escalates():
    email = make_email()
    analysis = make_analysis(
        requested_action=ActionType.CREATE_CALENDAR_EVENT,
        confidence_score=0.5,  # below default threshold of 0.75
    )

    specs = plan_actions(email, analysis)

    assert len(specs) == 1
    assert specs[0].action_type == ActionType.ESCALATE
    assert "below the threshold" in specs[0].reason


def test_urgent_complaint_creates_escalate_and_draft():
    email = make_email(subject="Order problem")
    analysis = make_analysis(
        intent=IntentType.CUSTOMER_COMPLAINT,
        priority=PriorityLevel.HIGH,
        requires_reply=True,
        requested_action=ActionType.ESCALATE,
        confidence_score=0.9,
        suggested_reply="Sorry about that, we're looking into it.",
    )

    specs = plan_actions(email, analysis)

    assert len(specs) == 2
    assert specs[0].action_type == ActionType.ESCALATE
    assert specs[1].action_type == ActionType.CREATE_GMAIL_DRAFT
    assert specs[1].payload["to"] == "sender@example.com"
    assert specs[1].payload["subject"] == "Re: Order problem"


def test_meeting_request_with_known_time_creates_calendar_event():
    email = make_email(sender="client@example.com")
    analysis = make_analysis(
        intent=IntentType.MEETING_REQUEST,
        priority=PriorityLevel.MEDIUM,
        requires_reply=True,
        requested_action=ActionType.CREATE_CALENDAR_EVENT,
        confidence_score=0.9,
        meeting_date="2026-06-21",
        meeting_time="3PM",
    )

    specs = plan_actions(email, analysis)

    assert len(specs) == 1
    assert specs[0].action_type == ActionType.CREATE_CALENDAR_EVENT
    assert specs[0].payload["date"] == "2026-06-21"
    assert specs[0].payload["time"] == "3PM"
    assert specs[0].payload["attendees"] == ["client@example.com"]


def test_meeting_request_without_date_creates_clarification_draft_not_calendar_event():
    email = make_email()
    analysis = make_analysis(
        intent=IntentType.MEETING_REQUEST,
        priority=PriorityLevel.MEDIUM,
        requires_reply=True,
        requested_action=ActionType.CREATE_CALENDAR_EVENT,
        confidence_score=0.9,
        meeting_date=None,
        meeting_time=None,
        suggested_reply="Could you confirm a time?",
    )

    specs = plan_actions(email, analysis)

    assert len(specs) == 1
    assert specs[0].action_type == ActionType.CREATE_GMAIL_DRAFT
    assert "unclear" in specs[0].reason.lower()


def test_invoice_creates_task_with_due_date():
    email = make_email(subject="Invoice #4471")
    analysis = make_analysis(
        intent=IntentType.INVOICE_PAYMENT,
        priority=PriorityLevel.HIGH,
        requested_action=ActionType.CREATE_TASK,
        confidence_score=0.85,
        deadline="2026-06-20",
        summary="Invoice due soon",
    )

    specs = plan_actions(email, analysis)

    assert len(specs) == 1
    assert specs[0].action_type == ActionType.CREATE_TASK
    assert specs[0].payload["due_date"] == "2026-06-20"
    assert "Invoice" in specs[0].payload["title"]


def test_spam_creates_ignore_action():
    email = make_email(subject="50% off everything")
    analysis = make_analysis(
        intent=IntentType.SPAM_OR_IGNORE,
        priority=PriorityLevel.LOW,
        requested_action=ActionType.IGNORE,
        confidence_score=0.95,
    )

    specs = plan_actions(email, analysis)

    assert len(specs) == 1
    assert specs[0].action_type == ActionType.IGNORE


def test_general_reply_creates_draft():
    email = make_email(sender="colleague@example.com", subject="Quick question")
    analysis = make_analysis(
        intent=IntentType.GENERAL_INFORMATION,
        priority=PriorityLevel.LOW,
        requires_reply=True,
        requested_action=ActionType.CREATE_GMAIL_DRAFT,
        confidence_score=0.8,
        suggested_reply="Sure, here's the info.",
    )

    specs = plan_actions(email, analysis)

    assert len(specs) == 1
    assert specs[0].action_type == ActionType.CREATE_GMAIL_DRAFT
    assert specs[0].payload["reply_text"] == "Sure, here's the info."
