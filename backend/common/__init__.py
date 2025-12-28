"""
Common utilities and models shared across backend services.
"""
from .models import (
    CameraType,
    CameraStatus,
    BoundingBox,
    InferenceResult,
    CameraConfig,
    SessionConfig,
    SessionStatus,
    HealthCheck,
    FrameMetadata,
    StreamMetrics,
)
from .utils import (
    setup_logging,
    generate_session_id,
    generate_camera_id,
    timing_context,
    LatencyTracker,
    FPSCounter,
    validate_rtsp_url,
    validate_http_url,
)

__all__ = [
    "CameraType",
    "CameraStatus",
    "BoundingBox",
    "InferenceResult",
    "CameraConfig",
    "SessionConfig",
    "SessionStatus",
    "HealthCheck",
    "FrameMetadata",
    "StreamMetrics",
    "setup_logging",
    "generate_session_id",
    "generate_camera_id",
    "timing_context",
    "LatencyTracker",
    "FPSCounter",
    "validate_rtsp_url",
    "validate_http_url",
]

