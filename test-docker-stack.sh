#!/bin/bash
# Docker Stack Health Check Script

set -e

echo "🔍 Docker Stack Health Check"
echo "=============================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if docker-compose is running
echo "1. Checking if Docker Compose is running..."
if docker-compose ps | grep -q "Up"; then
	echo -e "${GREEN}✓${NC} Docker Compose is running"
else
	echo -e "${RED}✗${NC} Docker Compose is not running"
	echo "   Run: docker-compose up -d"
	exit 1
fi
echo ""

# Check service status
echo "2. Checking service status..."
docker-compose ps
echo ""

# Check AWS credentials in .env
echo "3. Checking AWS credentials..."
if grep -q "^AWS_ACCESS_KEY_ID=" .env && ! grep -q "^AWS_ACCESS_KEY_ID=your" .env; then
	echo -e "${GREEN}✓${NC} AWS credentials configured in .env"
else
	echo -e "${RED}✗${NC} AWS credentials not configured in .env"
	echo "   Edit .env and set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
fi
echo ""

# Test Materials MCP Server
echo "4. Testing Materials MCP Server (port 8081)..."
if curl -sf http://localhost:8081/health >/dev/null 2>&1; then
	echo -e "${GREEN}✓${NC} Materials MCP Server is healthy"
	curl -s http://localhost:8081/health | jq . 2>/dev/null || curl -s http://localhost:8081/health
else
	echo -e "${RED}✗${NC} Materials MCP Server is not responding"
	echo "   Check logs: docker-compose logs materials"
fi
echo ""

# Test Permitting MCP Server
echo "5. Testing Permitting MCP Server (port 8082)..."
if curl -sf http://localhost:8082/health >/dev/null 2>&1; then
	echo -e "${GREEN}✓${NC} Permitting MCP Server is healthy"
	curl -s http://localhost:8082/health | jq . 2>/dev/null || curl -s http://localhost:8082/health
else
	echo -e "${RED}✗${NC} Permitting MCP Server is not responding"
	echo "   Check logs: docker-compose logs permitting"
fi
echo ""

# Test Backend API
echo "6. Testing Backend API (port 8000)..."
if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
	echo -e "${GREEN}✓${NC} Backend API is healthy"

	# Test detailed health
	echo "   Checking detailed health..."
	HEALTH=$(curl -s http://localhost:8000/api/health/detailed)
	echo "$HEALTH" | jq . 2>/dev/null || echo "$HEALTH"
else
	echo -e "${RED}✗${NC} Backend API is not responding"
	echo "   Check logs: docker-compose logs backend"
fi
echo ""

# Test Frontend
echo "7. Testing Frontend (port 3000)..."
if curl -sf http://localhost:3000/health >/dev/null 2>&1; then
	echo -e "${GREEN}✓${NC} Frontend is healthy"
else
	echo -e "${RED}✗${NC} Frontend is not responding"
	echo "   Check logs: docker-compose logs frontend"
fi
echo ""

# Check network connectivity
echo "8. Checking internal network connectivity..."
if docker-compose exec -T backend curl -sf http://materials:8080/health >/dev/null 2>&1; then
	echo -e "${GREEN}✓${NC} Backend can reach Materials MCP"
else
	echo -e "${RED}✗${NC} Backend cannot reach Materials MCP"
fi

if docker-compose exec -T backend curl -sf http://permitting:8080/health >/dev/null 2>&1; then
	echo -e "${GREEN}✓${NC} Backend can reach Permitting MCP"
else
	echo -e "${RED}✗${NC} Backend cannot reach Permitting MCP"
fi
echo ""

# Summary
echo "=============================="
echo "Summary:"
echo "- Frontend:   http://localhost:3000"
echo "- Backend:    http://localhost:8000"
echo "- Materials:  http://localhost:8081"
echo "- Permitting: http://localhost:8082"
echo ""
echo "To view logs: docker-compose logs -f [service-name]"
echo "To restart:   docker-compose restart [service-name]"
echo "To rebuild:   docker-compose up --build [service-name]"
