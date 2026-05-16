"""
BizMind AI — RAG Query Pipeline
1. Check Redis cache (MD5 hash)
2. Embed query with Gemini text-embedding-004
3. pgvector cosine similarity search (top 5)
4. Confidence gate (similarity < 0.35 → "no info" response)
5. Build context, call Gemini 2.0 Flash
6. Cache result, return answer + sources + scores
"""
from dataclasses import dataclass, field

from google import genai
from google.genai import types

from backend.core.config import get_settings
from backend.core.errors import retry, LLM_FALLBACK
from backend.core.logging import get_logger
from backend.core.supabase import get_supabase_admin
from backend.rag.cache import cache_get, cache_set

logger = get_logger("rag_pipeline")

NO_INFO_RESPONSE = (
    "I don't have information on this in the uploaded documents. "
    "Please upload relevant documents or rephrase your question."
)

RAG_SYSTEM_PROMPT = """You are BizMind AI, a precise document analyst.
Answer the user's question using ONLY the provided context excerpts.
Rules:
1. Base your answer strictly on the context below. Do not add external knowledge.
2. Cite sources by mentioning the document name (e.g., "[Source: filename.pdf]").
3. If the context does not contain enough information, say so clearly.
4. Be concise and structured. Use bullet points for lists.
5. Never fabricate facts, numbers, or names not present in the context.
"""


@dataclass
class RAGResult:
    answer: str
    sources: list[str] = field(default_factory=list)
    similarity_scores: list[float] = field(default_factory=list)
    from_cache: bool = False


@retry(max_attempts=3, base_delay=1.0)
async def _embed_query(query: str) -> list[float]:
    """Embed a user query for similarity search."""
    settings = get_settings()
    client = genai.Client(api_key=settings.google_api_key)
    result = client.models.embed_content(
        model=settings.embedding_model,
        contents=query,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )
    return result.embeddings[0].values


async def _vector_search(embedding: list[float], user_id: str, top_k: int = 5) -> list[dict]:
    """pgvector cosine similarity search via Supabase RPC."""
    sb = get_supabase_admin()
    try:
        resp = sb.rpc(
            "match_document_chunks",
            {"query_embedding": embedding, "match_count": top_k, "p_user_id": user_id},
        ).execute()
        return resp.data or []
    except Exception as exc:
        logger.error("Vector search failed", error=str(exc))
        return []


@retry(max_attempts=3, base_delay=1.0)
async def _generate_answer(query: str, context: str) -> str:
    """Generate a grounded answer from context using Gemini."""
    settings = get_settings()
    client = genai.Client(api_key=settings.google_api_key)
    prompt = f"Context:\n{context}\n\nUser question: {query}"
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=RAG_SYSTEM_PROMPT,
            temperature=0.2,
            max_output_tokens=1024,
        ),
    )
    return response.text


async def run_rag_pipeline(query: str, user_id: str) -> RAGResult:
    """Full RAG query pipeline."""
    settings = get_settings()

    cached = await cache_get(query, user_id)
    if cached:
        logger.info("Serving from cache", user_id=user_id)
        return RAGResult(
            answer=cached["answer"],
            sources=cached["sources"],
            similarity_scores=cached["similarity_scores"],
            from_cache=True,
        )

    try:
        query_embedding = await _embed_query(query)
    except Exception as exc:
        logger.error("Query embedding failed", error=str(exc))
        return RAGResult(answer=LLM_FALLBACK)

    chunks = await _vector_search(query_embedding, user_id, settings.rag_top_k)
    if not chunks:
        return RAGResult(answer=NO_INFO_RESPONSE)

    similarities = [c.get("similarity", 0.0) for c in chunks]
    max_sim = max(similarities) if similarities else 0.0
    logger.info("Vector search complete", top_similarity=max_sim, chunks_found=len(chunks))

    if max_sim < settings.rag_similarity_threshold:
        return RAGResult(answer=NO_INFO_RESPONSE)

    context_parts = []
    sources = []
    for i, chunk in enumerate(chunks):
        doc_name = chunk.get("document_filename", f"Document {i+1}")
        content = chunk.get("content", "")
        context_parts.append(f"[{doc_name}]\n{content}")
        if doc_name not in sources:
            sources.append(doc_name)

    context = "\n\n---\n\n".join(context_parts)

    try:
        answer = await _generate_answer(query, context)
    except Exception as exc:
        logger.error("Answer generation failed", error=str(exc))
        return RAGResult(answer=LLM_FALLBACK)

    cache_payload = {"answer": answer, "sources": sources, "similarity_scores": similarities}
    await cache_set(query, user_id, cache_payload)

    return RAGResult(answer=answer, sources=sources, similarity_scores=similarities, from_cache=False)
