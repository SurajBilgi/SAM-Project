"""
Inference routes for demo/testing.
"""
from fastapi import APIRouter
import sys
import os
import base64
import numpy as np
import cv2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from common import setup_logging

logger = setup_logging("inference-routes", os.getenv("LOG_LEVEL", "INFO"))
router = APIRouter()


@router.post("/demo-masks")
async def generate_demo_masks():
    """
    Generate demo segmentation masks for testing.
    
    Returns dummy masks that can be displayed immediately.
    """
    # Generate 3 demo masks
    masks = []
    
    # Create a 640x480 dummy mask
    width, height = 640, 480
    
    for i in range(3):
        # Create binary mask
        mask = np.zeros((height, width), dtype=np.uint8)
        
        # Random position and size
        mask_w = int(width * np.random.uniform(0.2, 0.4))
        mask_h = int(height * np.random.uniform(0.2, 0.4))
        x = int(np.random.uniform(0, width - mask_w))
        y = int(np.random.uniform(0, height - mask_h))
        
        # Draw ellipse
        center = (x + mask_w // 2, y + mask_h // 2)
        axes = (mask_w // 2, mask_h // 2)
        cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
        
        # Encode as PNG
        _, buffer = cv2.imencode('.png', mask)
        mask_b64 = base64.b64encode(buffer).decode('utf-8')
        
        masks.append({
            "mask_data": mask_b64,
            "width": width,
            "height": height,
            "confidence": float(np.random.uniform(0.8, 0.95)),
            "bbox": {
                "x": float(x) / width,
                "y": float(y) / height,
                "width": float(mask_w) / width,
                "height": float(mask_h) / height,
                "confidence": 0.9,
                "class_id": 0,
                "class_name": "object"
            },
            "area": int(np.sum(mask > 0))
        })
    
    return {
        "masks": masks,
        "inference_time_ms": 15.0,
        "model_version": "demo"
    }

