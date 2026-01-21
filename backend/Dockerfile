# Backend Dockerfile for General Contractor Agent Demo
# Includes the FastAPI backend with all agents and MCP servers (stdio mode)

FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml for dependency installation
COPY pyproject.toml .

# Install Python dependencies
# Using pip with pyproject.toml
RUN pip install --no-cache-dir .

# Copy backend code
COPY backend/ ./backend/

# Create a non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Environment variables (can be overridden)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV LOG_LEVEL=INFO

# MCP server paths (relative to /app)
ENV MATERIALS_MCP_PATH=backend/mcp_servers/materials_supplier.py
ENV PERMITTING_MCP_PATH=backend/mcp_servers/permitting.py
ENV MCP_PYTHON_EXECUTABLE=python

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose the API port
EXPOSE 8000

# Run the FastAPI application
CMD ["python", "-m", "uvicorn", "backend.api.routes:app", "--host", "0.0.0.0", "--port", "8000"]
