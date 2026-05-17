FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy project files for dependency installation
COPY pyproject.toml .
COPY uv.lock* .
COPY README.md .

# Install dependencies with uv
RUN uv sync --no-dev --frozen

# Copy source code
COPY backend/ ./backend/

# Create required directories
RUN mkdir -p logs exports

# Pre-download HuggingFace embedding model so it's baked into the image
RUN uv run python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Run with uv
CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
