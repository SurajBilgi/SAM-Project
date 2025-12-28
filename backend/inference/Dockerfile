# Multi-stage build for inference service
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install
COPY inference/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN useradd -m -u 1000 inferuser

# Set working directory
WORKDIR /app

# Copy common module first
COPY common /app/common

# Copy application code
COPY inference /app

# Compile protobuf (if not already compiled)
RUN chmod +x compile_protos.sh && ./compile_protos.sh || true

# Set ownership
RUN chown -R inferuser:inferuser /app

# Switch to non-root user
USER inferuser

# Expose gRPC port
EXPOSE 50051

# Health check (gRPC requires special client)
# Using a simple port check as fallback
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('localhost', 50051)); s.close()" || exit 1

# Run application
CMD ["python", "server.py"]

