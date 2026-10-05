"""
Qdrant vector database client wrapper.
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from app.config import Settings

import structlog

logger = structlog.get_logger(__name__)

_client: QdrantClient | None = None


def get_qdrant_client(settings: Settings) -> QdrantClient:
    """Get or create the Qdrant client singleton."""
    global _client
    if _client is None:
        _client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
        )
        logger.info("qdrant_client_created", url=settings.QDRANT_URL)
    return _client


async def check_qdrant_health(settings: Settings) -> bool:
    """Check Qdrant connectivity."""
    try:
        client = get_qdrant_client(settings)
        client.get_collections()
        return True
    except Exception as e:
        logger.error("qdrant_health_check_failed", error=str(e))
        return False


def ensure_collection(settings: Settings) -> None:
    """Create the support_knowledge collection if it doesn't exist."""
    client = get_qdrant_client(settings)
    collections = [c.name for c in client.get_collections().collections]

    if settings.QDRANT_COLLECTION not in collections:
        client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=settings.EMBEDDING_DIMENSION,
                distance=Distance.COSINE,
            ),
        )
        logger.info(
            "qdrant_collection_created",
            collection=settings.QDRANT_COLLECTION,
            dimension=settings.EMBEDDING_DIMENSION,
        )
    else:
        logger.info(
            "qdrant_collection_exists",
            collection=settings.QDRANT_COLLECTION,
        )
