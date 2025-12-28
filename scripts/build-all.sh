#!/bin/bash
# Build all Docker images for the Real-Time Vision Platform

set -e

echo "🏗️  Building Real-Time Vision Platform Docker Images"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to build and tag image
build_image() {
    local service=$1
    local context=$2
    local dockerfile=$3
    
    echo -e "${BLUE}Building $service...${NC}"
    docker build -t vision-platform/$service:latest -f $dockerfile $context
    echo -e "${GREEN}✓ $service built successfully${NC}"
    echo ""
}

# Build each service
build_image "api" "./backend/api" "./backend/api/Dockerfile"
build_image "streaming" "./backend/streaming" "./backend/streaming/Dockerfile"
build_image "inference" "./backend/inference" "./backend/inference/Dockerfile"
build_image "frontend" "./frontend" "./frontend/Dockerfile"

echo ""
echo -e "${GREEN}🎉 All images built successfully!${NC}"
echo ""
echo "Available images:"
docker images | grep vision-platform

echo ""
echo "To run locally:"
echo "  docker-compose up"
echo ""
echo "To deploy to Kubernetes:"
echo "  kubectl apply -f infra/k8s/"

