"""
User activity Pydantic model.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserActivity(BaseModel):
    """A user activity event on the platform."""

    id: str = Field(..., alias="_id", description="Activity ID (e.g., A1001)")
    user_id: str
    activity_type: str = Field(
        description=(
            "doctor_not_joined | payment_completed | payment_failed | "
            "consultation_joined | consultation_cancelled | login_attempt | "
            "profile_updated | support_contacted"
        ),
    )
    consultation_id: Optional[str] = None
    description: str = Field(default="")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}
