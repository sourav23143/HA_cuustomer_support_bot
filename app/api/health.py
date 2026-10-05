"""
Health check and demo API endpoints.
"""

from fastapi import APIRouter
import structlog

from app.config import get_settings
from app.db.mongodb import check_mongodb_health, get_database
from app.db.qdrant import check_qdrant_health

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Health check endpoint — verifies MongoDB and Qdrant connectivity."""
    settings = get_settings()

    mongo_ok = await check_mongodb_health(settings)
    qdrant_ok = await check_qdrant_health(settings)

    status = "ok" if (mongo_ok and qdrant_ok) else "degraded"

    return {
        "status": status,
        "mongodb": "connected" if mongo_ok else "unavailable",
        "qdrant": "connected" if qdrant_ok else "unavailable",
    }


# ── Demo endpoints ─────────────────────────────────────────

demo_router = APIRouter(prefix="/api/demo", tags=["demo"])


@demo_router.get("/users")
async def list_demo_users():
    """List all demo users (patients)."""
    settings = get_settings()
    db = get_database(settings)

    users = []
    async for user in db["users"].find({"role": "patient"}).sort("_id", 1):
        # Get latest consultation for this user
        consultation = await db["consultations"].find_one(
            {"patient_id": user["_id"]},
            sort=[("scheduled_at", -1)],
        )

        users.append({
            "user_id": user["_id"],
            "name": user["name"],
            "role": user["role"],
            "city": user.get("city", ""),
            "language": user.get("language", ""),
            "has_consultation": consultation is not None,
            "consultation_status": consultation["status"] if consultation else None,
        })

    return {"users": users}


@demo_router.get("/users/{user_id}")
async def get_demo_user(user_id: str):
    """Get detailed demo user info with consultation and payment."""
    settings = get_settings()
    db = get_database(settings)

    user = await db["users"].find_one({"_id": user_id})
    if not user:
        return {"error": "User not found"}

    # Get latest consultation
    consultation = await db["consultations"].find_one(
        {"patient_id": user_id},
        sort=[("scheduled_at", -1)],
    )

    payment = None
    doctor = None
    if consultation:
        payment = await db["payments"].find_one(
            {"consultation_id": consultation["_id"]}
        )
        doctor = await db["doctors"].find_one(
            {"_id": consultation["doctor_id"]}
        )

    return {
        "user": {
            "user_id": user["_id"],
            "name": user["name"],
            "role": user["role"],
            "city": user.get("city"),
            "language": user.get("language"),
            "email": user.get("email"),
        },
        "consultation": {
            "consultation_id": consultation["_id"],
            "status": consultation["status"],
            "doctor_joined": consultation.get("doctor_joined"),
            "patient_joined": consultation.get("patient_joined"),
            "scheduled_at": str(consultation.get("scheduled_at")),
        } if consultation else None,
        "payment": {
            "payment_id": payment["_id"],
            "amount": payment.get("amount"),
            "status": payment["status"],
            "currency": payment.get("currency", "INR"),
        } if payment else None,
        "doctor": {
            "doctor_id": doctor["_id"],
            "name": doctor["name"],
            "specialization": doctor.get("specialization"),
        } if doctor else None,
    }
