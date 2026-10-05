"""
Local embedding service using LangChain's HuggingFace integration.

Runs entirely on your PC to bypass network/DNS issues.
Uses sentence-transformers/all-MiniLM-L6-v2 (384 dimensions).
"""

import structlog
from langchain_huggingface import HuggingFaceEmbeddings
from app.config import Settings

logger = structlog.get_logger(__name__)

# Global model singleton to avoid reloading
_embeddings_instance = None


def get_embeddings(model_name: str) -> HuggingFaceEmbeddings:
    """Get or load the LangChain local embedding model."""
    global _embeddings_instance
    if _embeddings_instance is None:
        logger.info("loading_langchain_huggingface_embeddings", model=model_name)
        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},
        )
    return _embeddings_instance


class EmbeddingService:
    """Generate embeddings entirely locally using LangChain."""

    def __init__(self, settings: Settings):
        self.model_name = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        # Load model synchronously during init so it's ready
        self.embeddings = get_embeddings(self.model_name)

    async def embed_text(self, text: str) -> list[float]:
        """Embed a single text string."""
        return self.embed_text_sync(text)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of text strings."""
        return self.embed_texts_sync(texts)

    def embed_text_sync(self, text: str) -> list[float]:
        """Synchronous single-text embedding."""
        embedding = self.embeddings.embed_query(text)
        
        # Validate dimensions
        if len(embedding) != self.dimension:
            raise ValueError(
                f"Expected {self.dimension} dimensions, got {len(embedding)}"
            )
            
        return embedding

    def embed_texts_sync(self, texts: list[str]) -> list[list[float]]:
        """Synchronous batch embedding."""
        embeddings = self.embeddings.embed_documents(texts)
        
        if embeddings and len(embeddings[0]) != self.dimension:
            raise ValueError(
                f"Expected {self.dimension} dimensions, got {len(embeddings[0])}"
            )
            
        logger.info("langchain_embeddings_generated", count=len(texts))
        return embeddings
