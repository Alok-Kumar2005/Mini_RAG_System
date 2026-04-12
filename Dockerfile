# ── Backend Dockerfile (optimized for Render free tier) ──
# Multi-stage build: build deps in builder, copy to slim runtime

# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

# Install only the system libs needed for psycopg (postgres driver)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install Python deps into a separate prefix so we can copy them cleanly
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Stage 2: Slim runtime
FROM python:3.12-slim

WORKDIR /app

# Runtime postgres lib only (no gcc)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code only
COPY main.py .
COPY src/ ./src/

# Render sets PORT automatically (default 10000)
ENV PORT=8000

EXPOSE ${PORT}

# Run with uvicorn — bind to 0.0.0.0 so Render can reach it
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
