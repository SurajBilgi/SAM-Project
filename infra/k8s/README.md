# Kubernetes Deployment Guide

This directory contains Kubernetes manifests for deploying the Real-Time Vision Platform.

## Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Docker images built and available
- (Optional) Ingress controller (nginx-ingress)
- (Optional) Metrics server for HPA

## Quick Deployment

### 1. Build Docker Images

```bash
# From project root
docker build -t vision-platform/api:latest backend/api/
docker build -t vision-platform/streaming:latest backend/streaming/
docker build -t vision-platform/inference:latest backend/inference/
docker build -t vision-platform/frontend:latest frontend/
```

### 2. Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f namespace.yaml

# Apply configurations
kubectl apply -f configmap.yaml

# Deploy services
kubectl apply -f api-deployment.yaml
kubectl apply -f api-service.yaml
kubectl apply -f streaming-deployment.yaml
kubectl apply -f streaming-service.yaml
kubectl apply -f inference-deployment.yaml
kubectl apply -f inference-service.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f frontend-service.yaml

# Enable autoscaling
kubectl apply -f hpa.yaml

# (Optional) Setup ingress
kubectl apply -f ingress.yaml
```

Or deploy everything at once:

```bash
kubectl apply -f .
```

### 3. Verify Deployment

```bash
# Check pods
kubectl get pods -n vision-platform

# Check services
kubectl get services -n vision-platform

# Check HPA
kubectl get hpa -n vision-platform

# View logs
kubectl logs -f deployment/api-deployment -n vision-platform
```

### 4. Access the Application

```bash
# Get LoadBalancer external IP for frontend
kubectl get svc frontend-service -n vision-platform

# Or use port forwarding for local testing
kubectl port-forward svc/frontend-service 3000:80 -n vision-platform
```

Then access: http://localhost:3000

## Configuration

### ConfigMap

Edit `configmap.yaml` to modify:
- Log levels
- Service URLs
- Model versions
- FPS limits
- Device types (cpu/cuda)

### Resource Limits

Edit deployment files to adjust:
- CPU/Memory requests and limits
- Replica counts
- GPU allocation (inference-deployment.yaml)

### Autoscaling

Edit `hpa.yaml` to configure:
- Min/Max replicas
- CPU/Memory thresholds
- Scale up/down behavior

## GPU Support

To enable GPU for inference:

1. Ensure your cluster has GPU nodes
2. Install NVIDIA device plugin:
```bash
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/master/nvidia-device-plugin.yml
```

3. Uncomment GPU sections in `inference-deployment.yaml`:
```yaml
resources:
  limits:
    nvidia.com/gpu: 1
nodeSelector:
  accelerator: nvidia-tesla-t4
```

## Monitoring

### Logs

```bash
# API logs
kubectl logs -f deployment/api-deployment -n vision-platform

# Streaming logs
kubectl logs -f deployment/streaming-deployment -n vision-platform

# Inference logs
kubectl logs -f deployment/inference-deployment -n vision-platform
```

### Metrics

```bash
# Pod metrics
kubectl top pods -n vision-platform

# Node metrics
kubectl top nodes
```

## Troubleshooting

### Pods not starting

```bash
kubectl describe pod <pod-name> -n vision-platform
kubectl logs <pod-name> -n vision-platform
```

### Service not reachable

```bash
kubectl get endpoints -n vision-platform
kubectl describe service <service-name> -n vision-platform
```

### HPA not scaling

```bash
kubectl describe hpa <hpa-name> -n vision-platform
kubectl get --raw /apis/metrics.k8s.io/v1beta1/nodes
```

## Clean Up

```bash
# Delete all resources
kubectl delete namespace vision-platform

# Or delete individually
kubectl delete -f .
```

## Production Considerations

1. **Secrets Management**: Use Kubernetes Secrets or external secret managers for sensitive data
2. **TLS/SSL**: Configure TLS in ingress.yaml for HTTPS
3. **Resource Limits**: Tune based on actual workload
4. **Persistent Storage**: Add PVCs if model weights need persistence
5. **Network Policies**: Implement network policies for security
6. **Monitoring**: Integrate with Prometheus/Grafana
7. **Logging**: Ship logs to centralized logging (ELK, Loki)
8. **Backup**: Regular etcd backups
9. **High Availability**: Multi-zone deployment for production

## Advanced Configuration

### Custom Domains

Update `ingress.yaml` with your domain:
```yaml
- host: your-domain.com
```

### SSL Certificates

1. Create TLS secret:
```bash
kubectl create secret tls vision-platform-tls \
  --cert=path/to/cert.crt \
  --key=path/to/cert.key \
  -n vision-platform
```

2. Uncomment TLS section in ingress.yaml

### Database Integration

Add StatefulSet for databases if needed:
- PostgreSQL for session metadata
- Redis for caching
- MinIO for frame storage

## Support

For issues or questions:
- Check logs: `kubectl logs`
- Describe resources: `kubectl describe`
- Review events: `kubectl get events -n vision-platform`

