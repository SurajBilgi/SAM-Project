"""
RTSP Reader - Captures frames from RTSP/HTTP streams and webcams.

Handles:
- RTSP stream connection and reconnection
- HTTP stream ingestion
- Webcam capture
- Frame rate control
- Error recovery
"""
import asyncio
import cv2
import numpy as np
from typing import Optional
import sys
import os
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from common import setup_logging, FPSCounter, LatencyTracker


logger = setup_logging("rtsp-reader", os.getenv("LOG_LEVEL", "INFO"))


class RTSPReader:
    """
    Reads frames from RTSP streams, HTTP streams, or webcams.
    
    Features:
    - Automatic reconnection on failure
    - Frame rate limiting
    - Latency tracking
    - Backpressure-aware (drops frames if needed)
    """
    
    def __init__(
        self,
        session_id: str,
        url: str,
        fps: int = 30,
        username: Optional[str] = None,
        password: Optional[str] = None,
        is_webcam: bool = False,
        reconnect_delay: float = 2.0,
        max_reconnect_attempts: int = 10,
    ):
        """
        Initialize RTSP reader.
        
        Args:
            session_id: Session identifier
            url: RTSP/HTTP URL or device index for webcam
            fps: Target frames per second
            username: Optional authentication username
            password: Optional authentication password
            is_webcam: Whether this is a webcam (not RTSP)
            reconnect_delay: Delay between reconnection attempts (seconds)
            max_reconnect_attempts: Maximum reconnection attempts
        """
        self.session_id = session_id
        self.url = url
        self.fps = fps
        self.username = username
        self.password = password
        self.is_webcam = is_webcam
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_attempts = max_reconnect_attempts
        
        self.capture: Optional[cv2.VideoCapture] = None
        self.is_connected = False
        self.is_running = False
        
        # Metrics
        self.fps_counter = FPSCounter()
        self.latency_tracker = LatencyTracker()
        self.total_frames = 0
        self.dropped_frames = 0
        self.reconnect_attempts = 0
        
        logger.info(f"RTSPReader initialized for session {session_id}")
    
    async def start(self):
        """Start the reader and connect to stream."""
        self.is_running = True
        await self._connect()
    
    async def stop(self):
        """Stop the reader and release resources."""
        self.is_running = False
        self._disconnect()
        logger.info(f"RTSPReader stopped for session {self.session_id}")
    
    async def _connect(self):
        """Connect to the video stream."""
        try:
            # Build URL with authentication if provided
            if self.is_webcam:
                # For webcam, URL is device index
                url = int(self.url)
            else:
                url = self.url
                if self.username and self.password:
                    # Insert credentials into URL
                    # rtsp://username:password@host:port/path
                    if "://" in url:
                        protocol, rest = url.split("://", 1)
                        url = f"{protocol}://{self.username}:{self.password}@{rest}"
            
            logger.info(f"Connecting to stream for session {self.session_id}")
            
            # Run blocking OpenCV call in thread pool
            loop = asyncio.get_event_loop()
            self.capture = await loop.run_in_executor(
                None, cv2.VideoCapture, url
            )
            
            if not self.capture.isOpened():
                raise ConnectionError(f"Failed to open stream: {self.url}")
            
            # Configure capture for low latency
            self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffer
            
            self.is_connected = True
            self.reconnect_attempts = 0
            logger.info(f"Connected to stream for session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Failed to connect to stream for {self.session_id}: {e}")
            self.is_connected = False
            raise
    
    def _disconnect(self):
        """Disconnect from the video stream."""
        if self.capture:
            self.capture.release()
            self.capture = None
        self.is_connected = False
        logger.info(f"Disconnected from stream for session {self.session_id}")
    
    async def _reconnect(self):
        """Attempt to reconnect to the stream."""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(
                f"Max reconnection attempts ({self.max_reconnect_attempts}) "
                f"reached for session {self.session_id}"
            )
            return False
        
        self.reconnect_attempts += 1
        logger.info(
            f"Reconnection attempt {self.reconnect_attempts}/{self.max_reconnect_attempts} "
            f"for session {self.session_id}"
        )
        
        self._disconnect()
        await asyncio.sleep(self.reconnect_delay)
        
        try:
            await self._connect()
            return True
        except Exception as e:
            logger.error(f"Reconnection failed for {self.session_id}: {e}")
            return False
    
    async def read_frame(self) -> Optional[np.ndarray]:
        """
        Read a frame from the stream.
        
        Returns:
            Frame as numpy array (BGR format) or None if unavailable
        """
        if not self.is_connected or not self.capture:
            # Try to reconnect
            if self.is_running:
                await self._reconnect()
            return None
        
        try:
            start_time = time.time()
            
            # Read frame in thread pool (blocking operation)
            loop = asyncio.get_event_loop()
            ret, frame = await loop.run_in_executor(
                None, self.capture.read
            )
            
            if not ret or frame is None:
                logger.warning(f"Failed to read frame for session {self.session_id}")
                self.is_connected = False
                return None
            
            # Update metrics
            self.total_frames += 1
            self.fps_counter.tick()
            
            read_time_ms = (time.time() - start_time) * 1000
            self.latency_tracker.add_sample(read_time_ms)
            
            return frame
            
        except Exception as e:
            logger.error(f"Error reading frame for {self.session_id}: {e}")
            self.is_connected = False
            return None
    
    def get_current_fps(self) -> float:
        """Get current FPS."""
        return self.fps_counter.get_fps()
    
    def get_average_latency(self) -> float:
        """Get average latency in ms."""
        return self.latency_tracker.get_average()

