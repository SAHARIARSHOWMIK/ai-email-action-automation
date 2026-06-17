"""
AI analysis service.

This is the component that turns raw email text into the structured
fields the rest of the system depends on:

    intent, priority, requires_reply, requested_action, confidence_score,
    summary, suggested_reply, deadline, meeting_date, meeting_time

Reliability strategy:
  - The real analyzer forces structured output by requiring Claude to call
    a `submit_email_analysis` tool with a strict JSON schema (no free text).
  - Every response - real or mock - is validated against AIAnalysisResult
    (app/schemas). If validation fails for any reason, we fall back to a
    low-confidence UNKNOWN/ESCALATE result rather than crashing or storing
    invalid data, and the failure is recorded in raw_ai_response.
"""

import logging

from app.config import settings
from app.models import IntentType, PriorityLevel, ActionType
from app.schemas import AIAnalysisResult
from app.services.mock_analyzer import analyze_email_mock

logger = logging.getLogger("email_automation.ai_analysis")


SYSTEM_PROMPT = """You are an AI assistant inside a business email automation system.
Your job is to read a single email and classify it for a downstream workflow engine.

Supported intents:
  meeting_request, invoice_payment, customer_complaint, job_recruitment,
  project_update, deadline_reminder, general_information, spam_or_ignore, unknown

Supported requested_action values:
  CREATE_GMAIL_DRAFT   - a reply draft should be prepared (do not send)
  CREATE_CALENDAR_EVENT - a meeting/event should be scheduled
  CREATE_TASK          - an internal task/reminder should be created
  ESCALATE             - this needs human review (unclear, sensitive, urgent, or low confidence)
  IGNORE               - no action needed

Guidance:
  - Be conservative with confidence_score. Use lower scores (below 0.75) when the
    email is ambiguous, the date/time is unclear, or the intent is uncertain.
  - For payment, legal, or security-related topics, prefer ESCALATE or CREATE_TASK
    over auto-drafting replies.
  - If a meeting time is mentioned, extract meeting_date as an ISO date (YYYY-MM-DD)
    and meeting_time as a human-readable time (e.g. "3:00 PM"). If unclear, leave both null.
  - If a deadline or due date is mentioned, extract it as an ISO date (YYYY-MM-DD).
  - suggested_reply should be a short, polite draft reply, or an empty string if
    requires_reply is false.
  - Always respond by calling the submit_email_analysis tool. Do not respond with plain text.
"""

ANALYSIS_TOOL = {
    "name": "submit_email_analysis",
    "description": "Submit structured analysis of a single business email.",
    "input_schema": {
        "type": "object",
        "properties": {
            "intent": {
                "type": "string",
                "enum": [e.value for e in IntentType],
            },
            "priority": {
                "type": "string",
                "enum": [p.value for p in PriorityLevel],
            },
            "requires_reply": {"type": "boolean"},
            "requested_action": {
                "type": "string",
                "enum": [a.value for a in ActionType],
            },
            "confidence_score": {
                "type": "number",
                "description": "0.0 to 1.0",
            },
            "summary": {"type": "string"},
            "suggested_reply": {"type": "string"},
            "deadline": {"type": ["string", "null"], "description": "ISO date YYYY-MM-DD or null"},
            "meeting_date": {"type": ["string", "null"], "description": "ISO date YYYY-MM-DD or null"},
            "meeting_time": {"type": ["string", "null"], "description": "e.g. '3:00 PM', or null"},
        },
        "required": [
            "intent",
            "priority",
            "requires_reply",
            "requested_action",
            "confidence_score",
            "summary",
            "suggested_reply",
        ],
    },
}


def _fallback_result(reason: str, raw: dict | None = None) -> AIAnalysisResult:
    """Low-confidence result used whenever the AI output can't be trusted."""
    result = AIAnalysisResult(
        intent=IntentType.UNKNOWN,
        priority=PriorityLevel.LOW,
        requires_reply=False,
        requested_action=ActionType.ESCALATE,
        confidence_score=0.0,
        summary=f"AI analysis could not be completed reliably: {reason}",
        suggested_reply="",
    )
    return result


def _analyze_with_claude(sender: str, subject: str, body: str) -> tuple[AIAnalysisResult, dict]:
    """Call Claude with forced tool-use to get structured JSON output.

    Returns (validated_result, raw_response_dict). On any failure, returns
    a fallback result and a raw_response_dict describing the failure.
    """
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    user_message = (
        f"From: {sender}\n"
        f"Subject: {subject}\n\n"
        f"Body:\n{body}"
    )

    try:
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=[ANALYSIS_TOOL],
            tool_choice={"type": "tool", "name": "submit_email_analysis"},
            messages=[{"role": "user", "content": user_message}],
        )
    except Exception as exc:
        logger.error("Anthropic API call failed: %s", exc)
        return _fallback_result(f"API call failed: {exc}"), {"error": str(exc), "mode": "claude"}

    tool_use_block = next(
        (block for block in response.content if getattr(block, "type", None) == "tool_use"),
        None,
    )

    if tool_use_block is None:
        logger.error("Claude response did not contain a tool_use block")
        return _fallback_result("model did not return structured output"), {
            "error": "no tool_use block",
            "mode": "claude",
            "raw": str(response.content),
        }

    raw_input = tool_use_block.input

    try:
        result = AIAnalysisResult.model_validate(raw_input)
    except Exception as exc:
        logger.error("AI output failed schema validation: %s", exc)
        return _fallback_result(f"schema validation failed: {exc}"), {
            "error": str(exc),
            "mode": "claude",
            "raw_input": raw_input,
        }

    return result, {"mode": "claude", "raw_input": raw_input}


def analyze_email_content(sender: str, subject: str, body: str) -> tuple[AIAnalysisResult, dict]:
    """Main entrypoint: analyze a single email and return a validated result
    plus the raw AI response (for storage / debugging).

    Uses the mock analyzer when DEMO_MODE=true or no API key is configured,
    so the pipeline always works without credentials.
    """
    if settings.demo_mode or not settings.anthropic_api_key:
        result = analyze_email_mock(sender, subject, body)
        return result, {"mode": "mock"}

    return _analyze_with_claude(sender, subject, body)
