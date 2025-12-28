"""
Shared utility functions across backend services.
"""
import logging
import sys
import uuid
import time
from datetime import datetime
from typing import Optional
from contextlib import contextmanager


def setup_logging(service_name: str, log_level: str = "INFO") -> logging.Logger:
    """
    Configure structured JSON logging for the service.
    
    Args:
        service_name: Name of the service for log identification
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Create console handler with structured format
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, log_level.upper()))
    
    # JSON-like structured format for production
    formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "service": "' + service_name + '", '
        '"level": "%(levelname)s", "message": "%(message)s", "module": "%(module)s"}'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger


def generate_session_id() -> str:
    """
    Generate a unique session ID.
    
    Returns:
        UUID-based session identifier
    """
    return f"session-{uuid.uuid4().hex[:16]}"


def generate_camera_id() -> str:
    """
    Generate a unique camera ID.
    
    Returns:
        UUID-based camera identifier
    """
    return f"cam-{uuid.uuid4().hex[:12]}"


@contextmanager
def timing_context(name: str, logger: Optional[logging.Logger] = None):
    """
    Context manager for timing code blocks.
    
    Usage:
        with timing_context("inference", logger):
            result = model.predict(frame)
    
    Args:
        name: Name of the operation being timed
        logger: Optional logger for outputting timing info
    """
    start_time = time.time()
    try:
        yield
    finally:
        elapsed_ms = (time.time() - start_time) * 1000
        if logger:
            logger.debug(f"{name} took {elapsed_ms:.2f}ms")


class LatencyTracker:
    """
    Tracks latency metrics with moving average.
    """
    
    def __init__(self, window_size: int = 100):
        """
        Initialize latency tracker.
        
        Args:
            window_size: Number of samples for moving average
        """
        self.window_size = window_size
        self.latencies = []
        self.total_samples = 0
    
    def add_sample(self, latency_ms: float):
        """Add a latency sample."""
        self.latencies.append(latency_ms)
        self.total_samples += 1
        
        # Keep only recent samples
        if len(self.latencies) > self.window_size:
            self.latencies.pop(0)
    
    def get_average(self) -> float:
        """Get average latency in ms."""
        if not self.latencies:
            return 0.0
        return sum(self.latencies) / len(self.latencies)
    
    def get_p95(self) -> float:
        """Get 95th percentile latency."""
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        index = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[index]
    
    def reset(self):
        """Reset all metrics."""
        self.latencies = []
        self.total_samples = 0


class FPSCounter:
    """
    Tracks frames per second.
    """
    
    def __init__(self, window_seconds: float = 1.0):
        """
        Initialize FPS counter.
        
        Args:
            window_seconds: Time window for FPS calculation
        """
        self.window_seconds = window_seconds
        self.frame_times = []
    
    def tick(self):
        """Register a new frame."""
        current_time = time.time()
        self.frame_times.append(current_time)
        
        # Remove old frames outside the window
        cutoff_time = current_time - self.window_seconds
        self.frame_times = [t for t in self.frame_times if t > cutoff_time]
    
    def get_fps(self) -> float:
        """Get current FPS."""
        if len(self.frame_times) < 2:
            return 0.0
        
        time_span = self.frame_times[-1] - self.frame_times[0]
        if time_span == 0:
            return 0.0
        
        return len(self.frame_times) / time_span
    
    def reset(self):
        """Reset counter."""
        self.frame_times = []


def validate_rtsp_url(url: str) -> bool:
    """
    Validate RTSP URL format.
    
    Args:
        url: RTSP URL to validate
    
    Returns:
        True if valid, False otherwise
    """
    return url.startswith("rtsp://") or url.startswith("rtsps://")


def validate_http_url(url: str) -> bool:
    """
    Validate HTTP URL format.
    
    Args:
        url: HTTP URL to validate
    
    Returns:
        True if valid, False otherwise
    """
    return url.startswith("http://") or url.startswith("https://")

