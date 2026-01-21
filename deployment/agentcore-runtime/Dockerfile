# AgentCore Runtime Dockerfile
# Packages the General Contractor agents for deployment to Amazon Bedrock AgentCore Runtime
#
# This container connects to MCP servers deployed via AgentCore Gateway (HTTP mode)
# rather than running MCP servers as local subprocesses.

FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml for dependency installation
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir .

# Copy backend code (agents, orchestration, config)
COPY backend/ ./backend/

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# API configuration
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV LOG_LEVEL=INFO

# MCP configuration - HTTP mode for AgentCore Gateway
ENV MCP_MODE=http
# These must be set at runtime to point to deployed MCP servers
# ENV MATERIALS_MCP_URL=http://materials-mcp-alb.us-east-1.elb.amazonaws.com/mcp
# ENV PERMITTING_MCP_URL=http://permitting-mcp-alb.us-east-1.elb.amazonaws.com/mcp

# Task configuration
ENV TASK_TIMEOUT_SECONDS=120
ENV MAX_CONSECUTIVE_TOOL_CALLS=3
ENV MAX_TOTAL_TOOL_CALLS=20

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose the API port
EXPOSE 8000

# Run the FastAPI application
CMD ["python", "-m", "uvicorn", "backend.api.routes:app", "--host", "0.0.0.0", "--port", "8000"]
