"""
Support ticket Pydantic model.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SupportTicket(BaseModel):
    """A support ticket created during escalation."""

    ticket_id: str = Field(..., alias="_id", description="Ticket ID (e.g., TKT-10001)")
    user_id: str
    conversation_id: str
    category: str = Field(description="consultation | payment | account | general | safety")
    intent: str
    priority: str = Field(description="low | medium | high | critical")
    subject: str
    summary: str
    reason_for_escalation: str
    consultation_id: Optional[str] = None
    payment_id: Optional[str] = None
    status: str = Field(default="open", description="open | in_progress | resolved | closed")
    source: str = Field(default="ai_support_agent")
    idempotency_key: str = Field(description="Dedup key: conversation_id + intent")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}


class TicketCreate(BaseModel):
    """Input schema for creating a support ticket."""

    user_id: str
    conversation_id: str
    category: str
    intent: str
    priority: str = Field(default="medium")
    subject: str
    summary: str
    reason_for_escalation: str
    consultation_id: Optional[str] = None
    payment_id: Optional[str] = None
    idempotency_key: str


class TicketResponse(BaseModel):
    """Response after ticket creation."""

    ticket_id: str
    status: str
    created_at: datetime
    message: str = Field(default="Ticket created successfully")
