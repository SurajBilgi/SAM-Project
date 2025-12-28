# Multi-stage build for streaming service
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
COPY streaming/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# Production stage
FROM python:3.11-slim

# Install runtime dependencies for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN useradd -m -u 1000 streamuser

# Set working directory
WORKDIR /app

# Copy common module first
COPY common /app/common

# Copy application code
COPY streaming /app

# Set ownership
RUN chown -R streamuser:streamuser /app

# Switch to non-root user
USER streamuser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run application
CMD ["python", "main.py"]

