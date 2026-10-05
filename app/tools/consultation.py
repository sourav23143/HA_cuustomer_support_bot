"""
Read-only tool: get consultation data from MongoDB.
"""

import structlog
from app.config import Settings
from app.db.mongodb import get_database

logger = structlog.get_logger(__name__)


async def get_active_consultation(user_id: str, settings: Settings) -> dict | None:
    """
    Retrieve the most recent/active consultation for a user.

    Looks for consultations in order of priority:
    in_progress > scheduled > failed (recent) > cancelled (recent).
    """
    db = get_database(settings)

    # Try active consultations first
    for status in ["in_progress", "scheduled", "failed", "cancelled"]:
        consultation = await db["consultations"].find_one(
            {"patient_id": user_id, "status": status},
            sort=[("scheduled_at", -1)],
        )
        if consultation:
            # Also get doctor info
            doctor = await db["doctors"].find_one({"_id": consultation["doctor_id"]})
            doctor_info = {
                "doctor_id": doctor["_id"],
                "name": doctor.get("name"),
                "specialization": doctor.get("specialization"),
                "availability": doctor.get("availability"),
            } if doctor else None

            result = {
                "consultation_id": consultation["_id"],
                "patient_id": consultation["patient_id"],
                "doctor_id": consultation["doctor_id"],
                "status": consultation["status"],
                "patient_joined": consultation.get("patient_joined", False),
                "doctor_joined": consultation.get("doctor_joined", False),
                "scheduled_at": str(consultation.get("scheduled_at", "")),
                "doctor": doctor_info,
            }

            logger.info(
                "consultation_retrieved",
                consultation_id=consultation["_id"],
                status=status,
            )
            return result

    logger.info("no_consultation_found", user_id=user_id)
    return None


async def get_consultation_by_id(
    consultation_id: str, settings: Settings
) -> dict | None:
    """Retrieve a specific consultation by ID."""
    db = get_database(settings)
    consultation = await db["consultations"].find_one({"_id": consultation_id})

    if consultation:
        doctor = await db["doctors"].find_one({"_id": consultation["doctor_id"]})
        doctor_info = {
            "doctor_id": doctor["_id"],
            "name": doctor.get("name"),
            "specialization": doctor.get("specialization"),
        } if doctor else None

        return {
            "consultation_id": consultation["_id"],
            "patient_id": consultation["patient_id"],
            "doctor_id": consultation["doctor_id"],
            "status": consultation["status"],
            "patient_joined": consultation.get("patient_joined", False),
            "doctor_joined": consultation.get("doctor_joined", False),
            "scheduled_at": str(consultation.get("scheduled_at", "")),
            "doctor": doctor_info,
        }

    return None
