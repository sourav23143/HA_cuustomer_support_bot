"""
Knowledge base ingestion script.

Loads Markdown documents, chunks them, generates embeddings,
and upserts to Qdrant.

Usage:
    python scripts/ingest_knowledge.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings
from app.rag.ingestion import ingest_documents


def main():
    settings = get_settings()
    knowledge_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "knowledge",
    )

    print("=" * 60)
    print("  Ingesting Knowledge Base into Qdrant")
    print(f"  Knowledge dir: {knowledge_dir}")
    print(f"  Qdrant URL:    {settings.QDRANT_URL}")
    print(f"  Collection:    {settings.QDRANT_COLLECTION}")
    print(f"  Model:         {settings.EMBEDDING_MODEL}")
    print("=" * 60)

    stats = ingest_documents(knowledge_dir, settings)

    print()
    print(f"  [OK] Documents loaded:  {stats['documents_loaded']}")
    print(f"  [OK] Total chunks:      {stats['total_chunks']}")
    print(f"  [OK] Collection:        {stats['collection']}")
    print("=" * 60)
    print("  Ingestion complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
