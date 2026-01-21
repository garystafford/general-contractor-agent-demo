# Dockerfile for Permitting Service MCP Server (HTTP Transport)
# For local Docker deployment with docker-compose

FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY deployment/permitting-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code from deployment directory
COPY deployment/permitting-service/app/ ./app/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV HOST=0.0.0.0

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE 8080

# Run the server
CMD ["python", "-m", "app.main"]
