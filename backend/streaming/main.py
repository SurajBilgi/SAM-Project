"""
Streaming Service - Frame Ingestion and Distribution.

Responsibilities:
- Capture frames from webcams and IP cameras
- Handle RTSP/HTTP stream ingestion
- Manage frame pipeline with backpressure
- Forward frames to inference service
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from common import setup_logging, HealthCheck
from stream_manager import StreamManager


# Global state
stream_manager = StreamManager()
logger = setup_logging("streaming-service", os.getenv("LOG_LEVEL", "INFO"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Streaming service...")
    await stream_manager.start()
    yield
    logger.info("Shutting down Streaming service...")
    await stream_manager.stop()


# Initialize FastAPI app
app = FastAPI(
    title="Real-Time Vision Platform - Streaming Service",
    description="Frame ingestion and distribution service",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Streaming Service",
        "version": "1.0.0",
        "status": "operational",
    }


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        HealthCheck model with service status
    """
    status_value = "healthy"
    details = {
        "active_streams": stream_manager.get_active_stream_count(),
        "total_frames_processed": stream_manager.total_frames_processed,
    }
    
    try:
        # Check if manager is operational
        if not stream_manager.is_running:
            status_value = "unhealthy"
            details["error"] = "Stream manager not running"
    except Exception as e:
        status_value = "unhealthy"
        details["error"] = str(e)
        logger.error(f"Health check failed: {e}")
    
    return HealthCheck(
        status=status_value,
        service="streaming-service",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        details=details,
    )


@app.post("/stream/start/{session_id}")
async def start_stream(session_id: str, camera_config: dict):
    """
    Start streaming for a session.
    
    Args:
        session_id: Session identifier
        camera_config: Camera configuration dictionary
    
    Returns:
        Success message
    """
    logger.info(f"Starting stream for session {session_id}")
    
    try:
        await stream_manager.start_stream(session_id, camera_config)
        return {
            "session_id": session_id,
            "status": "streaming",
            "message": "Stream started successfully",
        }
    except Exception as e:
        logger.error(f"Failed to start stream for {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start stream: {str(e)}",
        )


@app.post("/stream/stop/{session_id}")
async def stop_stream(session_id: str):
    """
    Stop streaming for a session.
    
    Args:
        session_id: Session identifier
    
    Returns:
        Success message
    """
    logger.info(f"Stopping stream for session {session_id}")
    
    try:
        await stream_manager.stop_stream(session_id)
        return {
            "session_id": session_id,
            "status": "stopped",
            "message": "Stream stopped successfully",
        }
    except Exception as e:
        logger.error(f"Failed to stop stream for {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stream not found: {str(e)}",
        )


@app.get("/stream/status/{session_id}")
async def get_stream_status(session_id: str):
    """
    Get streaming status for a session.
    
    Args:
        session_id: Session identifier
    
    Returns:
        Stream status and metrics
    """
    try:
        metrics = stream_manager.get_stream_metrics(session_id)
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stream {session_id} not found",
            )
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get stream status for {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stream status: {str(e)}",
        )


@app.get("/metrics")
async def metrics():
    """
    Get service-wide metrics.
    
    Returns:
        Dictionary of current metrics
    """
    return {
        "active_streams": stream_manager.get_active_stream_count(),
        "total_frames_processed": stream_manager.total_frames_processed,
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8001")),
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )

