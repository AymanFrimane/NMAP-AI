# ============================================================================
# NMAP-AI API Dockerfile
# Person 4's responsibility
# 
# Multi-stage build for optimized image size
# ============================================================================

# ============================================================================
# Stage 1: Builder
# ============================================================================
FROM python:3.11-slim as builder

LABEL maintainer="NMAP-AI Team"
LABEL description="Builder stage for NMAP-AI API"

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 2: Runtime
# ============================================================================
FROM python:3.11-slim

LABEL maintainer="NMAP-AI Team"
LABEL description="NMAP-AI FastAPI Application"

# Set working directory
WORKDIR /app

# Install runtime dependencies including nmap
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Nmap for validation
    nmap \
    # Network tools
    curl \
    wget \
    # Process management
    procps \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create necessary directories
RUN mkdir -p \
    agents \
    api \
    data/kg \
    data/raw \
    data/processed \
    models \
    artifacts \
    logs \
    tests

# Copy application code
COPY agents/ ./agents/
COPY api/ ./api/
COPY data/ ./data/
COPY models/ ./models/
COPY requirements.txt .

# Create non-root user for security
RUN useradd -m -u 1000 nmapai && \
    chown -R nmapai:nmapai /app

# Switch to non-root user
USER nmapai

# Set Python environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ============================================================================
# Build Instructions
# ============================================================================
#
# Build image:
#   docker build -t nmap-ai-api:latest .
#
# Build with specific Python version:
#   docker build --build-arg PYTHON_VERSION=3.11 -t nmap-ai-api:latest .
#
# Run container:
#   docker run -p 8000:8000 \
#     -e NEO4J_URI=bolt://host.docker.internal:7687 \
#     nmap-ai-api:latest
#
# Run with development mode (hot reload):
#   docker run -p 8000:8000 \
#     -v $(pwd)/agents:/app/agents \
#     -v $(pwd)/api:/app/api \
#     nmap-ai-api:latest \
#     uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
#
# ============================================================================
