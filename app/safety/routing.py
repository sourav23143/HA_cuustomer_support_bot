"""
Clinical safety routing.

Routes emergency signals and medical advice requests
through appropriate safety pathways.
"""

import structlog

from app.classification.schemas import IntentResult

logger = structlog.get_logger(__name__)

# Intents requiring safety routing
EMERGENCY_INTENTS = {"emergency_signal"}
MEDICAL_INTENTS = {"medical_advice", "potential_adverse_event"}


class SafetyRouter:
    """Routes safety-critical intents through appropriate pathways."""

    @staticmethod
    def classify(intent_result: IntentResult) -> str:
        """
        Classify the safety level of an intent.

        Returns:
            "emergency" — immediate emergency routing
            "medical_advice" — medical refusal pathway
            "adverse_event" — adverse event escalation
            "safe" — normal support flow
        """
        intent = intent_result.primary_intent

        if intent in EMERGENCY_INTENTS:
            logger.warning("safety_emergency_detected", intent=intent)
            return "emergency"

        if intent == "potential_adverse_event":
            logger.warning("safety_adverse_event_detected", intent=intent)
            return "adverse_event"

        if intent == "medical_advice":
            logger.info("safety_medical_advice_detected", intent=intent)
            return "medical_advice"

        return "safe"
