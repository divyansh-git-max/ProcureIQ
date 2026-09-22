# ─────────────────────────────────────────────
# Stage 1: Base image with system dependencies
# ─────────────────────────────────────────────
FROM python:3.12-slim AS base

# Prevents Python from writing .pyc files and buffers stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system-level dependencies
# - tesseract-ocr: required by pytesseract (OCR Stage 2)
# - libgl1 libglib2.0-0: required by PyMuPDF
# - poppler-utils: required for PDF rendering
# - curl: for health checks
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ─────────────────────────────────────────────
# Stage 2: Install Python dependencies with uv
# ─────────────────────────────────────────────
FROM base AS builder

# Install uv (fastest Python package installer)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first (layer caching - only reinstalls if these change)
COPY pyproject.toml uv.lock* ./

# Install all Python dependencies into /app/.venv
RUN uv sync --frozen --no-dev

# Download the spaCy model (required by Presidio in input_guard.py)
RUN uv run python -m spacy download en_core_web_lg

# ─────────────────────────────────────────────
# Stage 3: Final runtime image
# ─────────────────────────────────────────────
FROM base AS runtime

WORKDIR /app

# Copy installed venv from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy the entire backend source code
COPY . .

# Add venv to PATH so all commands use it
ENV PATH="/app/.venv/bin:$PATH"

# Create temp directory for document uploads
RUN mkdir -p /tmp/procureiq

EXPOSE 8000

# Health check - pings the FastAPI /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command: start FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
