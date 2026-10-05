"""
Consultation Pydantic model.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Consultation(BaseModel):
    """A doctor-patient consultation session."""

    id: str = Field(..., alias="_id", description="Consultation ID (e.g., C1001)")
    patient_id: str
    doctor_id: str
    status: str = Field(
        default="scheduled",
        description="scheduled | in_progress | completed | failed | cancelled",
    )
    patient_joined: bool = Field(default=False)
    doctor_joined: bool = Field(default=False)
    scheduled_at: datetime
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    notes: Optional[str] = None

    model_config = {"populate_by_name": True}
