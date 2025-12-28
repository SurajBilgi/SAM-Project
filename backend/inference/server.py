"""
gRPC Inference Server.

Handles:
- Single frame inference
- Streaming inference
- Health checks
"""
import grpc
from concurrent import futures
import sys
import os
import time
import numpy as np
import cv2
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from common import setup_logging
from sam_model import SAMSegmentationModel
import inference_pb2
import inference_pb2_grpc


logger = setup_logging("inference-server", os.getenv("LOG_LEVEL", "INFO"))


class InferenceServicer(inference_pb2_grpc.InferenceServiceServicer):
    """
    gRPC service implementation for inference.
    """
    
    def __init__(self):
        """Initialize the inference servicer."""
        # Load SAM model
        model_version = os.getenv("MODEL_VERSION", "sam-vit-b")
        device = os.getenv("DEVICE", "cpu")
        checkpoint = os.getenv("SAM_CHECKPOINT", None)
        
        self.model = SAMSegmentationModel(
            model_version=model_version,
            device=device,
            checkpoint_path=checkpoint,
            points_per_side=12,  # Lower for faster inference
        )
        
        self.total_inferences = 0
        self.start_time = time.time()
        
        logger.info("InferenceServicer initialized with SAM")
    
    def Infer(self, request, context):
        """
        Single frame inference.
        
        Args:
            request: InferenceRequest
            context: gRPC context
        
        Returns:
            InferenceResponse
        """
        try:
            logger.debug(f"Inference request for session {request.session_id}, frame {request.frame_id}")
            
            # Decode frame
            frame = self._decode_frame(request.frame_data, request.width, request.height)
            
            if frame is None:
                return inference_pb2.InferenceResponse(
                    session_id=request.session_id,
                    frame_id=request.frame_id,
                    timestamp=int(time.time() * 1000),
                    success=False,
                    error_message="Failed to decode frame",
                    model_version=self.model.model_version,
                )
            
            # Run SAM segmentation
            masks, inference_time = self.model.generate_masks(frame)
            
            # Convert masks to protobuf
            proto_masks = []
            for mask_data in masks:
                # Encode mask as PNG for efficient transfer
                mask_binary = mask_data['segmentation'].astype(np.uint8) * 255
                _, mask_encoded = cv2.imencode('.png', mask_binary)
                mask_bytes = mask_encoded.tobytes()
                
                # Extract bounding box
                bbox = mask_data['bbox']  # [x, y, w, h]
                h, w = mask_data['segmentation'].shape
                
                proto_bbox = inference_pb2.BoundingBox(
                    x=float(bbox[0]) / w,
                    y=float(bbox[1]) / h,
                    width=float(bbox[2]) / w,
                    height=float(bbox[3]) / h,
                    confidence=float(mask_data.get('predicted_iou', 0.9)),
                    class_id=0,
                    class_name="object",
                )
                
                proto_mask = inference_pb2.SegmentationMask(
                    mask_data=mask_bytes,
                    width=w,
                    height=h,
                    confidence=float(mask_data.get('predicted_iou', 0.9)),
                    bbox=proto_bbox,
                    area=int(mask_data['area']),
                )
                proto_masks.append(proto_mask)
            
            self.total_inferences += 1
            
            return inference_pb2.InferenceResponse(
                session_id=request.session_id,
                frame_id=request.frame_id,
                timestamp=int(time.time() * 1000),
                masks=proto_masks,
                inference_time_ms=inference_time,
                model_version=self.model.model_version,
                success=True,
                error_message="",
            )
            
        except Exception as e:
            logger.error(f"Inference error: {e}")
            return inference_pb2.InferenceResponse(
                session_id=request.session_id,
                frame_id=request.frame_id,
                timestamp=int(time.time() * 1000),
                success=False,
                error_message=str(e),
                model_version=self.model.model_version,
            )
    
    def StreamInfer(self, request_iterator, context):
        """
        Streaming inference for multiple frames.
        
        Args:
            request_iterator: Stream of InferenceRequest
            context: gRPC context
        
        Yields:
            InferenceResponse for each frame
        """
        for request in request_iterator:
            response = self.Infer(request, context)
            yield response
    
    def HealthCheck(self, request, context):
        """
        Health check endpoint.
        
        Args:
            request: HealthCheckRequest
            context: gRPC context
        
        Returns:
            HealthCheckResponse
        """
        uptime = time.time() - self.start_time
        
        return inference_pb2.HealthCheckResponse(
            status="healthy",
            version=self.model.model_version,
            timestamp=int(time.time() * 1000),
        )
    
    def _decode_frame(self, frame_data: bytes, width: int, height: int) -> np.ndarray:
        """
        Decode frame from bytes.
        
        Args:
            frame_data: Encoded frame bytes
            width: Frame width
            height: Frame height
        
        Returns:
            Decoded frame as numpy array or None
        """
        try:
            # Decode from JPEG/PNG
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                # Try raw decoding if encoded decode fails
                frame = np.frombuffer(frame_data, dtype=np.uint8).reshape(height, width, 3)
            
            return frame
        except Exception as e:
            logger.error(f"Failed to decode frame: {e}")
            return None


def serve():
    """Start the gRPC server."""
    port = os.getenv("PORT", "50051")
    max_workers = int(os.getenv("MAX_WORKERS", "10"))
    
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=max_workers),
        options=[
            ('grpc.max_send_message_length', 50 * 1024 * 1024),  # 50MB
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),  # 50MB
        ],
    )
    
    inference_pb2_grpc.add_InferenceServiceServicer_to_server(
        InferenceServicer(), server
    )
    
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    
    logger.info(f"Inference server started on port {port}")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down inference server...")
        server.stop(0)


if __name__ == '__main__':
    serve()

