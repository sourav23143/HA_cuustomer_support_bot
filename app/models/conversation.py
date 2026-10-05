"""
Support conversation and message Pydantic models.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SupportConversation(BaseModel):
    """A support conversation session."""

    id: str = Field(..., alias="_id", description="Conversation ID (e.g., CONV-1001)")
    user_id: str
    status: str = Field(
        default="active",
        description="active | resolved | escalated | closed",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_intent: Optional[str] = None

    model_config = {"populate_by_name": True}


class SupportMessage(BaseModel):
    """A single message in a support conversation."""

    id: str = Field(..., alias="_id", description="Message ID (e.g., MSG-uuid)")
    conversation_id: str
    role: str = Field(description="user | assistant | system")
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}
