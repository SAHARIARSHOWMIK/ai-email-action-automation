"""
Pydantic schemas used for API request/response bodies.

Kept separate from SQLAlchemy models (app/models.py) so the database
layer and the API contract can evolve independently.
"""

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import IntentType, PriorityLevel, ActionType, ActionStatus


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

class EmailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    gmail_message_id: str
    sender: str
    subject: str
    body: str
    received_at: Optional[datetime] = None
    synced_at: datetime
    is_demo: bool


class EmailSyncResult(BaseModel):
    fetched: int
    new: int
    duplicates: int
    source: str  # "gmail" | "demo"


# ---------------------------------------------------------------------------
# AI analysis - structured output contract
# ---------------------------------------------------------------------------

class AIAnalysisResult(BaseModel):
    """The structured shape the AI (or mock analyzer) must produce.

    This is validated immediately after the AI call. If validation fails,
    the analysis service falls back to a low-confidence UNKNOWN/ESCALATE
    result rather than crashing or storing garbage.
    """

    intent: IntentType
    priority: PriorityLevel
    requires_reply: bool = False
    requested_action: ActionType
    confidence_score: float = Field()
    summary: str = ""
    suggested_reply: str = ""
    deadline: Optional[str] = None
    meeting_date: Optional[str] = None
    meeting_time: Optional[str] = None

    @field_validator("confidence_score", mode="before")
    @classmethod
    def _clamp_confidence(cls, v: float) -> float:
        value = float(v)
        return max(0.0, min(1.0, value))


# ---------------------------------------------------------------------------
# Email analysis
# ---------------------------------------------------------------------------

class EmailAnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email_id: int
    intent: IntentType
    priority: PriorityLevel
    requires_reply: bool
    requested_action: ActionType
    confidence_score: float
    summary: str
    suggested_reply: str
    deadline: Optional[str] = None
    meeting_date: Optional[str] = None
    meeting_time: Optional[str] = None
    raw_ai_response: Optional[Any] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

class ActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email_id: int
    analysis_id: Optional[int] = None
    action_type: ActionType
    status: ActionStatus
    payload: Optional[Any] = None
    reason: Optional[str] = None
    created_at: datetime
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    execution_result: Optional[Any] = None


class ActionEditRequest(BaseModel):
    """Body for editing a pending action's payload before approval."""
    payload: dict


class ActionRejectRequest(BaseModel):
    """Optional body for rejecting an action with a reason."""
    reason: Optional[str] = None


class ActionDecisionResponse(BaseModel):
    action: ActionOut
    message: str


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    related_email_id: Optional[int] = None
    related_action_id: Optional[int] = None
    message: str
    details: Optional[Any] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action_id: int
    title: str
    description: str
    due_date: Optional[str] = None
    status: str
    created_at: datetime


class TaskDecisionResponse(BaseModel):
    task: TaskOut
    message: str


# ---------------------------------------------------------------------------
# Dashboard metrics
# ---------------------------------------------------------------------------

class DashboardMetrics(BaseModel):
    total_emails: int
    emails_analyzed: int
    pending_actions: int
    approved_actions: int
    executed_actions: int
    escalated_emails: int


class ActivityItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    message: str
    related_email_id: Optional[int] = None
    related_action_id: Optional[int] = None
    created_at: datetime


class DashboardOverview(BaseModel):
    metrics: DashboardMetrics
    analysis_rate: float
    completion_rate: float
    automation_rate: float
    average_confidence: float
    high_priority_emails: int
    open_tasks: int
    intent_distribution: dict[str, int]
    priority_distribution: dict[str, int]
    action_status_distribution: dict[str, int]
    action_type_distribution: dict[str, int]
    recent_activity: list[ActivityItem]


class DemoBootstrapResult(BaseModel):
    emails_total: int
    emails_added: int
    emails_analyzed: int
    actions_created: int
    message: str


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    app_name: str
    env: str
    demo_mode: bool
    database_connected: bool
