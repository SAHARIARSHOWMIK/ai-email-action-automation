"""
Unit tests for structured-output validation (app.schemas.AIAnalysisResult)
and the fallback path used when AI output is invalid
(app.services.ai_analysis._fallback_result).

These cover the "invalid AI output does not crash the system" requirement.
"""

import pytest
from pydantic import ValidationError

from app.models import ActionType, IntentType, PriorityLevel
from app.schemas import AIAnalysisResult
from app.services.ai_analysis import _fallback_result


def test_valid_analysis_result_parses():
    result = AIAnalysisResult(
        intent=IntentType.MEETING_REQUEST,
        priority=PriorityLevel.MEDIUM,
        requires_reply=True,
        requested_action=ActionType.CREATE_CALENDAR_EVENT,
        confidence_score=0.9,
        summary="Client wants a meeting",
        suggested_reply="Sounds good, see you then.",
        meeting_date="2026-06-21",
        meeting_time="3:00 PM",
    )
    assert result.intent == IntentType.MEETING_REQUEST
    assert result.confidence_score == 0.9


@pytest.mark.parametrize("raw_score,expected", [(1.5, 1.0), (-0.3, 0.0), (0.75, 0.75)])
def test_confidence_score_is_clamped(raw_score, expected):
    result = AIAnalysisResult(
        intent=IntentType.UNKNOWN,
        priority=PriorityLevel.LOW,
        requires_reply=False,
        requested_action=ActionType.ESCALATE,
        confidence_score=raw_score,
        summary="",
        suggested_reply="",
    )
    assert result.confidence_score == expected


def test_invalid_intent_value_raises_validation_error():
    with pytest.raises(ValidationError):
        AIAnalysisResult(
            intent="not_a_real_intent",
            priority=PriorityLevel.LOW,
            requires_reply=False,
            requested_action=ActionType.ESCALATE,
            confidence_score=0.5,
            summary="",
            suggested_reply="",
        )


def test_missing_required_field_raises_validation_error():
    with pytest.raises(ValidationError):
        # confidence_score is required
        AIAnalysisResult(
            intent=IntentType.UNKNOWN,
            priority=PriorityLevel.LOW,
            requires_reply=False,
            requested_action=ActionType.ESCALATE,
            summary="",
            suggested_reply="",
        )


def test_fallback_result_is_safe_and_escalates():
    """When the AI output can't be trusted, the fallback must be a valid,
    low-confidence result that routes to human review - never a crash."""
    result = _fallback_result("schema validation failed: bad enum value")

    assert isinstance(result, AIAnalysisResult)
    assert result.intent == IntentType.UNKNOWN
    assert result.requested_action == ActionType.ESCALATE
    assert result.confidence_score == 0.0
    assert "schema validation failed" in result.summary
