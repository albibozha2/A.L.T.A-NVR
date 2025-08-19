#!/bin/bash

# OpenNVR Docker Build and Run Script

set -e

echo "🐳 Building OpenNVR Docker image..."

# Build the Docker image
docker build -f Dockerfile.fixed -t opennvr:latest .

echo "✅ Docker image built successfully!"

# Optional: Run with docker-compose
echo ""
echo "To run with docker-compose:"
echo "  docker-compose up -d"
echo ""
echo "To run standalone:"
echo "  docker run -p 8080:8080 -v \$(pwd)/data:/app/data -v \$(pwd)/recordings:/app/recordings -v \$(pwd)/logs:/app/logs opennvr:latest"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop:"
echo "  docker-compose down"
