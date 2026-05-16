"""
BizMind AI — RAG / Documents API
POST /upload, GET /documents, DELETE /documents/{id}
"""
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile

from backend.api.auth import get_current_user
from backend.core.logging import get_logger
from backend.core.supabase import get_supabase_admin
from backend.models.schemas import DocumentResponse, UploadResponse
from backend.rag.ingestion import ingest_document

router = APIRouter()
logger = get_logger("rag")

ALLOWED_CONTENT_TYPES = {"application/pdf", "text/plain", "text/csv"}


@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Upload a PDF or TXT file, chunk it, embed it, and store in pgvector."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {file.content_type}. Allowed: PDF, TXT.",
        )

    content = await file.read()
    if len(content) > 20 * 1024 * 1024:  # 20 MB cap
        raise HTTPException(status_code=413, detail="File too large (max 20 MB).")

    doc_id = str(uuid.uuid4())
    chunks_stored = await ingest_document(
        content=content,
        filename=file.filename or "unknown",
        content_type=file.content_type or "text/plain",
        document_id=doc_id,
        user_id=user["id"],
    )

    logger.info(
        "Document ingested",
        document_id=doc_id,
        filename=file.filename,
        chunks=chunks_stored,
        user_id=user["id"],
    )
    return UploadResponse(
        document_id=doc_id,
        filename=file.filename or "unknown",
        chunks_stored=chunks_stored,
    )


@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents(user: dict = Depends(get_current_user)):
    """List all uploaded documents for the user."""
    sb = get_supabase_admin()
    docs = (
        sb.table("documents")
        .select("id, user_id, filename, created_at")
        .eq("user_id", user["id"])
        .order("created_at", desc=True)
        .execute()
    )
    result = []
    for doc in docs.data or []:
        chunks = (
            sb.table("document_chunks")
            .select("id", count="exact")
            .eq("document_id", doc["id"])
            .execute()
        )
        chunk_count = chunks.count or 0
        result.append(DocumentResponse(**doc, chunk_count=chunk_count))
    return result


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    user: dict = Depends(get_current_user),
):
    """Delete a document and its chunks."""
    sb = get_supabase_admin()
    # Verify ownership
    doc = (
        sb.table("documents")
        .select("id")
        .eq("id", document_id)
        .eq("user_id", user["id"])
        .execute()
    )
    if not doc.data:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Delete chunks first (FK cascade should handle it, but explicit is safer)
    sb.table("document_chunks").delete().eq("document_id", document_id).execute()
    sb.table("documents").delete().eq("id", document_id).execute()

    logger.info("Document deleted", document_id=document_id, user_id=user["id"])
