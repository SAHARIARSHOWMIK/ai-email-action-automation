"""
Mock AI analyzer.

Used when DEMO_MODE=true (or no ANTHROPIC_API_KEY is set), so the full
pipeline - sync -> analyze -> plan -> approve -> execute - works without
any AI credentials.

This is intentionally simple keyword/regex matching. It is NOT a
replacement for the real LLM analyzer in ai_analysis.py - it exists only
to produce plausible, varied, structured output for the demo seed emails
(and reasonable fallbacks for arbitrary text).
"""

import re

from app.models import IntentType, PriorityLevel, ActionType
from app.schemas import AIAnalysisResult
from app.services.text_extraction import extract_iso_date, extract_meeting_datetime


def _contains_any(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def analyze_email_mock(sender: str, subject: str, body: str) -> AIAnalysisResult:
    """Rule-based stand-in for the LLM analyzer."""
    full_text = f"{subject}\n{body}"
    full_lower = full_text.lower()

    # --- Spam / promotional ---------------------------------------------
    if _contains_any(full_lower, ["% off", "limited time", "click here", "shop now", "biggest sale"]):
        return AIAnalysisResult(
            intent=IntentType.SPAM_OR_IGNORE,
            priority=PriorityLevel.LOW,
            requires_reply=False,
            requested_action=ActionType.IGNORE,
            confidence_score=0.95,
            summary="Promotional/marketing email, not relevant to business workflow.",
            suggested_reply="",
        )

    # --- Urgent customer complaint ----------------------------------------
    if _contains_any(full_lower, ["urgent", "refund", "unacceptable", "never arrived"]):
        return AIAnalysisResult(
            intent=IntentType.CUSTOMER_COMPLAINT,
            priority=PriorityLevel.HIGH,
            requires_reply=True,
            requested_action=ActionType.ESCALATE,
            confidence_score=0.88,
            summary="Customer is upset about a missing order and is requesting a refund or response.",
            suggested_reply=(
                "Hi, I'm sorry to hear about the trouble with your order. "
                "I'm escalating this to our team right now and someone will "
                "follow up with a resolution shortly."
            ),
        )

    # --- Meeting request -----------------------------------------------
    if _contains_any(full_lower, ["meeting", "kickoff", "call", "schedule"]):
        meeting_date, meeting_time = extract_meeting_datetime(full_text)
        return AIAnalysisResult(
            intent=IntentType.MEETING_REQUEST,
            priority=PriorityLevel.MEDIUM,
            requires_reply=True,
            requested_action=ActionType.CREATE_CALENDAR_EVENT if meeting_date else ActionType.CREATE_GMAIL_DRAFT,
            confidence_score=0.9 if meeting_date else 0.6,
            summary="Sender is requesting a meeting and proposing a time.",
            suggested_reply=(
                f"Hi, that time works for me - looking forward to the meeting "
                f"on {meeting_date} at {meeting_time}." if meeting_date else
                "Hi, thanks for reaching out - could you suggest a specific date and time for the meeting?"
            ),
            meeting_date=meeting_date,
            meeting_time=meeting_time,
        )

    # --- Invoice / payment -----------------------------------------------
    if _contains_any(full_lower, ["invoice", "payment due", "amount due"]):
        deadline = extract_iso_date(full_text)
        return AIAnalysisResult(
            intent=IntentType.INVOICE_PAYMENT,
            priority=PriorityLevel.HIGH,
            requires_reply=False,
            requested_action=ActionType.CREATE_TASK,
            confidence_score=0.85,
            summary="Invoice received with a payment due date; needs to be tracked as a task.",
            suggested_reply="",
            deadline=deadline,
        )

    # --- Deadline / contract reminder ------------------------------------
    if _contains_any(full_lower, ["deadline", "renewal", "reminder"]):
        deadline = extract_iso_date(full_text)
        return AIAnalysisResult(
            intent=IntentType.DEADLINE_REMINDER,
            priority=PriorityLevel.MEDIUM,
            requires_reply=False,
            requested_action=ActionType.CREATE_TASK,
            confidence_score=0.82,
            summary="Reminder about an upcoming deadline that should be tracked.",
            suggested_reply="",
            deadline=deadline,
        )

    # --- Job recruitment ---------------------------------------------------
    if _contains_any(full_lower, ["application", "recruiting", "career", "position"]):
        return AIAnalysisResult(
            intent=IntentType.JOB_RECRUITMENT,
            priority=PriorityLevel.LOW,
            requires_reply=False,
            requested_action=ActionType.IGNORE,
            confidence_score=0.9,
            summary="Automated recruitment/application confirmation email.",
            suggested_reply="",
        )

    # --- Project update ----------------------------------------------------
    if _contains_any(full_lower, ["sprint", "project update", "on track", "status update"]):
        return AIAnalysisResult(
            intent=IntentType.PROJECT_UPDATE,
            priority=PriorityLevel.LOW,
            requires_reply=False,
            requested_action=ActionType.IGNORE,
            confidence_score=0.9,
            summary="Routine internal project status update, no action required.",
            suggested_reply="",
        )

    # --- Generic question / information request -------------------------
    if "?" in full_text:
        return AIAnalysisResult(
            intent=IntentType.GENERAL_INFORMATION,
            priority=PriorityLevel.LOW,
            requires_reply=True,
            requested_action=ActionType.CREATE_GMAIL_DRAFT,
            confidence_score=0.8,
            summary="Sender is asking a general question and likely expects a reply.",
            suggested_reply="Hi, thanks for the question - let me look into that and get back to you shortly.",
        )

    # --- Fallback: unknown / low confidence -------------------------------
    return AIAnalysisResult(
        intent=IntentType.UNKNOWN,
        priority=PriorityLevel.LOW,
        requires_reply=False,
        requested_action=ActionType.ESCALATE,
        confidence_score=0.4,
        summary="Could not confidently determine the intent of this email.",
        suggested_reply="",
    )
