# ── Stage 1: Frontend Builder ─────────────────────────────────
FROM node:20-slim AS frontend-builder

WORKDIR /src/dashboard

# Install dependencies
COPY dashboard/package*.json ./
RUN npm install

# Copy source and build (vite.config.ts outputs to ../static/dashboard)
COPY dashboard/ .
RUN npm run build

# ── Stage 2: Python Builder ───────────────────────────────────
FROM python:3.11-slim AS python-builder

WORKDIR /build-python

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into /build-python/venv
COPY requirements.txt .
RUN python -m venv /build-python/venv \
    && /build-python/venv/bin/pip install --upgrade pip \
    && /build-python/venv/bin/pip install --no-cache-dir -r requirements.txt

# ── Stage 3: Production ───────────────────────────────────────
FROM python:3.11-slim AS production

# Security: run as non-root user
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Install runtime system dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Use virtualenv binaries
ENV PATH="/app/venv/bin:$PATH"
ENV PYTHONPATH="/app"

# Copy virtualenv from builder
COPY --from=python-builder /build-python/venv /app/venv

# Copy dashboard build from frontend-builder
# (Vite config builds to ../static/dashboard relative to /src/dashboard)
COPY --chown=appuser:appuser --from=frontend-builder /src/static/dashboard /app/static/dashboard

# Copy application code
COPY --chown=appuser:appuser . .

# Create data directory for SQLite DB
RUN mkdir -p /app/data && chown appuser:appuser /app/data

# Switch to non-root user
USER appuser

# Use venv python
ENV PATH="/app/venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV APP_PORT=7860

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Run the application using the venv's uvicorn
CMD ["/app/venv/bin/uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
