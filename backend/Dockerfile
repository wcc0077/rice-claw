# Backend Dockerfile for Shrimp Market
# Uses uv for fast dependency management

FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

# Install uv using pip to avoid ghcr.io access issues
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml ./

# Install dependencies
RUN uv pip install --system -e .

# Copy application code
COPY src/ ./src/

# Create directories
RUN mkdir -p /app/data /app/init-data

# Copy database template (used for RESET_DATA=true)
COPY data/shrimp_market.db /app/init-data/

# Copy entrypoint script
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Set default database path
ENV DATABASE_PATH=/app/data/shrimp_market.db

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Use entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]