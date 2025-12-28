"""
Main FastAPI application - Control Plane for Real-Time Vision Platform.

This service orchestrates:
- Session management
- Camera registration and configuration
- Stream coordination
- Health monitoring
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from common import setup_logging, HealthCheck
from routes import camera, session, inference
from models import SessionManager


# Global state
session_manager = SessionManager()
logger = setup_logging("api-service", os.getenv("LOG_LEVEL", "INFO"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting API service...")
    yield
    logger.info("Shutting down API service...")
    # Cleanup sessions
    await session_manager.cleanup_all()


# Initialize FastAPI app
app = FastAPI(
    title="Real-Time Vision Platform API",
    description="Control plane for real-time computer vision streaming and inference",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(camera.router, prefix="/api/v1/camera", tags=["Camera"])
app.include_router(session.router, prefix="/api/v1/session", tags=["Session"])
app.include_router(inference.router, prefix="/api/v1/inference", tags=["Inference"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Real-Time Vision Platform API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Health check endpoint for load balancers and orchestrators.
    
    Returns:
        HealthCheck model with service status
    """
    # Check if critical dependencies are accessible
    status = "healthy"
    details = {
        "active_sessions": len(session_manager.sessions),
        "inference_service": "connected",  # TODO: Add actual health check
        "streaming_service": "connected",  # TODO: Add actual health check
    }
    
    try:
        # Basic health validation
        if len(session_manager.sessions) > 100:  # Arbitrary limit
            status = "degraded"
            details["warning"] = "High number of active sessions"
    except Exception as e:
        status = "unhealthy"
        details["error"] = str(e)
        logger.error(f"Health check failed: {e}")
    
    return HealthCheck(
        status=status,
        service="api-service",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        details=details,
    )


@app.get("/metrics")
async def metrics():
    """
    Metrics endpoint for monitoring systems.
    
    Returns:
        Dictionary of current metrics
    """
    return {
        "active_sessions": len(session_manager.sessions),
        "total_sessions_created": session_manager.total_sessions_created,
        "uptime_seconds": session_manager.get_uptime(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time communication.
    
    Sends:
    - Inference results
    - Stream status updates
    - Metrics
    
    Args:
        websocket: WebSocket connection
        session_id: Session identifier
    """
    await websocket.accept()
    logger.info(f"WebSocket connection established for session {session_id}")
    
    try:
        # Register websocket with session
        if session_id not in session_manager.sessions:
            await websocket.send_json({
                "error": f"Session {session_id} not found"
            })
            await websocket.close()
            return
        
        session_manager.register_websocket(session_id, websocket)
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            # Handle control messages if needed
            logger.debug(f"Received message from {session_id}: {data}")
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
        session_manager.unregister_websocket(session_id)
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        session_manager.unregister_websocket(session_id)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )

