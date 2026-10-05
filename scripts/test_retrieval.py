import asyncio
from app.config import get_settings
from app.rag.retriever import RAGRetriever

async def test_retrieval():
    settings = get_settings()
    retriever = RAGRetriever(settings)
    
    query = "What is the refund policy for cancelled consultations?"
    results = await retriever.retrieve(query, top_k=5)
    
    print(f"Top {len(results)} chunks for query: '{query}'")
    for i, r in enumerate(results):
        print(f"Chunk {i+1}: Score: {r.score:.4f} | Document: {r.document}")

if __name__ == "__main__":
    asyncio.run(test_retrieval())
