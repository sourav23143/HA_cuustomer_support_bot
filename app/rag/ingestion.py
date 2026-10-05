"""
Document ingestion pipeline using LangChain.

Loads Markdown → Cleans → Chunks → Embeds → Upserts to Qdrant.
"""

import os
import re
import structlog

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore

from app.config import Settings
from app.db.qdrant import get_qdrant_client, ensure_collection
from app.rag.embeddings import EmbeddingService

logger = structlog.get_logger(__name__)

# Mapping from directory name to category
CATEGORY_MAP = {
    "consultation": "consultation",
    "payments": "payment",
    "account": "account",
    "general": "general",
    "safety": "safety",
}


def clean_document_text(text: str) -> str:
    """Clean markdown text for embedding."""
    # Remove the demo disclaimer lines
    text = re.sub(r"\*This document is fictional.*?\*\n*", "", text)
    # Collapse excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def ingest_documents(
    knowledge_dir: str,
    settings: Settings,
) -> dict:
    """
    Full LangChain ingestion pipeline: load → chunk → embed → upsert to Qdrant.

    Returns ingestion statistics.
    """
    # 1. Load documents using LangChain DirectoryLoader
    loader = DirectoryLoader(
        knowledge_dir,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    docs = loader.load()

    # 2. Process metadata and clean text
    for doc in docs:
        source_file = doc.metadata.get("source", "")
        # Extract folder name for category mapping
        parent_dir = os.path.basename(os.path.dirname(source_file))
        category = CATEGORY_MAP.get(parent_dir, "general")
        doc_name = os.path.basename(source_file).replace(".md", "")

        doc.page_content = clean_document_text(doc.page_content)

        # Inject our standard metadata schema
        doc.metadata.update({
            "document": doc_name,
            "category": category,
            "audience": "patient",
            "version": "1.0",
            "status": "active",
        })

    logger.info("langchain_documents_loaded", count=len(docs))

    # 3. Split documents using LangChain RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks = text_splitter.split_documents(docs)

    # Add chunk_index metadata
    for idx, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = idx

    logger.info("langchain_chunks_prepared", total_chunks=len(chunks))

    # 4. Prepare Qdrant Collection (recreate to avoid duplicates)
    client = get_qdrant_client(settings)
    try:
        client.delete_collection(settings.QDRANT_COLLECTION)
        logger.info("qdrant_collection_deleted", collection=settings.QDRANT_COLLECTION)
    except Exception:
        pass
    ensure_collection(settings)

    # 5. Embed and Upsert using LangChain QdrantVectorStore
    embedding_service = EmbeddingService(settings)

    QdrantVectorStore.from_documents(
        chunks,
        embedding_service.embeddings,
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
        collection_name=settings.QDRANT_COLLECTION,
        prefer_grpc=False,
    )

    stats = {
        "documents_loaded": len(docs),
        "total_chunks": len(chunks),
        "collection": settings.QDRANT_COLLECTION,
    }

    logger.info("langchain_ingestion_complete", **stats)
    return stats
