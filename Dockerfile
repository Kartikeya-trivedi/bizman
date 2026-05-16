FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy pyproject.toml for dependency installation
COPY pyproject.toml .
COPY uv.lock* .

# Install dependencies with uv
RUN uv sync --no-dev --frozen

# Copy source code
COPY backend/ ./backend/

# Create required directories
RUN mkdir -p logs exports

# Run with uv
CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
