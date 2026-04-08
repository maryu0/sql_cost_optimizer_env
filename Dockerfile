# ==============================================================================
# SQL Cost Optimizer OpenEnv - Hugging Face Spaces Dockerfile
# ==============================================================================
FROM python:3.11-slim

# HF Spaces labels
LABEL org.opencontainers.image.title="SQL Cost Optimizer OpenEnv"
LABEL space.huggingface.sdk="docker"
LABEL openenv="true"

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (HF Spaces requirement)
RUN useradd -m -u 1000 appuser

# Copy requirements first for caching
COPY --chown=appuser:appuser requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Set ownership
RUN chown -R appuser:appuser /app

USER appuser

# Expose port 7860 (HF Spaces default)
EXPOSE 7860

# Health check using curl
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Run on port 7860
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "7860"]
