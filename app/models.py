"""
Database models.

Traceability is the core requirement of this system:
Email -> AI analysis -> proposed action -> approval -> execution -> audit log

Every table below maps directly onto one stage of that chain.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class IntentType(str, enum.Enum):
    MEETING_REQUEST = "meeting_request"
    INVOICE_PAYMENT = "invoice_payment"
    CUSTOMER_COMPLAINT = "customer_complaint"
    JOB_RECRUITMENT = "job_recruitment"
    PROJECT_UPDATE = "project_update"
    DEADLINE_REMINDER = "deadline_reminder"
    GENERAL_INFORMATION = "general_information"
    SPAM_OR_IGNORE = "spam_or_ignore"
    UNKNOWN = "unknown"


class PriorityLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ActionType(str, enum.Enum):
    CREATE_GMAIL_DRAFT = "CREATE_GMAIL_DRAFT"
    CREATE_CALENDAR_EVENT = "CREATE_CALENDAR_EVENT"
    CREATE_TASK = "CREATE_TASK"
    ESCALATE = "ESCALATE"
    IGNORE = "IGNORE"


class ActionStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"
    EXECUTED = "executed"
    FAILED = "failed"
    ESCALATED = "escalated"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Email(Base):
    """An email synced from Gmail (or seeded demo data)."""

    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)

    # Gmail's message ID. Used to prevent duplicate imports.
    gmail_message_id = Column(String(128), unique=True, index=True, nullable=False)

    sender = Column(String(255), nullable=False)
    subject = Column(String(512), nullable=False, default="")
    body = Column(Text, nullable=False, default="")

    received_at = Column(DateTime, nullable=True)
    synced_at = Column(DateTime, default=datetime.utcnow)

    is_demo = Column(Boolean, default=False)

    analysis = relationship(
        "EmailAnalysis", back_populates="email", uselist=False, cascade="all, delete-orphan"
    )
    actions = relationship("Action", back_populates="email", cascade="all, delete-orphan")


class EmailAnalysis(Base):
    """Structured AI output for a single email."""

    __tablename__ = "email_analysis"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"), unique=True, nullable=False)

    intent = Column(SAEnum(IntentType), nullable=False, default=IntentType.UNKNOWN)
    priority = Column(SAEnum(PriorityLevel), nullable=False, default=PriorityLevel.LOW)

    requires_reply = Column(Boolean, default=False)
    requested_action = Column(SAEnum(ActionType), nullable=False, default=ActionType.IGNORE)

    confidence_score = Column(Float, nullable=False, default=0.0)
    summary = Column(Text, default="")
    suggested_reply = Column(Text, default="")

    deadline = Column(String(64), nullable=True)       # ISO date string, e.g. "2026-06-20"
    meeting_date = Column(String(64), nullable=True)    # ISO date string
    meeting_time = Column(String(64), nullable=True)    # e.g. "3:00 PM"

    # Full raw AI response, kept for debugging / "show raw AI decision" requirement.
    raw_ai_response = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    email = relationship("Email", back_populates="analysis")


class Action(Base):
    """A proposed (and eventually approved/executed) workflow action."""

    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False)
    analysis_id = Column(Integer, ForeignKey("email_analysis.id"), nullable=True)

    action_type = Column(SAEnum(ActionType), nullable=False)
    status = Column(SAEnum(ActionStatus), nullable=False, default=ActionStatus.PENDING)

    # Flexible payload, e.g. {"reply_text": "...", "to": "...", "subject": "..."}
    # or {"summary": "...", "start_time": "...", "end_time": "...", "attendees": [...]}
    payload = Column(JSON, nullable=True)

    # Free-text reason, mainly used for ESCALATE actions.
    reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)

    # Result returned by the execution service, e.g. {"draft_id": "...", "event_link": "..."}
    execution_result = Column(JSON, nullable=True)

    email = relationship("Email", back_populates="actions")
    task = relationship("Task", back_populates="action", uselist=False, cascade="all, delete-orphan")


class AuditLog(Base):
    """Append-only log of every meaningful system event."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    event_type = Column(String(64), nullable=False)
    # e.g. "email_synced", "email_analyzed", "action_proposed",
    #      "action_approved", "action_rejected", "action_executed",
    #      "action_failed", "execution_error"

    related_email_id = Column(Integer, ForeignKey("emails.id"), nullable=True)
    related_action_id = Column(Integer, ForeignKey("actions.id"), nullable=True)

    message = Column(Text, nullable=False, default="")
    details = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class Task(Base):
    """Internal task record created by a CREATE_TASK action."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(Integer, ForeignKey("actions.id"), unique=True, nullable=False)

    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    due_date = Column(String(64), nullable=True)
    status = Column(String(32), default="open")  # open | done

    created_at = Column(DateTime, default=datetime.utcnow)

    action = relationship("Action", back_populates="task")
