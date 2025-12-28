# Contributing to Real-Time Vision Platform

Thank you for considering contributing to this project! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- Git

### Getting Started

1. **Fork and clone the repository**

```bash
git clone https://github.com/yourusername/SAM-Project.git
cd SAM-Project
```

2. **Run the setup script**

```bash
chmod +x scripts/local-dev.sh
./scripts/local-dev.sh
```

3. **Start the development environment**

```bash
docker-compose up
```

## Project Structure

```
├── backend/
│   ├── api/              # FastAPI control plane
│   ├── streaming/        # Frame ingestion service
│   ├── inference/        # CV inference service
│   └── common/           # Shared utilities
├── frontend/             # React TypeScript frontend
├── infra/
│   └── k8s/             # Kubernetes manifests
└── scripts/             # Helper scripts
```

## Coding Standards

### Python (Backend)

- Follow PEP 8 style guide
- Use type hints
- Document functions with docstrings
- Maximum line length: 100 characters
- Use Black for formatting: `black .`
- Use flake8 for linting: `flake8 .`

Example:
```python
def process_frame(frame: np.ndarray, config: FrameConfig) -> ProcessedFrame:
    """
    Process a video frame with the given configuration.
    
    Args:
        frame: Input frame as numpy array
        config: Processing configuration
    
    Returns:
        Processed frame with metadata
    """
    # Implementation
    pass
```

### TypeScript (Frontend)

- Follow ESLint configuration
- Use functional components with hooks
- Props should be typed with interfaces
- Use meaningful variable names
- Maximum line length: 100 characters

Example:
```typescript
interface CameraViewProps {
  sessionId: string
  source: CameraSource
  onStop: () => void
}

function CameraView({ sessionId, source, onStop }: CameraViewProps) {
  // Implementation
}
```

### Git Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit first line to 72 characters
- Reference issues and pull requests when relevant

Examples:
```
Add webcam capture functionality

Implement RTSP stream reconnection logic
Fixes #123

Update Kubernetes deployment configuration
- Increase memory limits
- Add GPU support
- Update HPA thresholds
```

## Testing

### Backend Tests

```bash
# Run all backend tests
cd backend/api && pytest
cd backend/streaming && pytest
cd backend/inference && pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Pull Request Process

1. **Create a feature branch**
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**
   - Write clean, documented code
   - Add tests for new functionality
   - Update documentation if needed

3. **Test your changes**
```bash
make test
```

4. **Commit your changes**
```bash
git add .
git commit -m "Add your descriptive commit message"
```

5. **Push to your fork**
```bash
git push origin feature/your-feature-name
```

6. **Create a Pull Request**
   - Provide a clear description of the changes
   - Link any related issues
   - Ensure CI checks pass
   - Request review from maintainers

## Areas for Contribution

### High Priority

- [ ] Real CV model integration (YOLO, DETR, etc.)
- [ ] WebRTC implementation for low-latency streaming
- [ ] Performance optimizations
- [ ] Comprehensive test coverage
- [ ] Production deployment guides

### Features

- [ ] Multi-camera support
- [ ] Recording and playback
- [ ] Advanced analytics
- [ ] Custom model upload
- [ ] Mobile app
- [ ] LLM reasoning integration

### Documentation

- [ ] API documentation
- [ ] Deployment guides
- [ ] Architecture diagrams
- [ ] Performance tuning guides
- [ ] Troubleshooting guides

### Infrastructure

- [ ] CI/CD pipelines
- [ ] Monitoring and alerting
- [ ] Load testing
- [ ] Security hardening
- [ ] Multi-cloud support

## Code Review Guidelines

### For Contributors

- Keep PRs focused and small
- Respond to feedback constructively
- Update PR based on review comments
- Ensure tests pass before requesting review

### For Reviewers

- Be respectful and constructive
- Focus on code quality and design
- Suggest improvements, don't demand
- Approve when ready, request changes when needed

## Community

- Be respectful and inclusive
- Help others learn and grow
- Share knowledge and experiences
- Follow the code of conduct

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions or ideas
- Check existing issues before creating new ones

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to the Real-Time Vision Platform! 🚀

