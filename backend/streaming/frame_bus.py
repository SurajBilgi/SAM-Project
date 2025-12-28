"""
Frame Bus - Distributes frames to inference service.

Implements:
- Async frame queue with backpressure
- Frame distribution to inference service
- Latest-frame-only policy (drops old frames)
"""
import asyncio
from typing import Dict, Optional
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from common import setup_logging


logger = setup_logging("frame-bus", os.getenv("LOG_LEVEL", "INFO"))


class FrameBus:
    """
    Distributes frames from streams to inference service.
    
    Design principles:
    - Always process latest frame (drop old frames if inference is slow)
    - Non-blocking publish
    - Per-session queues
    """
    
    def __init__(self, max_queue_size: int = 2):
        """
        Initialize frame bus.
        
        Args:
            max_queue_size: Maximum frames to buffer per session
        """
        self.max_queue_size = max_queue_size
        self.frame_queues: Dict[str, asyncio.Queue] = {}
        self.is_running = False
        self.processing_tasks: Dict[str, asyncio.Task] = {}
        logger.info("FrameBus initialized")
    
    async def start(self):
        """Start the frame bus."""
        self.is_running = True
        logger.info("FrameBus started")
    
    async def stop(self):
        """Stop the frame bus."""
        self.is_running = False
        
        # Cancel all processing tasks
        for task in self.processing_tasks.values():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self.processing_tasks.clear()
        self.frame_queues.clear()
        logger.info("FrameBus stopped")
    
    async def publish_frame(self, session_id: str, frame_id: int, frame: np.ndarray):
        """
        Publish a frame to the bus.
        
        Args:
            session_id: Session identifier
            frame_id: Frame sequence number
            frame: Frame data as numpy array
        """
        # Create queue for new sessions
        if session_id not in self.frame_queues:
            self.frame_queues[session_id] = asyncio.Queue(maxsize=self.max_queue_size)
            
            # Start processing task for this session
            task = asyncio.create_task(self._process_frames(session_id))
            self.processing_tasks[session_id] = task
        
        queue = self.frame_queues[session_id]
        
        # Non-blocking publish with backpressure handling
        try:
            # If queue is full, remove oldest frame (keep only latest)
            if queue.full():
                try:
                    queue.get_nowait()
                    logger.debug(f"Dropped old frame for session {session_id} (backpressure)")
                except asyncio.QueueEmpty:
                    pass
            
            # Add new frame
            queue.put_nowait((frame_id, frame))
            
        except asyncio.QueueFull:
            logger.warning(f"Failed to publish frame for session {session_id}")
    
    async def _process_frames(self, session_id: str):
        """
        Process frames for a session and call inference service.
        
        Args:
            session_id: Session identifier
        """
        logger.info(f"Started frame processing for session {session_id}")
        
        queue = self.frame_queues[session_id]
        
        # Import here to avoid circular dependencies
        import httpx
        import cv2
        import base64
        
        try:
            while self.is_running:
                try:
                    # Wait for frame with timeout
                    frame_id, frame = await asyncio.wait_for(
                        queue.get(),
                        timeout=1.0,
                    )
                    
                    logger.debug(
                        f"Processing frame {frame_id} for session {session_id} "
                        f"(shape: {frame.shape})"
                    )
                    
                    # Encode frame as JPEG for inference
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    frame_bytes = buffer.tobytes()
                    frame_b64 = base64.b64encode(frame_bytes).decode('utf-8')
                    
                    # Send to API service (which will handle inference results)
                    try:
                        async with httpx.AsyncClient(timeout=5.0) as client:
                            # Send frame data to API for inference
                            response = await client.post(
                                f"http://api:8000/api/v1/inference/process",
                                json={
                                    "session_id": session_id,
                                    "frame_id": frame_id,
                                    "frame_data": frame_b64,
                                    "width": frame.shape[1],
                                    "height": frame.shape[0],
                                }
                            )
                            if response.status_code == 200:
                                logger.debug(f"Frame {frame_id} processed successfully")
                    except Exception as e:
                        logger.error(f"Failed to send frame to API: {e}")
                    
                except asyncio.TimeoutError:
                    # No frames available, continue
                    continue
                    
        except asyncio.CancelledError:
            logger.info(f"Frame processing cancelled for session {session_id}")
            raise
        except Exception as e:
            logger.error(f"Error processing frames for session {session_id}: {e}")
    
    async def unsubscribe(self, session_id: str):
        """
        Unsubscribe a session from the bus.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.processing_tasks:
            self.processing_tasks[session_id].cancel()
            try:
                await self.processing_tasks[session_id]
            except asyncio.CancelledError:
                pass
            del self.processing_tasks[session_id]
        
        if session_id in self.frame_queues:
            del self.frame_queues[session_id]
        
        logger.info(f"Session {session_id} unsubscribed from frame bus")

