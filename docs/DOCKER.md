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
| Frontend (React) | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

---

## Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                      Docker Compose Network                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────┐       ┌──────────────────────┐       │
│  │      Frontend        │       │       Backend        │       │
│  │    (gc-frontend)     │──────▶│     (gc-backend)     │       │
│  │                      │       │                      │       │
│  │  - nginx:80          │       │  - FastAPI:8000      │       │
│  │  - React SPA         │       │  - Strands Agents    │       │
│  │  - Static assets     │       │  - MCP Servers       │       │
│  │                      │       │    (stdio mode)      │       │
│  └──────────┬───────────┘       └──────────┬───────────┘       │
│             │                              │                    │
│             │                              │                    │
│     localhost:3000                 localhost:8000               │
│                                            │                    │
└────────────────────────────────────────────│────────────────────┘
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
| `gc-backend` | python:3.13-slim | 8000 | FastAPI + Agents + MCP Servers |
| `gc-frontend` | nginx:alpine | 3000 (→80) | React SPA served by nginx |

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

# View backend logs only
docker-compose logs -f backend

# View frontend logs only
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
- 60-second startup period for MCP initialization
- Health check endpoint at `/health`

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
- Static asset caching

---

## Development Workflow

### Rebuild After Code Changes

```bash
# Rebuild specific service
docker-compose up --build backend

# Rebuild all services
docker-compose up --build
```

### Access Container Shell

```bash
# Backend container
docker-compose exec backend bash

# Frontend container (sh only in alpine)
docker-compose exec frontend sh
```

### View Real-time Logs

```bash
# Follow all logs
docker-compose logs -f

# Follow specific service
docker-compose logs -f backend
```

### Test Health Endpoints

```bash
# Backend health
curl http://localhost:8000/health

# Backend detailed health
curl http://localhost:8000/api/health/detailed

# Frontend health
curl http://localhost:3000/health
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

### MCP Servers Not Initializing

**Symptoms:** Health check shows MCP services as "down"

**Solution:**
1. MCP servers initialize as subprocesses on first use
2. Check backend logs for MCP initialization errors
3. Verify Python path is correct in container

```bash
docker-compose exec backend python -c "import backend.mcp_servers.materials_supplier"
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
