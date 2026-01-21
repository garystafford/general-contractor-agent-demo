# Docker Stack Troubleshooting Guide

## Issues Fixed

### 1. MCP Server Host/Port Configuration ✅
**Problem**: MCP servers weren't passing host and port to the `run()` method.

**Fixed in**:
- `deployment/materials-supplier/app/main.py`
- `deployment/permitting-service/app/main.py`

Changed from:
```python
mcp.run(transport="streamable-http")
```

To:
```python
mcp.run(transport="streamable-http", host=HOST, port=PORT)
```

## Required Setup Steps

### 1. Configure AWS Credentials

Docker containers **cannot** use AWS SSO profiles. You must provide explicit credentials.

Edit your `.env` file and uncomment/set:

```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-actual-access-key
AWS_SECRET_ACCESS_KEY=your-actual-secret-key
# AWS_SESSION_TOKEN=your-token  # Only if using temporary credentials
```

**To get credentials**:
```bash
# If using SSO, get temporary credentials:
aws sso login --profile your-profile
aws configure export-credentials --profile your-profile

# Or create long-term credentials in AWS IAM Console
```

### 2. Start the Docker Stack

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up --build -d
```

### 3. Verify Services are Running

```bash
# Check service status
docker-compose ps

# Should show 4 services running:
# - gc-materials (port 8081)
# - gc-permitting (port 8082)
# - gc-backend (port 8000)
# - gc-frontend (port 3000)
```

### 4. Check Service Health

```bash
# Materials MCP Server
curl http://localhost:8081/health

# Permitting MCP Server
curl http://localhost:8082/health

# Backend API
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000/health
```

### 5. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f materials
docker-compose logs -f permitting
docker-compose logs -f frontend
```

## Common Issues

### Issue: Backend fails with "AWS credentials not found"

**Solution**: Ensure `.env` has valid AWS credentials (see step 1 above).

```bash
# Verify credentials are loaded
docker-compose exec backend env | grep AWS
```

### Issue: MCP servers fail to start

**Symptoms**: Backend logs show "Failed to initialize MCP clients"

**Check**:
```bash
# View MCP server logs
docker-compose logs materials
docker-compose logs permitting

# Common errors:
# - Port already in use
# - Missing dependencies
# - Python import errors
```

**Solution**:
```bash
# Rebuild MCP services
docker-compose up --build materials permitting
```

### Issue: Frontend can't connect to backend

**Symptoms**: Frontend shows connection errors or API calls fail

**Check**:
```bash
# Verify backend is accessible from host
curl http://localhost:8000/health

# Check if backend is running
docker-compose ps backend
```

**Solution**: Ensure backend is healthy before frontend starts (docker-compose handles this with `depends_on`).

### Issue: Port conflicts

**Symptoms**: "port is already allocated" error

**Solution**:
```bash
# Check what's using the ports
lsof -i :8000  # Backend
lsof -i :8081  # Materials
lsof -i :8082  # Permitting
lsof -i :3000  # Frontend

# Stop conflicting services or change ports in docker-compose.yaml
```

### Issue: Services keep restarting

**Check health checks**:
```bash
docker-compose ps

# If status shows "restarting", check logs
docker-compose logs --tail=100 <service-name>
```

## Testing the Stack

### 1. Test MCP Servers Directly

```bash
# Materials catalog
curl http://localhost:8081/mcp

# Permitting service
curl http://localhost:8082/mcp
```

### 2. Test Backend API

```bash
# Health check
curl http://localhost:8000/health

# Detailed health (includes MCP status)
curl http://localhost:8000/api/health/detailed

# Get agents
curl http://localhost:8000/api/agents
```

### 3. Test Full Stack

Open browser to: http://localhost:3000

## Cleanup

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

## Architecture

```
┌─────────────────┐
│   Frontend      │  Port 3000 (nginx)
│   (React/Vite)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Backend       │  Port 8000 (FastAPI)
│   (Strands)     │
└────┬───────┬────┘
     │       │
     ▼       ▼
┌─────────┐ ┌─────────┐
│Materials│ │Permitting│  Ports 8081, 8082
│   MCP   │ │   MCP    │  (FastMCP HTTP)
└─────────┘ └─────────┘
```

## Network Configuration

All services run on the `gc-network` bridge network:
- Services can communicate using container names (e.g., `http://materials:8080`)
- Host can access via localhost ports (e.g., `http://localhost:8081`)

## Environment Variables

### Backend
- `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` - AWS credentials
- `MCP_MODE=http` - Use HTTP transport for MCP
- `MATERIALS_MCP_URL=http://materials:8080/mcp` - Materials server URL
- `PERMITTING_MCP_URL=http://permitting:8080/mcp` - Permitting server URL

### MCP Servers
- `HOST=0.0.0.0` - Listen on all interfaces
- `PORT=8080` - Internal port (mapped to 8081/8082 on host)

### Frontend
- `VITE_API_URL=http://localhost:8000` - Backend API URL (build-time)
