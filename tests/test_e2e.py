"""
Tests for the LangGraph agent orchestrator.
"""

import pytest
from app.agent.orchestrator import safety_router, escalation_router
from app.agent.state import AgentState
from app.classification.schemas import IntentResult


class TestSafetyRouterEdge:
    def test_emergency_routes_to_emergency(self):
        state = {"safety_classification": "emergency"}
        assert safety_router(state) == "handle_emergency"

    def test_medical_advice_routes_correctly(self):
        state = {"safety_classification": "medical_advice"}
        assert safety_router(state) == "handle_medical_advice"

    def test_adverse_event_routes_to_emergency(self):
        state = {"safety_classification": "adverse_event"}
        assert safety_router(state) == "handle_emergency"

    def test_safe_routes_to_context(self):
        state = {"safety_classification": "safe"}
        assert safety_router(state) == "build_context"

    def test_missing_classification_defaults_safe(self):
        state = {}
        assert safety_router(state) == "build_context"


class TestEscalationRouterEdge:
    def test_escalation_true_routes_to_escalate(self):
        state = {"should_escalate": True}
        assert escalation_router(state) == "escalate"

    def test_escalation_false_routes_to_store(self):
        state = {"should_escalate": False}
        assert escalation_router(state) == "store_message"

    def test_missing_escalation_routes_to_store(self):
        state = {}
        assert escalation_router(state) == "store_message"
