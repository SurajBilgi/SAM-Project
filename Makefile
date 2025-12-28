# Makefile for Real-Time Vision Platform

.PHONY: help build run stop clean test docker-build k8s-deploy k8s-delete

help:
	@echo "Real-Time Vision Platform - Makefile Commands"
	@echo ""
	@echo "Development:"
	@echo "  make run              - Start all services with Docker Compose"
	@echo "  make stop             - Stop all services"
	@echo "  make logs             - View logs from all services"
	@echo "  make clean            - Clean up containers and volumes"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     - Build all Docker images"
	@echo "  make docker-push      - Push images to registry"
	@echo ""
	@echo "Kubernetes:"
	@echo "  make k8s-deploy       - Deploy to Kubernetes"
	@echo "  make k8s-delete       - Delete Kubernetes deployment"
	@echo "  make k8s-status       - Check deployment status"
	@echo ""
	@echo "Testing:"
	@echo "  make test             - Run all tests"
	@echo "  make test-backend     - Run backend tests"
	@echo "  make test-frontend    - Run frontend tests"

# Development
run:
	docker-compose up --build

stop:
	docker-compose down

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "node_modules" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +

# Docker
docker-build:
	@echo "Building API service..."
	docker build -t vision-platform/api:latest backend/api/
	@echo "Building Streaming service..."
	docker build -t vision-platform/streaming:latest backend/streaming/
	@echo "Building Inference service..."
	docker build -t vision-platform/inference:latest backend/inference/
	@echo "Building Frontend..."
	docker build -t vision-platform/frontend:latest frontend/
	@echo "All images built successfully!"

docker-push:
	docker push vision-platform/api:latest
	docker push vision-platform/streaming:latest
	docker push vision-platform/inference:latest
	docker push vision-platform/frontend:latest

# Kubernetes
k8s-deploy:
	@echo "Deploying to Kubernetes..."
	kubectl apply -f infra/k8s/namespace.yaml
	kubectl apply -f infra/k8s/configmap.yaml
	kubectl apply -f infra/k8s/
	@echo "Deployment complete!"
	@echo "Checking status..."
	kubectl get pods -n vision-platform

k8s-delete:
	kubectl delete namespace vision-platform

k8s-status:
	@echo "=== Pods ==="
	kubectl get pods -n vision-platform
	@echo ""
	@echo "=== Services ==="
	kubectl get services -n vision-platform
	@echo ""
	@echo "=== HPA ==="
	kubectl get hpa -n vision-platform

# Testing
test: test-backend test-frontend

test-backend:
	@echo "Running backend tests..."
	cd backend/api && pytest
	cd backend/streaming && pytest
	cd backend/inference && pytest

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && npm test

# Development setup
install-backend:
	cd backend/api && pip install -r requirements.txt
	cd backend/streaming && pip install -r requirements.txt
	cd backend/inference && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

install: install-backend install-frontend

# Protobuf compilation
compile-protos:
	cd backend/inference && chmod +x compile_protos.sh && ./compile_protos.sh

