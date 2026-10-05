"""
Centralized configuration for AI Healthcare Customer Support Agent.

All environment variables are loaded here via Pydantic BaseSettings.
No other module should read from os.environ directly.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── MongoDB ──────────────────────────────────────────────
    MONGODB_URI: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection URI",
    )
    MONGODB_DATABASE: str = Field(
        default="ha_customer_support",
        description="MongoDB database name",
    )

    # ── Qdrant ───────────────────────────────────────────────
    QDRANT_URL: str = Field(
        default="http://localhost:6333",
        description="Qdrant server URL",
    )
    QDRANT_API_KEY: str = Field(
        default="",
        description="Qdrant API key (optional for local)",
    )
    QDRANT_COLLECTION: str = Field(
        default="support_knowledge",
        description="Qdrant collection name for knowledge base",
    )

    # ── Groq LLM ─────────────────────────────────────────────
    GROQ_API_KEY: str = Field(
        default="",
        description="Groq API key",
    )
    LLM_MODEL: str = Field(
        default="llama-3.3-70b-versatile",
        description="Groq model identifier",
    )
    LLM_TEMPERATURE: float = Field(
        default=0.1,
        description="LLM temperature for response generation",
    )
    LLM_MAX_TOKENS: int = Field(
        default=1024,
        description="Maximum tokens for LLM response",
    )

    # ── HuggingFace Embeddings ────────────────────────────────
    HUGGINGFACE_API_KEY: str = Field(
        default="",
        description="HuggingFace Inference API key",
    )
    EMBEDDING_MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="HuggingFace embedding model",
    )
    EMBEDDING_DIMENSION: int = Field(
        default=384,
        description="Embedding vector dimension",
    )

    # ── Agent Thresholds ──────────────────────────────────────
    INTENT_CONFIDENCE_THRESHOLD: float = Field(
        default=0.60,
        description="Minimum confidence to trust intent classification",
    )
    RAG_RELEVANCE_THRESHOLD: float = Field(
        default=0.45,
        description="Minimum similarity score for RAG results",
    )
    RAG_TOP_K: int = Field(
        default=5,
        description="Number of top RAG results to retrieve",
    )

    # ── Application ───────────────────────────────────────────
    APP_HOST: str = Field(default="0.0.0.0", description="API host")
    APP_PORT: int = Field(default=8000, description="API port")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    ENVIRONMENT: str = Field(default="development", description="Environment name")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
