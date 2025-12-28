"""
Shared data models used across backend services.
These Pydantic models ensure type safety and validation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum


class CameraType(str, Enum):
    """Supported camera types."""
    WEBCAM = "webcam"
    RTSP = "rtsp"
    HTTP = "http"


class CameraStatus(str, Enum):
    """Camera connection status."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"


class BoundingBox(BaseModel):
    """Bounding box for object detection."""
    x: float = Field(..., description="Top-left x coordinate (normalized 0-1)")
    y: float = Field(..., description="Top-left y coordinate (normalized 0-1)")
    width: float = Field(..., description="Box width (normalized 0-1)")
    height: float = Field(..., description="Box height (normalized 0-1)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    class_id: int = Field(..., description="Object class ID")
    class_name: str = Field(..., description="Human-readable class name")


class SegmentationMask(BaseModel):
    """Segmentation mask."""
    mask_data: bytes = Field(..., description="Encoded mask (PNG)")
    width: int
    height: int
    confidence: float
    bbox: BoundingBox
    area: int


class InferenceResult(BaseModel):
    """Result from inference service."""
    session_id: str
    frame_id: int
    timestamp: datetime
    detections: List[BoundingBox] = []
    masks: List[SegmentationMask] = []
    inference_time_ms: float = Field(..., description="Time spent in inference (ms)")
    model_version: str
    fps: Optional[float] = None


class CameraConfig(BaseModel):
    """Configuration for a camera source."""
    camera_id: str = Field(..., description="Unique camera identifier")
    camera_type: CameraType
    url: Optional[str] = Field(None, description="Camera stream URL (for RTSP/HTTP)")
    username: Optional[str] = Field(None, description="Camera authentication username")
    password: Optional[str] = Field(None, description="Camera authentication password")
    fps: int = Field(30, ge=1, le=60, description="Target frames per second")
    resolution: Optional[str] = Field("1280x720", description="Target resolution")


class SessionConfig(BaseModel):
    """Configuration for a vision session."""
    session_id: str = Field(..., description="Unique session identifier")
    camera: CameraConfig
    enable_inference: bool = Field(True, description="Enable CV inference")
    max_latency_ms: int = Field(200, description="Maximum acceptable latency")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SessionStatus(BaseModel):
    """Current status of a vision session."""
    session_id: str
    camera_status: CameraStatus
    is_streaming: bool
    current_fps: Optional[float] = None
    avg_latency_ms: Optional[float] = None
    frames_processed: int = 0
    errors: List[str] = []
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class HealthCheck(BaseModel):
    """Health check response."""
    status: Literal["healthy", "degraded", "unhealthy"]
    service: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[dict] = None


class FrameMetadata(BaseModel):
    """Metadata for a video frame."""
    session_id: str
    frame_id: int
    timestamp: datetime
    width: int
    height: int
    format: str = "bgr24"


class StreamMetrics(BaseModel):
    """Real-time streaming metrics."""
    fps: float
    latency_ms: float
    dropped_frames: int
    total_frames: int
    bitrate_kbps: Optional[float] = None

