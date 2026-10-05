"""
Intent classification schemas and enums.
"""

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class IntentCategory(str, Enum):
    """Top-level intent categories."""
    CONSULTATION = "consultation"
    PAYMENT = "payment"
    ACCOUNT = "account"
    GENERAL = "general"
    SAFETY = "safety"
    OTHER = "other"


# Full intent taxonomy
INTENT_TAXONOMY = {
    # Consultation
    "doctor_not_joining": IntentCategory.CONSULTATION,
    "consultation_failed": IntentCategory.CONSULTATION,
    "consultation_cancelled": IntentCategory.CONSULTATION,
    "call_problem": IntentCategory.CONSULTATION,
    "doctor_replacement": IntentCategory.CONSULTATION,
    # Payment
    "payment_failed": IntentCategory.PAYMENT,
    "payment_pending": IntentCategory.PAYMENT,
    "payment_success": IntentCategory.PAYMENT,
    "refund_request": IntentCategory.PAYMENT,
    "refund_status": IntentCategory.PAYMENT,
    "payment_consultation_failure": IntentCategory.PAYMENT,
    # Account
    "login_problem": IntentCategory.ACCOUNT,
    "otp_problem": IntentCategory.ACCOUNT,
    "profile_problem": IntentCategory.ACCOUNT,
    # General
    "platform_question": IntentCategory.GENERAL,
    "pricing_question": IntentCategory.GENERAL,
    "policy_question": IntentCategory.GENERAL,
    # Safety / Clinical
    "medical_advice": IntentCategory.SAFETY,
    "emergency_signal": IntentCategory.SAFETY,
    "potential_adverse_event": IntentCategory.SAFETY,
    # Other
    "human_support_request": IntentCategory.OTHER,
    "unknown": IntentCategory.OTHER,
}

ALL_INTENTS = list(INTENT_TAXONOMY.keys())


class ExtractedEntities(BaseModel):
    """Entities extracted from user message."""

    consultation_id: Optional[str] = Field(default=None, description="Consultation ID if mentioned")
    payment_id: Optional[str] = Field(default=None, description="Payment ID if mentioned")
    doctor_id: Optional[str] = Field(default=None, description="Doctor ID if mentioned")
    amount: Optional[float] = Field(default=None, description="Monetary amount if mentioned")
    doctor_name: Optional[str] = Field(default=None, description="Doctor name if mentioned")
    date: Optional[str] = Field(default=None, description="Date/time if mentioned")
    error_message: Optional[str] = Field(default=None, description="Error message if described")
    issue_description: Optional[str] = Field(default=None, description="Brief description of the issue")


class IntentResult(BaseModel):
    """Result of intent classification and entity extraction."""

    primary_intent: str = Field(description="Primary intent from taxonomy")
    secondary_intents: list[str] = Field(default_factory=list, description="Additional intents")
    confidence: float = Field(ge=0.0, le=1.0, description="Classification confidence")
    entities: ExtractedEntities = Field(default_factory=ExtractedEntities)
    priority: str = Field(default="medium", description="low | medium | high | critical")

    @property
    def category(self) -> str:
        """Get the intent category."""
        return INTENT_TAXONOMY.get(self.primary_intent, IntentCategory.OTHER).value
