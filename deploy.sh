#!/bin/bash
set -e

echo "Starting AgentForge deployment..."

docker-compose -f docker-compose.prod.yml up -d --build

echo "Starting services..."
docker-compose -f docker-compose.prod.yml up -d

echo "Waiting for services to be healthy..."
sleep 10

echo "Checking service health..."
docker-compose -f docker-compose.prod.yml ps

echo "Deployment complete!"
echo "AgentForge is now running at:"
echo "  - API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - N8N: http://localhost:5678"
