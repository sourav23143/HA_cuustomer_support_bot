"""
Read-only tool: get user activity from MongoDB.
"""

import structlog
from app.config import Settings
from app.db.mongodb import get_database

logger = structlog.get_logger(__name__)


async def get_user_activity(
    user_id: str, settings: Settings, limit: int = 10
) -> list[dict]:
    """Retrieve recent activity for a user, sorted by timestamp desc."""
    db = get_database(settings)
    cursor = (
        db["user_activity"]
        .find({"user_id": user_id})
        .sort("timestamp", -1)
        .limit(limit)
    )

    activities = []
    async for activity in cursor:
        activities.append({
            "activity_id": activity["_id"],
            "activity_type": activity["activity_type"],
            "consultation_id": activity.get("consultation_id"),
            "description": activity.get("description", ""),
            "timestamp": str(activity.get("timestamp", "")),
        })

    logger.info("user_activity_retrieved", user_id=user_id, count=len(activities))
    return activities
