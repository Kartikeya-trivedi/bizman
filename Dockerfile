# ── Stage 1: Builder ─────────────────────────────────────
FROM python:3.11-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy only dependency files first (maximizes layer cache hits)
COPY pyproject.toml uv.lock README.md ./

# Install production deps only, skip modal (it's for `modal deploy`, not Docker)
RUN uv sync --no-dev --frozen --no-install-package modal

# Copy source code (separate layer so dep cache isn't busted by code changes)
COPY backend/ ./backend/

# Pre-download HuggingFace embedding model so it's baked into the image
RUN --mount=type=cache,target=/root/.cache/huggingface \
    uv run python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" && \
    cp -r /root/.cache/huggingface /app/.hf_cache

# ── Stage 2: Runtime (clean, minimal image) ─────────────
FROM python:3.11-slim

WORKDIR /app

# Copy the virtual environment from the builder
COPY --from=builder /app/.venv /app/.venv

# Copy the application source
COPY --from=builder /app/backend /app/backend

# Copy the pre-downloaded HuggingFace models
COPY --from=builder /app/.hf_cache /root/.cache/huggingface

# Create required directories
RUN mkdir -p logs exports

# Use the venv directly (no need for uv at runtime)
ENV PATH="/app/.venv/bin:$PATH"

# Hugging Face Spaces default port is 7860
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
