"""
BizMind AI — Document Ingestion Pipeline
PDF/TXT → extract → chunk → embed → store in Supabase pgvector
Uses local HuggingFace SentenceTransformer for embeddings.
"""
import io
import re
import uuid
from datetime import datetime, timezone

import tiktoken

from backend.core.config import get_settings
from backend.core.embedder import embed_text
from backend.core.errors import retry
from backend.core.logging import get_logger
from backend.core.supabase import get_supabase_admin

logger = get_logger("ingestion")
_enc = tiktoken.get_encoding("cl100k_base")


def _count_tokens(text: str) -> int:
    return len(_enc.encode(text))


def _extract_text(content: bytes, content_type: str) -> str:
    if "pdf" in content_type:
        try:
            import fitz
            doc = fitz.open(stream=content, filetype="pdf")
            pages = [page.get_text() for page in doc]
            doc.close()
            return "\n\n".join(pages)
        except Exception as exc:
            raise ValueError(f"Failed to extract PDF text: {exc}")
    else:
        try:
            return content.decode("utf-8", errors="replace")
        except Exception as exc:
            raise ValueError(f"Failed to decode text file: {exc}")


def _chunk_text(text: str, chunk_size: int = 600, overlap: int = 100) -> list[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks: list[str] = []
    current_tokens: list[str] = []
    current_count = 0

    for sentence in sentences:
        sent_tokens = _enc.encode(sentence)
        sent_count = len(sent_tokens)

        if current_count + sent_count > chunk_size and current_tokens:
            chunks.append(_enc.decode(current_tokens))
            overlap_tokens = current_tokens[-overlap:] if len(current_tokens) > overlap else current_tokens[:]
            current_tokens = list(overlap_tokens)
            current_count = len(current_tokens)

        current_tokens.extend(sent_tokens)
        current_count += sent_count

    if current_tokens:
        chunks.append(_enc.decode(current_tokens))

    return [c for c in chunks if len(c.strip()) > 50]


@retry(max_attempts=3, base_delay=1.0)
async def _embed_chunk(text: str) -> list[float]:
    """Embed a single chunk using local HuggingFace model."""
    return embed_text(text)


async def ingest_document(
    content: bytes,
    filename: str,
    content_type: str,
    document_id: str,
    user_id: str,
) -> int:
    settings = get_settings()
    sb = get_supabase_admin()

    text = _extract_text(content, content_type)
    if not text.strip():
        raise ValueError("Document appears to be empty after text extraction.")

    logger.info("Text extracted", filename=filename, chars=len(text))

    now = datetime.now(timezone.utc).isoformat()
    sb.table("documents").insert(
        {
            "id": document_id,
            "user_id": user_id,
            "filename": filename,
            "content": text[:5000],
            "created_at": now,
        }
    ).execute()

    chunks = _chunk_text(text, settings.rag_chunk_size, settings.rag_chunk_overlap)
    logger.info("Chunked document", filename=filename, chunks=len(chunks))

    chunk_rows = []
    for idx, chunk in enumerate(chunks):
        try:
            embedding = await _embed_chunk(chunk)
            chunk_rows.append(
                {
                    "id": str(uuid.uuid4()),
                    "document_id": document_id,
                    "content": chunk,
                    "embedding": embedding,
                    "chunk_index": idx,
                }
            )
        except Exception as exc:
            logger.error("Embedding failed for chunk", chunk_index=idx, error=str(exc))
            continue

    batch_size = 50
    total_stored = 0
    for i in range(0, len(chunk_rows), batch_size):
        batch = chunk_rows[i : i + batch_size]
        resp = sb.table("document_chunks").insert(batch).execute()
        total_stored += len(resp.data or [])

    logger.info("Ingestion complete", document_id=document_id, chunks_stored=total_stored)
    return total_stored
