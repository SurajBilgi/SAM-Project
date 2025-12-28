# Real-Time Vision Platform

A production-grade, cloud-native real-time computer vision platform with ultra-low latency video streaming and inference.

## 🏗️ Architecture

```
┌─────────────┐     WebRTC/WS      ┌──────────────┐
│   Browser   │ ←─────────────────→ │   Frontend   │
│  (Webcam)   │                     │  (React/TS)  │
└─────────────┘                     └──────┬───────┘
                                           │
┌─────────────┐     RTSP/HTTP       ┌──────▼───────┐
│ IP Cameras  │ ───────────────────→ │  API Service │
└─────────────┘                     │   (FastAPI)  │
                                    └──────┬───────┘
                                           │
                                    ┌──────▼───────┐
                                    │  Streaming   │
                                    │   Service    │
                                    └──────┬───────┘
                                           │
                                    ┌──────▼───────┐
                                    │  Inference   │
                                    │  Service     │
                                    │  (gRPC/CV)   │
                                    └──────────────┘
```

## ✨ Features

- **Ultra-Low Latency**: Sub-200ms end-to-end latency
- **Multiple Input Sources**: Webcam + IP Cameras (RTSP/HTTP)
- **Real-Time Inference**: Live computer vision processing
- **Production Ready**: Docker + Kubernetes ready
- **Auto-Recovery**: Automatic reconnection and graceful degradation
- **Scalable**: Horizontal pod autoscaling support
- **Observable**: Structured logging and metrics

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.10+ (for local backend development)
- Kubernetes cluster (for production deployment)

### Local Development with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Local Development without Docker

#### Backend Services

```bash
# API Service
cd backend/api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Streaming Service
cd backend/streaming
pip install -r requirements.txt
python main.py

# Inference Service
cd backend/inference
pip install -r requirements.txt
python server.py
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 📦 Production Deployment (Kubernetes)

```bash
# Apply all Kubernetes manifests
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/

# Verify deployment
kubectl get pods -n vision-platform
kubectl get services -n vision-platform

# Access via LoadBalancer
kubectl get svc frontend-service -n vision-platform
```

## 🏗️ Project Structure

```
.
├── frontend/                 # TypeScript React application
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── services/        # API and WebRTC services
│   │   └── main.tsx
│   ├── Dockerfile
│   └── package.json
│
├── backend/
│   ├── api/                 # FastAPI control plane
│   │   ├── routes/
│   │   ├── models.py
│   │   ├── main.py
│   │   └── Dockerfile
│   │
│   ├── streaming/           # Frame ingestion service
│   │   ├── stream_manager.py
│   │   ├── rtsp_reader.py
│   │   ├── frame_bus.py
│   │   └── Dockerfile
│   │
│   ├── inference/           # CV inference service
│   │   ├── server.py
│   │   ├── model.py
│   │   ├── protos/
│   │   └── Dockerfile
│   │
│   └── common/              # Shared utilities
│       ├── models.py
│       └── utils.py
│
└── infra/
    ├── docker/              # Docker configurations
    └── k8s/                 # Kubernetes manifests
        ├── namespace.yaml
        ├── *-deployment.yaml
        ├── *-service.yaml
        └── hpa.yaml
```

## 🔧 Configuration

### Environment Variables

#### API Service
- `INFERENCE_SERVICE_URL`: gRPC endpoint for inference service
- `STREAMING_SERVICE_URL`: HTTP endpoint for streaming service
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

#### Streaming Service
- `INFERENCE_SERVICE_URL`: gRPC endpoint for inference service
- `MAX_FPS`: Maximum frames per second to process
- `LOG_LEVEL`: Logging level

#### Inference Service
- `MODEL_VERSION`: Version identifier for the model
- `DEVICE`: Compute device (cpu, cuda)
- `LOG_LEVEL`: Logging level

#### Frontend
- `VITE_API_URL`: Backend API base URL
- `VITE_WS_URL`: WebSocket URL for real-time communication

## 📊 Performance Characteristics

- **Target Latency**: < 200ms end-to-end
- **Frame Rate**: Up to 30 FPS
- **Backpressure Handling**: Drops frames instead of buffering
- **Auto-Reconnect**: Automatic recovery on connection loss

## 🔒 Security

- Token-based session management
- No hardcoded credentials
- Environment-based configuration
- Secure RTSP credential handling
- CORS configuration for production

## 📈 Observability

- Structured JSON logging
- Health check endpoints on all services
- Metrics for FPS, latency, and throughput
- Ready for Prometheus/Grafana integration

## 🛠️ Development

### Adding a New CV Model

1. Update `backend/inference/model.py`
2. Implement the `InferenceModel` interface
3. Update model loading logic in `server.py`
4. Rebuild inference service Docker image

### Adding a New Camera Source

1. Extend `backend/streaming/stream_manager.py`
2. Add new reader class (similar to `RTSPReader`)
3. Register in camera routes

## 🧪 Testing

```bash
# Backend tests
cd backend/api
pytest

# Frontend tests
cd frontend
npm test
```

## 📝 API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Contributing

This is a production-grade foundation designed for extensibility. Key extension points:

- Custom CV models in `backend/inference/`
- Additional camera sources in `backend/streaming/`
- Frontend visualization components in `frontend/src/components/`

## 📄 License

See LICENSE file for details.

## 🔮 Future Enhancements

- [ ] LLM-based reasoning integration
- [ ] Multi-model ensemble support
- [ ] Advanced analytics and alerting
- [ ] Cloud storage integration
- [ ] Mobile app support
