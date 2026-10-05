"""
Payment Pydantic model.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Payment(BaseModel):
    """Payment for a consultation."""

    id: str = Field(..., alias="_id", description="Payment ID (e.g., P1001)")
    patient_id: str
    consultation_id: str
    amount: float
    currency: str = Field(default="INR")
    status: str = Field(
        default="success",
        description="success | pending | failed | refunded",
    )
    payment_method: str = Field(default="UPI")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}
