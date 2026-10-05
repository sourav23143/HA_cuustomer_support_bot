"""
Tests for Pydantic schema validation.
"""

import pytest
from app.classification.schemas import IntentResult, ExtractedEntities, INTENT_TAXONOMY, ALL_INTENTS
from app.models.ticket import TicketCreate, TicketResponse, SupportTicket
from app.models.user import User, Doctor
from app.models.consultation import Consultation
from app.models.payment import Payment
from datetime import datetime


# ── Intent Schema Tests ──────────────────────────────────────

class TestIntentResult:
    def test_valid_intent_result(self):
        result = IntentResult(
            primary_intent="doctor_not_joining",
            secondary_intents=["consultation_failed"],
            confidence=0.92,
            entities=ExtractedEntities(consultation_id="C1001"),
            priority="high",
        )
        assert result.primary_intent == "doctor_not_joining"
        assert result.confidence == 0.92
        assert result.entities.consultation_id == "C1001"
        assert result.category == "consultation"

    def test_intent_with_no_entities(self):
        result = IntentResult(
            primary_intent="platform_question",
            confidence=0.85,
            priority="low",
        )
        assert result.entities.consultation_id is None
        assert result.entities.amount is None

    def test_confidence_bounds(self):
        with pytest.raises(Exception):
            IntentResult(primary_intent="unknown", confidence=1.5, priority="low")

        with pytest.raises(Exception):
            IntentResult(primary_intent="unknown", confidence=-0.1, priority="low")

    def test_all_intents_have_categories(self):
        for intent in ALL_INTENTS:
            assert intent in INTENT_TAXONOMY, f"Intent {intent} missing from taxonomy"


# ── Ticket Schema Tests ─────────────────────────────────────

class TestTicketSchemas:
    def test_valid_ticket_create(self):
        ticket = TicketCreate(
            user_id="U1001",
            conversation_id="CONV-001",
            category="consultation",
            intent="doctor_not_joining",
            priority="high",
            subject="Doctor did not join",
            summary="Patient waited but doctor didn't show.",
            reason_for_escalation="Requires human review",
            consultation_id="C1001",
            idempotency_key="CONV-001:doctor_not_joining",
        )
        assert ticket.user_id == "U1001"
        assert ticket.priority == "high"

    def test_ticket_create_without_optional_fields(self):
        ticket = TicketCreate(
            user_id="U1001",
            conversation_id="CONV-001",
            category="general",
            intent="platform_question",
            subject="General question",
            summary="User had a question",
            reason_for_escalation="Unknown intent",
            idempotency_key="CONV-001:platform_question",
        )
        assert ticket.consultation_id is None
        assert ticket.payment_id is None

    def test_ticket_response(self):
        response = TicketResponse(
            ticket_id="TKT-10001",
            status="open",
            created_at=datetime.utcnow(),
        )
        assert response.ticket_id == "TKT-10001"
        assert response.message == "Ticket created successfully"


# ── Domain Model Tests ───────────────────────────────────────

class TestDomainModels:
    def test_user_model(self):
        user = User(
            _id="U1001",
            name="Sourav Kumar",
            role="patient",
            language="English",
            city="Jaipur",
        )
        assert user.id == "U1001"
        assert user.name == "Sourav Kumar"

    def test_doctor_model(self):
        doctor = Doctor(
            _id="D1001",
            name="Dr. Priya Sharma",
            specialization="General Physician",
            languages=["English", "Hindi"],
            availability="online",
        )
        assert doctor.id == "D1001"
        assert "Hindi" in doctor.languages

    def test_consultation_model(self):
        consult = Consultation(
            _id="C1001",
            patient_id="U1001",
            doctor_id="D1001",
            status="failed",
            patient_joined=True,
            doctor_joined=False,
            scheduled_at=datetime(2026, 8, 30, 19, 30),
        )
        assert consult.status == "failed"
        assert consult.patient_joined is True
        assert consult.doctor_joined is False

    def test_payment_model(self):
        payment = Payment(
            _id="P1001",
            patient_id="U1001",
            consultation_id="C1001",
            amount=499,
            status="success",
        )
        assert payment.amount == 499
        assert payment.currency == "INR"
