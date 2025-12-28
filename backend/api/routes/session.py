"""
Session management routes.

Handles:
- Session creation
- Session status monitoring
- Session lifecycle management
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from common import (
    SessionConfig,
    SessionStatus,
    CameraConfig,
    setup_logging,
    generate_session_id,
)
from models import SessionManager


logger = setup_logging("session-routes", os.getenv("LOG_LEVEL", "INFO"))
router = APIRouter()


# Dependency to get session manager
# In production, this would be injected properly
_session_manager: SessionManager = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


@router.post("/create", response_model=SessionConfig, status_code=status.HTTP_201_CREATED)
async def create_session(camera: CameraConfig):
    """
    Create a new vision session.
    
    Args:
        camera: Camera configuration for the session
    
    Returns:
        Created session configuration
    """
    session_id = generate_session_id()
    logger.info(f"Creating session {session_id} with camera {camera.camera_id}")
    
    config = SessionConfig(
        session_id=session_id,
        camera=camera,
        enable_inference=True,
        max_latency_ms=200,
        created_at=datetime.utcnow(),
    )
    
    manager = get_session_manager()
    created_config = manager.create_session(config)
    
    # TODO: Notify streaming service to start ingestion
    # This would make an async HTTP call to the streaming service
    
    logger.info(f"Session {session_id} created successfully")
    return created_config


@router.get("/{session_id}", response_model=SessionConfig)
async def get_session(session_id: str):
    """
    Get session configuration.
    
    Args:
        session_id: Session identifier
    
    Returns:
        Session configuration
    
    Raises:
        HTTPException: If session not found
    """
    logger.info(f"Getting session {session_id}")
    
    manager = get_session_manager()
    config = manager.get_session(session_id)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    return config


@router.get("/{session_id}/status", response_model=SessionStatus)
async def get_session_status(session_id: str):
    """
    Get current session status.
    
    Args:
        session_id: Session identifier
    
    Returns:
        Current session status
    
    Raises:
        HTTPException: If session not found
    """
    logger.info(f"Getting status for session {session_id}")
    
    manager = get_session_manager()
    status_obj = manager.get_session_status(session_id)
    
    if not status_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    return status_obj


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str):
    """
    Delete a session and stop streaming.
    
    Args:
        session_id: Session identifier
    
    Raises:
        HTTPException: If session not found
    """
    logger.info(f"Deleting session {session_id}")
    
    manager = get_session_manager()
    deleted = await manager.delete_session(session_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    # TODO: Notify streaming service to stop ingestion
    
    logger.info(f"Session {session_id} deleted successfully")


@router.get("/", response_model=List[SessionConfig])
async def list_sessions():
    """
    List all active sessions.
    
    Returns:
        List of active session configurations
    """
    logger.info("Listing all active sessions")
    
    manager = get_session_manager()
    sessions = manager.list_sessions()
    
    return list(sessions.values())


@router.post("/{session_id}/start")
async def start_session(session_id: str):
    """
    Start streaming for a session.
    
    Args:
        session_id: Session identifier
    
    Returns:
        Success message
    
    Raises:
        HTTPException: If session not found
    """
    logger.info(f"Starting session {session_id}")
    
    manager = get_session_manager()
    config = manager.get_session(session_id)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    # TODO: Notify streaming service to start
    
    return {
        "session_id": session_id,
        "status": "started",
        "message": "Streaming started successfully",
    }


@router.post("/{session_id}/stop")
async def stop_session(session_id: str):
    """
    Stop streaming for a session (without deleting).
    
    Args:
        session_id: Session identifier
    
    Returns:
        Success message
    
    Raises:
        HTTPException: If session not found
    """
    logger.info(f"Stopping session {session_id}")
    
    manager = get_session_manager()
    config = manager.get_session(session_id)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )
    
    # TODO: Notify streaming service to stop
    
    return {
        "session_id": session_id,
        "status": "stopped",
        "message": "Streaming stopped successfully",
    }

