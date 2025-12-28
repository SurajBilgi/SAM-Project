#!/bin/bash
# Deploy Real-Time Vision Platform to Kubernetes

set -e

echo "🚀 Deploying Real-Time Vision Platform to Kubernetes"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster. Please check your configuration."
    exit 1
fi

echo -e "${GREEN}✓ Connected to Kubernetes cluster${NC}"
echo ""

# Apply manifests
echo -e "${BLUE}Creating namespace...${NC}"
kubectl apply -f infra/k8s/namespace.yaml

echo -e "${BLUE}Applying configurations...${NC}"
kubectl apply -f infra/k8s/configmap.yaml

echo -e "${BLUE}Deploying API service...${NC}"
kubectl apply -f infra/k8s/api-deployment.yaml
kubectl apply -f infra/k8s/api-service.yaml

echo -e "${BLUE}Deploying Streaming service...${NC}"
kubectl apply -f infra/k8s/streaming-deployment.yaml
kubectl apply -f infra/k8s/streaming-service.yaml

echo -e "${BLUE}Deploying Inference service...${NC}"
kubectl apply -f infra/k8s/inference-deployment.yaml
kubectl apply -f infra/k8s/inference-service.yaml

echo -e "${BLUE}Deploying Frontend...${NC}"
kubectl apply -f infra/k8s/frontend-deployment.yaml
kubectl apply -f infra/k8s/frontend-service.yaml

echo -e "${BLUE}Configuring autoscaling...${NC}"
kubectl apply -f infra/k8s/hpa.yaml

echo ""
echo -e "${GREEN}✓ Deployment complete!${NC}"
echo ""

# Wait for pods to be ready
echo -e "${YELLOW}Waiting for pods to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=api -n vision-platform --timeout=120s || true
kubectl wait --for=condition=ready pod -l app=streaming -n vision-platform --timeout=120s || true
kubectl wait --for=condition=ready pod -l app=inference -n vision-platform --timeout=120s || true
kubectl wait --for=condition=ready pod -l app=frontend -n vision-platform --timeout=120s || true

echo ""
echo "📊 Deployment Status:"
echo "===================="
kubectl get pods -n vision-platform
echo ""
kubectl get services -n vision-platform
echo ""

# Get frontend URL
FRONTEND_URL=$(kubectl get svc frontend-service -n vision-platform -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
if [ "$FRONTEND_URL" != "pending" ] && [ -n "$FRONTEND_URL" ]; then
    echo -e "${GREEN}Frontend accessible at: http://$FRONTEND_URL${NC}"
else
    echo -e "${YELLOW}Frontend LoadBalancer IP is pending. Check with: kubectl get svc -n vision-platform${NC}"
fi

echo ""
echo "📝 Useful commands:"
echo "  kubectl get pods -n vision-platform"
echo "  kubectl logs -f deployment/api-deployment -n vision-platform"
echo "  kubectl port-forward svc/frontend-service 3000:80 -n vision-platform"

