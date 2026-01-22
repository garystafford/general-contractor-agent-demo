# Docker Deployment Guide

Run the entire General Contractor Agent Demo stack using Docker Compose - no local Python or Node.js installation required.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Docker Commands](#docker-commands)
- [Container Details](#container-details)
- [Development Workflow](#development-workflow)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

- **Docker Desktop** (or Docker Engine + Docker Compose)
- **AWS Credentials** with Amazon Bedrock access (Claude Sonnet model enabled)

### Verify Docker Installation

```bash
# Check Docker version
docker --version

# Check Docker Compose version
docker compose version
```

---

## Quick Start

### 1. Configure AWS Credentials

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your AWS credentials
```

**Required environment variables in `.env`:**

```bash
# AWS Bedrock credentials (REQUIRED for Docker)
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1

# Optional: Session token (only for temporary credentials)
# AWS_SESSION_TOKEN=your_session_token_here
```

> **Note:** Docker cannot use AWS SSO profiles. You must provide explicit credentials.

### 2. Build and Start

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode (background)
docker-compose up --build -d
```

### 3. Access the Application

| Service | URL |
|---------|-----|
| Frontend (React) | <http://localhost:3000> |
| Backend API | <http://localhost:8000> |
| API Documentation | <http://localhost:8000/docs> |
| Health Check | <http://localhost:8000/health> |
| Materials MCP Server | <http://localhost:8081/health> |
| Permitting MCP Server | <http://localhost:8082/health> |

---

## Architecture

The Docker Compose stack runs **4 containers** that communicate over an internal network:

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                          Docker Compose Network (gc-network)                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────┐                    ┌────────────────────┐            │
│  │     Frontend       │                    │      Backend       │            │
│  │  (gc-frontend)     │───────────────────▶│   (gc-backend)     │            │
│  │                    │     HTTP API       │                    │            │
│  │  - nginx:80        │                    │  - FastAPI:8000    │            │
│  │  - React SPA       │                    │  - Strands Agents  │            │
│  └────────┬───────────┘                    └─────────┬──────────┘            │
│           │                                          │                       │
│   localhost:3000                                     │ HTTP (MCP Protocol)   │
│                                                      │                       │
│                         ┌────────────────────────────┼───────────────────┐   │
│                         │                            │                   │   │
│                         ▼                            ▼                   │   │
│           ┌─────────────────────────┐  ┌─────────────────────────┐       │   │
│           │   Materials MCP Server  │  │  Permitting MCP Server  │       │   │
│           │   (gc-materials)        │  │  (gc-permitting)        │       │   │
│           │                         │  │                         │       │   │
│           │   - FastMCP:8080        │  │   - FastMCP:8080        │       │   │
│           │   - Streamable HTTP     │  │   - Streamable HTTP     │       │   │
│           └────────────┬────────────┘  └────────────┬────────────┘       │   │
│                        │                            │                    │   │
│                localhost:8081                  localhost:8082            │   │
│                                                                          │   │
└──────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
                                ┌────────────────┐
                                │  AWS Bedrock   │
                                │  (Claude LLM)  │
                                └────────────────┘
```

### Container Summary

| Container | Base Image | Port | Purpose |
|-----------|------------|------|---------|
| `gc-materials` | python:3.13-slim | 8081 (→8080) | Materials Supplier MCP Server |
| `gc-permitting` | python:3.13-slim | 8082 (→8080) | Permitting Service MCP Server |
| `gc-backend` | python:3.13-slim | 8000 | FastAPI + Strands Agents |
| `gc-frontend` | nginx:alpine | 3000 (→80) | React SPA served by nginx |

### Startup Order

1. **MCP Servers** start first (materials, permitting)
2. **Backend** waits for MCP servers to be healthy before starting
3. **Frontend** waits for backend to be healthy before starting

---

## Configuration

### Environment Variables

The backend container reads configuration from environment variables defined in `docker-compose.yaml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `AWS_REGION` | us-east-1 | AWS region for Bedrock |
| `AWS_ACCESS_KEY_ID` | (required) | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | (required) | AWS secret key |
| `AWS_SESSION_TOKEN` | (optional) | Temporary session token |
| `DEFAULT_MODEL` | us.anthropic.claude-sonnet-4-5-20250929-v1:0 | Bedrock model ID |
| `MCP_MODE` | http | MCP connection mode (http for Docker) |
| `MATERIALS_MCP_URL` | <http://materials:8080/mcp> | Materials MCP endpoint |
| `PERMITTING_MCP_URL` | <http://permitting:8080/mcp> | Permitting MCP endpoint |
| `TASK_TIMEOUT_SECONDS` | 60 | Timeout per task |
| `MAX_CONSECUTIVE_TOOL_CALLS` | 3 | Loop detection threshold |
| `MAX_TOTAL_TOOL_CALLS` | 20 | Max tool calls per task |
| `LOG_LEVEL` | INFO | Logging verbosity |

### Frontend Build Arguments

The frontend is built with the API URL baked in at build time:

```yaml
build:
  args:
    - VITE_API_URL=http://localhost:8000
```

To change the API URL, modify `docker-compose.yaml` and rebuild.

---

## Docker Commands

### Basic Operations

```bash
# Start services (foreground)
docker-compose up

# Start services (background)
docker-compose up -d

# Build and start
docker-compose up --build

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f materials
docker-compose logs -f permitting
docker-compose logs -f frontend

# View last 100 lines
docker-compose logs --tail=100 backend
```

### Container Management

```bash
# List running containers
docker-compose ps

# Restart a service
docker-compose restart backend

# Execute command in container
docker-compose exec backend bash

# View container resource usage
docker stats
```

### Cleanup

```bash
# Remove stopped containers
docker-compose rm

# Remove all project containers, networks, and volumes
docker-compose down -v --rmi local

# Prune unused Docker resources
docker system prune -a
```

---

## Container Details

### MCP Server Containers

**Dockerfiles:** `docker/materials-mcp/Dockerfile`, `docker/permitting-mcp/Dockerfile`

Both MCP servers use the same structure:

```dockerfile
FROM python:3.13-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl

# Install Python dependencies
COPY deployment-ecs/*/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY deployment-ecs/*/app/ ./app/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080
CMD ["python", "-m", "app.main"]
```

**Key Features:**

- FastMCP with streamable HTTP transport
- Health check endpoint at `/health`
- MCP endpoint at `/mcp`

### Backend Container (`gc-backend`)

**Dockerfile:** `backend/Dockerfile`

```dockerfile
FROM python:3.13-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy backend code
COPY backend/ ./backend/

# Security: Non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "backend.api.routes:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Key Features:**

- Python 3.13 slim image
- Runs as non-root user for security
- 60-second startup period for initialization
- Connects to MCP servers via HTTP (MCP_MODE=http)

### Frontend Container (`gc-frontend`)

**Dockerfile:** `frontend/Dockerfile`

```dockerfile
# Build stage
FROM node:20-slim AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
ARG VITE_API_URL=http://localhost:8000
RUN npm run build

# Production stage
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1
CMD ["nginx", "-g", "daemon off;"]
```

**Key Features:**

- Multi-stage build (Node.js → nginx)
- Production-optimized nginx configuration
- SPA routing support (all routes → index.html)
- Gzip compression enabled

---

## Development Workflow

### Rebuild After Code Changes

```bash
# Rebuild specific service
docker-compose up --build backend

# Rebuild MCP servers
docker-compose up --build materials permitting

# Rebuild all services
docker-compose up --build
```

### Access Container Shell

```bash
# Backend container
docker-compose exec backend bash

# MCP server container
docker-compose exec materials bash

# Frontend container (sh only in alpine)
docker-compose exec frontend sh
```

### Test Health Endpoints

```bash
# MCP servers health
curl http://localhost:8081/health  # Materials MCP
curl http://localhost:8082/health  # Permitting MCP

# Backend health
curl http://localhost:8000/health

# Backend detailed health (includes MCP status)
curl http://localhost:8000/api/health/detailed

# Frontend health
curl http://localhost:3000/health
```

### Test MCP Endpoints Directly

```bash
# Test Materials MCP server
curl -X POST http://localhost:8081/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/list"}'

# Test Permitting MCP server
curl -X POST http://localhost:8082/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/list"}'
```

---

## Troubleshooting

### Backend Won't Start

**Error:** `AWS credentials not found`

**Solution:**

1. Ensure `.env` file exists with valid credentials
2. Verify credentials are not expired
3. Docker cannot use AWS SSO profiles - use explicit keys

```bash
# Check if .env is being loaded
docker-compose exec backend env | grep AWS
```

**Error:** `Port 8000 already in use`

**Solution:**

```bash
# Find process using port
lsof -i :8000

# Kill process or change port in docker-compose.yaml
```

### MCP Servers Not Starting

**Symptoms:** Backend logs show connection errors to MCP servers

**Solution:**

1. Check MCP server logs: `docker-compose logs materials`
2. Verify health endpoints: `curl http://localhost:8081/health`
3. Ensure MCP servers started before backend (check startup order)

```bash
# Check all container statuses
docker-compose ps

# View MCP server logs
docker-compose logs -f materials permitting
```

### Frontend Can't Connect to Backend

**Symptoms:** API calls fail, blank dashboard

**Solution:**

1. Check backend is healthy: `docker-compose ps`
2. Verify backend logs: `docker-compose logs backend`
3. Test backend directly: `curl http://localhost:8000/health`
4. Ensure `VITE_API_URL` build arg is correct

### Container Keeps Restarting

**Solution:**

```bash
# Check logs for error
docker-compose logs backend

# Check container status
docker-compose ps

# View container events
docker events --filter container=gc-backend
```

### Slow Container Builds

**Solution:**

```bash
# Use BuildKit for faster builds
DOCKER_BUILDKIT=1 docker-compose build

# Prune build cache if needed
docker builder prune
```

### Memory Issues

**Solution:**

```bash
# Check container memory usage
docker stats

# Increase Docker memory limit in Docker Desktop settings
```

---

## Comparison: Docker vs Local Development

| Aspect | Docker | Local Development |
|--------|--------|-------------------|
| Setup | `docker-compose up` | Install Python, Node.js, uv |
| AWS Auth | Explicit credentials only | SSO profiles supported |
| Isolation | Full container isolation | Uses local environment |
| MCP Mode | HTTP (separate containers) | stdio (subprocesses) |
| Rebuild | Container rebuild required | Hot reload available |
| Best For | Workshops, demos, CI/CD | Active development |

---

## Next Steps

- [QUICKSTART.md](QUICKSTART.md) - Test scripts and demos
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture details
- [README.md](../README.md) - Full project documentation

---

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Strands Agents Documentation](https://strandsagents.com/latest/)
