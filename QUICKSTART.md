# Quick Start Guide

Get the Real-Time Vision Platform running in under 5 minutes!

## Prerequisites

- Docker Desktop (or Docker + Docker Compose)
- 4GB+ RAM available
- Chrome/Firefox/Safari browser

## Option 1: Docker Compose (Recommended)

### 1. Clone the Repository

```bash
git clone <repository-url>
cd SAM-Project
```

### 2. Start All Services

```bash
docker-compose up --build
```

This will:
- Build all 4 services (API, Streaming, Inference, Frontend)
- Start containers with proper networking
- Expose ports for access

### 3. Access the Application

Open your browser and navigate to:

```
http://localhost:3000
```

### 4. Use the Platform

**Option A: Webcam**
1. Click "Start Webcam"
2. Allow camera access when prompted
3. See live video with AI detections!

**Option B: IP Camera**
1. Enter your RTSP URL (e.g., `rtsp://192.168.1.100:554/stream`)
2. Add credentials if needed
3. Click "Connect"
4. View your camera stream with AI!

### 5. Stop the Services

Press `Ctrl+C` in the terminal, then:

```bash
docker-compose down
```

## Option 2: Kubernetes

### Prerequisites

- Kubernetes cluster (minikube, kind, or cloud)
- kubectl configured

### 1. Build Images

```bash
make docker-build
```

### 2. Deploy

```bash
make k8s-deploy
```

### 3. Access

```bash
# Get the frontend URL
kubectl get svc frontend-service -n vision-platform

# Or port-forward for local access
kubectl port-forward svc/frontend-service 3000:80 -n vision-platform
```

Then visit: http://localhost:3000

## Option 3: Local Development

For development with hot-reload:

### 1. Install Dependencies

```bash
chmod +x scripts/local-dev.sh
./scripts/local-dev.sh
```

### 2. Start Services Individually

**Terminal 1: API Service**
```bash
cd backend/api
uvicorn main:app --reload --port 8000
```

**Terminal 2: Streaming Service**
```bash
cd backend/streaming
python main.py
```

**Terminal 3: Inference Service**
```bash
cd backend/inference
python server.py
```

**Terminal 4: Frontend**
```bash
cd frontend
npm run dev
```

### 3. Access

Frontend: http://localhost:3000  
API Docs: http://localhost:8000/docs

## Troubleshooting

### Webcam not working?

1. Ensure browser has camera permissions
2. Check if another app is using the camera
3. Try incognito/private browsing mode

### RTSP camera not connecting?

1. Verify the RTSP URL is correct
2. Check network connectivity to camera
3. Ensure credentials are correct
4. Try a test stream: `rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4`

### Docker build failing?

```bash
# Clean everything and rebuild
docker-compose down -v
docker system prune -a
docker-compose up --build
```

### Services not communicating?

```bash
# Check service health
curl http://localhost:8000/health  # API
curl http://localhost:8001/health  # Streaming

# View logs
docker-compose logs api
docker-compose logs streaming
docker-compose logs inference
```

### Performance issues?

1. Close other resource-intensive apps
2. Reduce FPS in camera settings
3. Allocate more RAM to Docker (Settings > Resources)

## Next Steps

- Read the [Architecture Documentation](ARCHITECTURE.md)
- Check out [Contributing Guidelines](CONTRIBUTING.md)
- Review [API Documentation](http://localhost:8000/docs) when running
- Explore [Kubernetes Deployment](infra/k8s/README.md)

## Test URLs

If you don't have an IP camera, try these public test streams:

**H.264 Stream**:
```
rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4
```

**Another test stream**:
```
rtsp://rtsp.stream/pattern
```

## Performance Expectations

On a typical development machine:
- **Latency**: 100-200ms end-to-end
- **FPS**: 25-30 fps
- **Inference**: 15-50ms per frame (CPU)
- **Memory**: ~2GB total for all services

## What's Next?

1. **Replace the stub model**: Integrate YOLO or your custom CV model
2. **Add WebRTC**: Reduce latency even further
3. **Deploy to cloud**: Use Kubernetes configs for production
4. **Extend features**: Recording, analytics, multi-camera, etc.

## Getting Help

- 📖 Read the full [README](README.md)
- 🏗️ Check [Architecture docs](ARCHITECTURE.md)
- 🐛 Report issues on GitHub
- 💬 Start a discussion for questions

Happy coding! 🚀

