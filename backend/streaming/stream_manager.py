"""
Stream Manager - Orchestrates frame capture and distribution.

Manages multiple concurrent streams with backpressure handling.
"""
import asyncio
from typing import Dict, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from common import setup_logging, StreamMetrics, CameraType
from rtsp_reader import RTSPReader
from frame_bus import FrameBus


logger = setup_logging("stream-manager", os.getenv("LOG_LEVEL", "INFO"))


class StreamManager:
    """
    Manages multiple video streams and their lifecycles.
    
    Responsibilities:
    - Create and destroy stream readers
    - Coordinate frame flow to inference
    - Track metrics per stream
    - Handle stream failures and reconnection
    """
    
    def __init__(self):
        """Initialize stream manager."""
        self.streams: Dict[str, RTSPReader] = {}
        self.stream_tasks: Dict[str, asyncio.Task] = {}
        self.frame_bus = FrameBus()
        self.is_running = False
        self.total_frames_processed = 0
        logger.info("StreamManager initialized")
    
    async def start(self):
        """Start the stream manager."""
        self.is_running = True
        await self.frame_bus.start()
        logger.info("StreamManager started")
    
    async def stop(self):
        """Stop the stream manager and all streams."""
        self.is_running = False
        
        # Stop all active streams
        session_ids = list(self.streams.keys())
        for session_id in session_ids:
            await self.stop_stream(session_id)
        
        await self.frame_bus.stop()
        logger.info("StreamManager stopped")
    
    async def start_stream(self, session_id: str, camera_config: dict):
        """
        Start a new stream for a session.
        
        Args:
            session_id: Session identifier
            camera_config: Camera configuration dictionary
        """
        if session_id in self.streams:
            logger.warning(f"Stream {session_id} already exists, stopping it first")
            await self.stop_stream(session_id)
        
        camera_type = camera_config.get("camera_type", "webcam")
        camera_url = camera_config.get("url")
        fps = camera_config.get("fps", 30)
        
        logger.info(f"Starting {camera_type} stream for session {session_id}")
        
        # Create appropriate reader based on camera type
        if camera_type in ["rtsp", "http"]:
            if not camera_url:
                raise ValueError(f"{camera_type} camera requires URL")
            
            reader = RTSPReader(
                session_id=session_id,
                url=camera_url,
                fps=fps,
                username=camera_config.get("username"),
                password=camera_config.get("password"),
            )
        elif camera_type == "webcam":
            # For webcam, use device index 0
            reader = RTSPReader(
                session_id=session_id,
                url="0",  # Device index for webcam
                fps=fps,
                is_webcam=True,
            )
        else:
            raise ValueError(f"Unsupported camera type: {camera_type}")
        
        self.streams[session_id] = reader
        
        # Start reading frames in background task
        task = asyncio.create_task(self._stream_loop(session_id, reader))
        self.stream_tasks[session_id] = task
        
        logger.info(f"Stream {session_id} started successfully")
    
    async def stop_stream(self, session_id: str):
        """
        Stop a stream for a session.
        
        Args:
            session_id: Session identifier
        """
        if session_id not in self.streams:
            raise ValueError(f"Stream {session_id} not found")
        
        logger.info(f"Stopping stream {session_id}")
        
        # Cancel the stream task
        if session_id in self.stream_tasks:
            self.stream_tasks[session_id].cancel()
            try:
                await self.stream_tasks[session_id]
            except asyncio.CancelledError:
                pass
            del self.stream_tasks[session_id]
        
        # Stop the reader
        reader = self.streams[session_id]
        await reader.stop()
        
        del self.streams[session_id]
        logger.info(f"Stream {session_id} stopped")
    
    async def _stream_loop(self, session_id: str, reader: RTSPReader):
        """
        Main loop for processing frames from a stream.
        
        Args:
            session_id: Session identifier
            reader: Stream reader instance
        """
        try:
            await reader.start()
            
            frame_id = 0
            while self.is_running:
                # Read frame
                frame = await reader.read_frame()
                
                if frame is None:
                    # No frame available, handle based on reader state
                    if not reader.is_connected:
                        logger.warning(f"Stream {session_id} disconnected, attempting reconnect...")
                        await asyncio.sleep(1)
                        continue
                    else:
                        # Just wait a bit for next frame
                        await asyncio.sleep(0.01)
                        continue
                
                # Publish frame to bus
                frame_id += 1
                await self.frame_bus.publish_frame(session_id, frame_id, frame)
                self.total_frames_processed += 1
                
                # Small delay to control frame rate
                await asyncio.sleep(1.0 / reader.fps)
                
        except asyncio.CancelledError:
            logger.info(f"Stream loop for {session_id} cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in stream loop for {session_id}: {e}")
            # TODO: Notify API service about stream failure
    
    def get_stream_metrics(self, session_id: str) -> Optional[StreamMetrics]:
        """
        Get metrics for a specific stream.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Stream metrics or None if not found
        """
        if session_id not in self.streams:
            return None
        
        reader = self.streams[session_id]
        return StreamMetrics(
            fps=reader.get_current_fps(),
            latency_ms=reader.get_average_latency(),
            dropped_frames=reader.dropped_frames,
            total_frames=reader.total_frames,
        )
    
    def get_active_stream_count(self) -> int:
        """
        Get number of active streams.
        
        Returns:
            Number of active streams
        """
        return len(self.streams)

