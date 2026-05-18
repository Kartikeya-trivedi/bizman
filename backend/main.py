"""
BizMind AI — FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import get_settings
from backend.core.errors import register_error_handlers
from backend.core.logging import get_logger, setup_logging

# ── Import routers ────────────────────────────────────────────────────────────
from backend.api.auth import router as auth_router
from backend.api.chat import router as chat_router
from backend.api.rag import router as rag_router
from backend.api.leads import router as leads_router
from backend.api.workflows import router as workflows_router
from backend.api.dashboard import router as dashboard_router
from backend.api.webhooks import router as webhooks_router

logger = get_logger("main")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown lifecycle."""
    setup_logging()

    # Ensure export and logs directories exist
    Path(settings.exports_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.logs_dir).mkdir(parents=True, exist_ok=True)

    logger.info(
        "BizMind AI starting",
        version=settings.app_version,
        debug=settings.debug,
        gemini_model=settings.gemini_model,
    )
    yield
    logger.info("BizMind AI shutting down")


app = FastAPI(
    title="BizMind AI",
    description="AI Business Assistant Platform for SMEs",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Error Handlers ────────────────────────────────────────────────────────────
register_error_handlers(app)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(rag_router, tags=["RAG"])
app.include_router(leads_router, tags=["Leads"])
app.include_router(workflows_router, prefix="/workflows", tags=["Workflows"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(webhooks_router, prefix="/webhooks", tags=["Webhooks"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": settings.app_version, "app": settings.app_name}
