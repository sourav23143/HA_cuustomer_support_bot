"""
Shared test fixtures and configuration.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.config import Settings


@pytest.fixture
def settings():
    """Test settings with safe defaults."""
    return Settings(
        MONGODB_URI="mongodb://localhost:27017",
        MONGODB_DATABASE="ha_test",
        QDRANT_URL="http://localhost:6333",
        GROQ_API_KEY="test-key",
        HUGGINGFACE_API_KEY="test-key",
        INTENT_CONFIDENCE_THRESHOLD=0.60,
        RAG_RELEVANCE_THRESHOLD=0.45,
    )


@pytest.fixture
def mock_db():
    """Mock MongoDB database."""
    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=MagicMock())
    return db


@pytest.fixture
def sample_user():
    """Sample user document."""
    return {
        "_id": "U1001",
        "name": "Sourav Kumar",
        "email": "sourav@demo.com",
        "phone": "+91-9876543001",
        "role": "patient",
        "language": "English",
        "city": "Jaipur",
    }


@pytest.fixture
def sample_consultation():
    """Sample consultation document."""
    return {
        "_id": "C1001",
        "patient_id": "U1001",
        "doctor_id": "D1001",
        "status": "failed",
        "patient_joined": True,
        "doctor_joined": False,
        "scheduled_at": "2026-08-30T19:30:00",
    }


@pytest.fixture
def sample_payment():
    """Sample payment document."""
    return {
        "_id": "P1001",
        "patient_id": "U1001",
        "consultation_id": "C1001",
        "amount": 499,
        "currency": "INR",
        "status": "success",
        "payment_method": "UPI",
    }


@pytest.fixture
def sample_activity():
    """Sample user activity."""
    return {
        "_id": "A1001",
        "user_id": "U1001",
        "activity_type": "doctor_not_joined",
        "consultation_id": "C1001",
        "description": "Doctor did not join consultation.",
        "timestamp": "2026-08-30T19:34:00",
    }
