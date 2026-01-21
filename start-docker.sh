#!/bin/bash
# Start Docker Stack

echo "🚀 Starting Docker Stack..."
echo ""

# Check for AWS credentials
if ! grep -q "^AWS_ACCESS_KEY_ID=" .env || grep -q "^AWS_ACCESS_KEY_ID=your" .env; then
    echo "⚠️  WARNING: AWS credentials not configured in .env"
    echo "   The backend will fail to start without valid AWS credentials."
    echo ""
    echo "   Edit .env and set:"
    echo "   AWS_ACCESS_KEY_ID=your-actual-key"
    echo "   AWS_SECRET_ACCESS_KEY=your-actual-secret"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Start services
echo "Starting services..."
docker-compose up -d

echo ""
echo "Waiting for services to be healthy..."
sleep 10

# Check status
docker-compose ps

echo ""
echo "✅ Docker stack started!"
echo ""
echo "Services:"
echo "- Frontend:   http://localhost:3000"
echo "- Backend:    http://localhost:8000"
echo "- Materials:  http://localhost:8081"
echo "- Permitting: http://localhost:8082"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop:      docker-compose down"
echo "To test:      ./test-docker-stack.sh"
