"""
MongoDB connection manager.

Provides async MongoDB client via Motor and collection accessors.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import Settings

import structlog

logger = structlog.get_logger(__name__)

# Module-level client singleton
_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None


def get_mongo_client(settings: Settings) -> AsyncIOMotorClient:
    """Get or create the MongoDB client singleton."""
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGODB_URI)
        logger.info("mongodb_client_created", uri=settings.MONGODB_URI.split("@")[-1])
    return _client


def get_database(settings: Settings) -> AsyncIOMotorDatabase:
    """Get the application database."""
    global _database
    if _database is None:
        client = get_mongo_client(settings)
        _database = client[settings.MONGODB_DATABASE]
        logger.info("mongodb_database_selected", database=settings.MONGODB_DATABASE)
    return _database


async def check_mongodb_health(settings: Settings) -> bool:
    """Check MongoDB connectivity."""
    try:
        client = get_mongo_client(settings)
        await client.admin.command("ping")
        return True
    except Exception as e:
        logger.error("mongodb_health_check_failed", error=str(e))
        return False


async def close_mongo_client():
    """Close the MongoDB client connection."""
    global _client, _database
    if _client is not None:
        _client.close()
        _client = None
        _database = None
        logger.info("mongodb_client_closed")


# ── Collection Accessors ─────────────────────────────────────

def get_users_collection(settings: Settings):
    """Get the users collection."""
    return get_database(settings)["users"]


def get_doctors_collection(settings: Settings):
    """Get the doctors collection."""
    return get_database(settings)["doctors"]


def get_consultations_collection(settings: Settings):
    """Get the consultations collection."""
    return get_database(settings)["consultations"]


def get_payments_collection(settings: Settings):
    """Get the payments collection."""
    return get_database(settings)["payments"]


def get_user_activity_collection(settings: Settings):
    """Get the user_activity collection."""
    return get_database(settings)["user_activity"]


def get_support_conversations_collection(settings: Settings):
    """Get the support_conversations collection."""
    return get_database(settings)["support_conversations"]


def get_support_messages_collection(settings: Settings):
    """Get the support_messages collection."""
    return get_database(settings)["support_messages"]


def get_support_tickets_collection(settings: Settings):
    """Get the support_tickets collection."""
    return get_database(settings)["support_tickets"]
