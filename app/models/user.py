"""
User and Doctor Pydantic models.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class User(BaseModel):
    """Patient or general user on the platform."""

    id: str = Field(..., alias="_id", description="User ID (e.g., U1001)")
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str = Field(default="patient", description="patient or doctor")
    language: str = Field(default="English")
    city: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}


class Doctor(BaseModel):
    """Doctor on the platform."""

    id: str = Field(..., alias="_id", description="Doctor ID (e.g., D1001)")
    name: str
    specialization: str
    languages: list[str] = Field(default_factory=lambda: ["English"])
    availability: str = Field(
        default="online",
        description="online | offline | busy",
    )
    rating: float = Field(default=4.5)
    experience_years: int = Field(default=5)

    model_config = {"populate_by_name": True}
