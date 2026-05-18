"""
BizMind AI — Pydantic Schemas
All request/response models for the API.
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ─── Auth ────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


# ─── Chat ────────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    images: list[str] = []
    stream: bool = False
    conversation_id: str | None = None
    session_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    intent: str  # rag | lead_capture | general | workflow
    sources: list[str] = []
    similarity_scores: list[float] = []
    conversation_id: str
    hallucination_flagged: bool = False


# ─── RAG / Documents ─────────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    created_at: datetime
    chunk_count: int = 0


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    chunks_stored: int
    message: str = "Document uploaded and indexed successfully."


class RAGResult(BaseModel):
    answer: str
    sources: list[str]
    similarity_scores: list[float]
    from_cache: bool = False


# ─── Leads ───────────────────────────────────────────────────────────────────

class LeadStatus(str):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class LeadCreate(BaseModel):
    name: str
    email: EmailStr | None = None
    company: str | None = None
    need: str | None = None
    status: str = "cold"


class LeadUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    company: str | None = None
    need: str | None = None
    status: str | None = None


class LeadResponse(BaseModel):
    id: str
    user_id: str
    name: str
    email: str | None
    company: str | None
    need: str | None
    status: str
    created_at: datetime
    updated_at: datetime


# ─── Workflows ────────────────────────────────────────────────────────────────

class EmailSummaryRequest(BaseModel):
    text: str = Field(min_length=10)


class EmailSummaryResponse(BaseModel):
    subject: str
    key_points: list[str]
    action_items: list[str]
    priority: str  # low | medium | high | urgent


class LeadNotifyRequest(BaseModel):
    lead_id: str


class LeadNotifyResponse(BaseModel):
    status: str
    timestamp: str
    lead_id: str


class CRMExportResponse(BaseModel):
    status: str
    count: int
    file: str


# ─── Dashboard ───────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_leads: int
    hot_leads: int
    total_conversations: int
    workflows_run: int
    documents_uploaded: int
    avg_similarity_score: float


class ConversationLog(BaseModel):
    id: str
    user_id: str
    created_at: datetime
    message_count: int


class WorkflowLog(BaseModel):
    id: str
    workflow_name: str
    status: str
    duration_ms: int
    created_at: datetime


class AIUsageEntry(BaseModel):
    date: str
    tokens_used: int
    rag_hits: int
    total_queries: int


# ─── Memory ──────────────────────────────────────────────────────────────────

class MemoryEntry(BaseModel):
    key: str
    value: Any


# ─── Agent Internal ──────────────────────────────────────────────────────────

class PlannerResult(BaseModel):
    intent: str  # rag | lead_capture | general | workflow
    workflow_name: str | None = None  # set when intent == "workflow"
    confidence: float = 1.0


class LeadExtraction(BaseModel):
    name: str
    email: str | None = None
    company: str | None = None
    need: str | None = None
    status: str = "cold"  # hot | warm | cold


class ValidatorResult(BaseModel):
    is_faithful: bool
    flagged_claims: list[str] = []
    final_answer: str
