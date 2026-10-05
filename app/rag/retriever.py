"""
RAG retriever — searches Qdrant for relevant knowledge chunks using LangChain.
"""

from typing import Optional
from pydantic import BaseModel
import structlog

from qdrant_client.models import Filter, FieldCondition, MatchValue
from langchain_qdrant import QdrantVectorStore

from app.config import Settings
from app.db.qdrant import get_qdrant_client
from app.rag.embeddings import EmbeddingService

logger = structlog.get_logger(__name__)


class RetrievalResult(BaseModel):
    """A single retrieval result from Qdrant."""

    text: str
    score: float
    document: str
    category: str
    audience: str = "patient"
    chunk_index: int = 0


class RAGRetriever:
    """Retrieve relevant knowledge from Qdrant vector store using LangChain."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.embedding_service = EmbeddingService(settings)
        
        # Initialize LangChain QdrantVectorStore
        self.vector_store = QdrantVectorStore(
            client=get_qdrant_client(settings),
            collection_name=settings.QDRANT_COLLECTION,
            embedding=self.embedding_service.embeddings,
        )

    async def retrieve(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> list[RetrievalResult]:
        """
        Search Qdrant for relevant knowledge chunks.

        Args:
            query: The search query text.
            category: Optional category filter (consultation, payment, etc.)
            top_k: Number of results to return.

        Returns:
            List of RetrievalResult with text, score, and metadata.
        """
        k = top_k or self.settings.RAG_TOP_K

        try:
            # Build Qdrant filter (langchain-qdrant supports raw Qdrant Filter objects)
            search_filter = None
            if category:
                search_filter = Filter(
                    must=[
                        FieldCondition(
                            key="metadata.category",
                            match=MatchValue(value=category),
                        ),
                        FieldCondition(
                            key="metadata.status",
                            match=MatchValue(value="active"),
                        ),
                    ]
                )

            # Note: similarity_search_with_score is synchronous in LangChain QdrantVectorStore
            # Using it directly here since Qdrant is local and fast, but could be wrapped in asyncio.to_thread if needed.
            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=k,
                filter=search_filter,
            )

            retrieval_results = []
            for doc, score in results:
                # Qdrant returns cosine distance or similar, depending on configuration
                # LangChain similarity_search_with_score returns (Document, score)
                retrieval_results.append(
                    RetrievalResult(
                        text=doc.page_content,
                        score=score,
                        document=doc.metadata.get("document", "unknown"),
                        category=doc.metadata.get("category", "general"),
                        audience=doc.metadata.get("audience", "patient"),
                        chunk_index=doc.metadata.get("chunk_index", 0),
                    )
                )

            logger.info(
                "langchain_rag_retrieval_complete",
                query_length=len(query),
                results=len(retrieval_results),
                top_score=retrieval_results[0].score if retrieval_results else 0,
                category_filter=category,
            )

            return retrieval_results

        except Exception as e:
            logger.error("langchain_rag_retrieval_error", error=str(e))
            return []

    def format_results_for_prompt(
        self, results: list[RetrievalResult], threshold: float | None = None
    ) -> str:
        """Format retrieval results as text for the LLM prompt."""
        min_score = threshold or self.settings.RAG_RELEVANCE_THRESHOLD
        relevant = [r for r in results if r.score >= min_score]

        if not relevant:
            return "No relevant documentation found."

        sections = []
        for i, r in enumerate(relevant, 1):
            sections.append(
                f"[Source: {r.document} | Category: {r.category} | Relevance: {r.score:.2f}]\n{r.text}"
            )

        return "\n\n---\n\n".join(sections)
