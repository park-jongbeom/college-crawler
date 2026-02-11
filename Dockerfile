# Multi-stage build for Python application
FROM python:3.12-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    cron \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r crawler && useradd -r -g crawler crawler

# Copy Python packages from builder
COPY --from=builder /root/.local /home/crawler/.local

# Copy application code
COPY --chown=crawler:crawler . .

# Create logs directory with proper permissions
RUN mkdir -p /app/logs && chown -R crawler:crawler /app/logs

# Add local bin to PATH
ENV PATH=/home/crawler/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER crawler:crawler

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command (can be overridden)
CMD ["python", "src/main.py", "crawl"]
