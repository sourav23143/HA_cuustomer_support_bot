"""
Read-only tool: get payment data from MongoDB.
"""

import structlog
from app.config import Settings
from app.db.mongodb import get_database

logger = structlog.get_logger(__name__)


async def get_payment_status(
    consultation_id: str, settings: Settings
) -> dict | None:
    """Retrieve payment for a consultation."""
    db = get_database(settings)
    payment = await db["payments"].find_one({"consultation_id": consultation_id})

    if payment:
        result = {
            "payment_id": payment["_id"],
            "patient_id": payment["patient_id"],
            "consultation_id": payment["consultation_id"],
            "amount": payment.get("amount"),
            "currency": payment.get("currency", "INR"),
            "status": payment["status"],
            "payment_method": payment.get("payment_method"),
            "created_at": str(payment.get("created_at", "")),
        }
        logger.info(
            "payment_retrieved",
            payment_id=payment["_id"],
            status=payment["status"],
        )
        return result

    logger.info("no_payment_found", consultation_id=consultation_id)
    return None


async def get_payments_for_user(
    user_id: str, settings: Settings, limit: int = 5
) -> list[dict]:
    """Retrieve recent payments for a user."""
    db = get_database(settings)
    cursor = db["payments"].find(
        {"patient_id": user_id}
    ).sort("created_at", -1).limit(limit)

    payments = []
    async for payment in cursor:
        payments.append({
            "payment_id": payment["_id"],
            "consultation_id": payment["consultation_id"],
            "amount": payment.get("amount"),
            "status": payment["status"],
            "created_at": str(payment.get("created_at", "")),
        })

    logger.info("user_payments_retrieved", user_id=user_id, count=len(payments))
    return payments
