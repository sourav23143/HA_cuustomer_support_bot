"""
Read-only tool: get user context from MongoDB.
"""

import structlog
from app.config import Settings
from app.db.mongodb import get_database

logger = structlog.get_logger(__name__)


async def get_user_context(user_id: str, settings: Settings) -> dict | None:
    """
    Retrieve user information from MongoDB.

    Returns user dict or None if not found.
    """
    db = get_database(settings)
    user = await db["users"].find_one({"_id": user_id})

    if user:
        logger.info("user_context_retrieved", user_id=user_id)
        return {
            "user_id": user["_id"],
            "name": user.get("name"),
            "role": user.get("role"),
            "language": user.get("language"),
            "city": user.get("city"),
            "email": user.get("email"),
        }

    logger.warning("user_not_found", user_id=user_id)
    return None
