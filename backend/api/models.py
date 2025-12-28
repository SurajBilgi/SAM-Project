"""
API service models and session management.
"""
from typing import Dict, Optional
from datetime import datetime
import time
import sys
import os
from fastapi import WebSocket

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from common import (
    SessionConfig,
    SessionStatus,
    CameraStatus,
    setup_logging,
)


logger = setup_logging("api-models", os.getenv("LOG_LEVEL", "INFO"))


class SessionManager:
    """
    Manages active vision sessions.
    
    Responsibilities:
    - Session lifecycle (create, update, delete)
    - WebSocket connection management
    - Session state tracking
    """
    
    def __init__(self):
        """Initialize session manager."""
        self.sessions: Dict[str, SessionConfig] = {}
        self.session_status: Dict[str, SessionStatus] = {}
        self.websockets: Dict[str, WebSocket] = {}
        self.total_sessions_created = 0
        self.start_time = time.time()
        logger.info("SessionManager initialized")
    
    def create_session(self, config: SessionConfig) -> SessionConfig:
        """
        Create a new vision session.
        
        Args:
            config: Session configuration
        
        Returns:
            Created session configuration
        """
        session_id = config.session_id
        
        if session_id in self.sessions:
            logger.warning(f"Session {session_id} already exists, overwriting")
        
        self.sessions[session_id] = config
        self.session_status[session_id] = SessionStatus(
            session_id=session_id,
            camera_status=CameraStatus.CONNECTING,
            is_streaming=False,
            current_fps=0.0,
            avg_latency_ms=0.0,
            frames_processed=0,
            errors=[],
            last_updated=datetime.utcnow(),
        )
        
        self.total_sessions_created += 1
        logger.info(f"Created session {session_id} with camera {config.camera.camera_id}")
        
        return config
    
    def get_session(self, session_id: str) -> Optional[SessionConfig]:
        """
        Get session configuration by ID.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session configuration or None if not found
        """
        return self.sessions.get(session_id)
    
    def update_session_status(self, session_id: str, status: SessionStatus):
        """
        Update session status.
        
        Args:
            session_id: Session identifier
            status: New session status
        """
        if session_id not in self.sessions:
            logger.warning(f"Attempted to update non-existent session {session_id}")
            return
        
        status.last_updated = datetime.utcnow()
        self.session_status[session_id] = status
        logger.debug(f"Updated status for session {session_id}")
    
    def get_session_status(self, session_id: str) -> Optional[SessionStatus]:
        """
        Get current session status.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session status or None if not found
        """
        return self.session_status.get(session_id)
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and cleanup resources.
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if deleted, False if not found
        """
        if session_id not in self.sessions:
            return False
        
        # Close WebSocket if exists
        if session_id in self.websockets:
            try:
                await self.websockets[session_id].close()
            except Exception as e:
                logger.error(f"Error closing WebSocket for {session_id}: {e}")
            del self.websockets[session_id]
        
        # Remove session data
        del self.sessions[session_id]
        if session_id in self.session_status:
            del self.session_status[session_id]
        
        logger.info(f"Deleted session {session_id}")
        return True
    
    def list_sessions(self) -> Dict[str, SessionConfig]:
        """
        List all active sessions.
        
        Returns:
            Dictionary of session_id -> SessionConfig
        """
        return self.sessions.copy()
    
    def register_websocket(self, session_id: str, websocket: WebSocket):
        """
        Register a WebSocket connection for a session.
        
        Args:
            session_id: Session identifier
            websocket: WebSocket connection
        """
        self.websockets[session_id] = websocket
        logger.info(f"Registered WebSocket for session {session_id}")
    
    def unregister_websocket(self, session_id: str):
        """
        Unregister a WebSocket connection.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.websockets:
            del self.websockets[session_id]
            logger.info(f"Unregistered WebSocket for session {session_id}")
    
    async def send_to_session(self, session_id: str, message: dict):
        """
        Send a message to a session's WebSocket.
        
        Args:
            session_id: Session identifier
            message: Dictionary to send as JSON
        """
        if session_id in self.websockets:
            try:
                await self.websockets[session_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending to session {session_id}: {e}")
                self.unregister_websocket(session_id)
    
    async def cleanup_all(self):
        """Cleanup all sessions and connections."""
        logger.info("Cleaning up all sessions...")
        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            await self.delete_session(session_id)
        logger.info("All sessions cleaned up")
    
    def get_uptime(self) -> float:
        """
        Get service uptime in seconds.
        
        Returns:
            Uptime in seconds
        """
        return time.time() - self.start_time

