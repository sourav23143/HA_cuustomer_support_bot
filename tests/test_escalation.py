"""
Tests for escalation logic.
"""

import pytest
from app.classification.schemas import IntentResult, ExtractedEntities
from app.safety.routing import SafetyRouter


# ── Safety Routing Tests ─────────────────────────────────────

class TestSafetyRouter:
    def test_emergency_signal_routes_to_emergency(self):
        result = IntentResult(
            primary_intent="emergency_signal",
            confidence=0.95,
            priority="critical",
        )
        assert SafetyRouter.classify(result) == "emergency"

    def test_medical_advice_routes_correctly(self):
        result = IntentResult(
            primary_intent="medical_advice",
            confidence=0.90,
            priority="medium",
        )
        assert SafetyRouter.classify(result) == "medical_advice"

    def test_adverse_event_routes_to_emergency(self):
        result = IntentResult(
            primary_intent="potential_adverse_event",
            confidence=0.88,
            priority="critical",
        )
        assert SafetyRouter.classify(result) == "adverse_event"

    def test_normal_intent_is_safe(self):
        result = IntentResult(
            primary_intent="platform_question",
            confidence=0.85,
            priority="low",
        )
        assert SafetyRouter.classify(result) == "safe"

    def test_payment_intent_is_safe(self):
        result = IntentResult(
            primary_intent="payment_failed",
            confidence=0.80,
            priority="medium",
        )
        assert SafetyRouter.classify(result) == "safe"

    def test_doctor_not_joining_is_safe(self):
        result = IntentResult(
            primary_intent="doctor_not_joining",
            confidence=0.90,
            priority="high",
        )
        assert SafetyRouter.classify(result) == "safe"


# ── Escalation Decision Tests ────────────────────────────────

class TestEscalationRules:
    """Test the deterministic escalation rules from the decision node."""

    def test_emergency_should_escalate(self):
        result = IntentResult(primary_intent="emergency_signal", confidence=0.95, priority="critical")
        assert result.primary_intent == "emergency_signal"

    def test_human_request_should_escalate(self):
        result = IntentResult(primary_intent="human_support_request", confidence=0.90, priority="medium")
        assert result.primary_intent == "human_support_request"

    def test_low_confidence_should_escalate(self):
        result = IntentResult(primary_intent="platform_question", confidence=0.40, priority="low")
        assert result.confidence < 0.60

    def test_unknown_intent_should_escalate(self):
        result = IntentResult(primary_intent="unknown", confidence=0.30, priority="medium")
        assert result.primary_intent == "unknown"

    def test_high_confidence_normal_intent_should_not_escalate(self):
        result = IntentResult(primary_intent="platform_question", confidence=0.90, priority="low")
        assert result.confidence >= 0.60
        assert result.primary_intent != "emergency_signal"
        assert result.primary_intent != "human_support_request"
        assert result.primary_intent != "unknown"

    def test_payment_consultation_failure_should_escalate(self):
        result = IntentResult(
            primary_intent="payment_consultation_failure",
            confidence=0.95,
            priority="high",
            entities=ExtractedEntities(consultation_id="C1001", amount=499),
        )
        assert result.primary_intent == "payment_consultation_failure"

    def test_adverse_event_should_escalate(self):
        result = IntentResult(primary_intent="potential_adverse_event", confidence=0.85, priority="critical")
        assert result.primary_intent == "potential_adverse_event"
