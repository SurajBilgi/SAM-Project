"""
Segment Anything Model (SAM) integration for real-time segmentation.

This replaces the stub model with actual SAM inference.
"""
import numpy as np
import time
import torch
import cv2
from typing import List, Tuple
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from common import setup_logging


logger = setup_logging("sam-model", os.getenv("LOG_LEVEL", "INFO"))


class SAMSegmentationModel:
    """
    Segment Anything Model for automatic mask generation.
    
    Features:
    - Automatic mask generation (no prompts needed)
    - GPU/CPU support
    - Configurable mask quality
    - Real-time optimized
    """
    
    def __init__(
        self,
        model_version: str = "sam-vit-b",
        device: str = "cpu",
        checkpoint_path: str = None,
        points_per_side: int = 16,  # Lower for speed, higher for quality
        pred_iou_thresh: float = 0.7,
        stability_score_thresh: float = 0.8,
    ):
        """
        Initialize SAM model.
        
        Args:
            model_version: SAM model variant (sam-vit-b, sam-vit-l, sam-vit-h)
            device: Compute device ('cpu' or 'cuda')
            checkpoint_path: Path to model checkpoint
            points_per_side: Number of points per side for mask generation
            pred_iou_thresh: IoU threshold for mask prediction
            stability_score_thresh: Stability score threshold
        """
        self.model_version = model_version
        self.device = device
        self.points_per_side = points_per_side
        
        logger.info(f"Initializing SAM model {model_version} on {device}")
        
        # Determine model type and checkpoint
        if "vit-h" in model_version or model_version == "vit_h":
            model_type = "vit_h"
            default_checkpoint = "sam_vit_h_4b8939.pth"
        elif "vit-l" in model_version or model_version == "vit_l":
            model_type = "vit_l"
            default_checkpoint = "sam_vit_l_0b3195.pth"
        else:  # vit-b (default - fastest)
            model_type = "vit_b"
            default_checkpoint = "sam_vit_b_01ec64.pth"
        
        checkpoint_path = checkpoint_path or default_checkpoint
        
        try:
            # Load SAM model
            self.sam = sam_model_registry[model_type](checkpoint=checkpoint_path)
            self.sam.to(device=device)
            
            # Create mask generator
            self.mask_generator = SamAutomaticMaskGenerator(
                model=self.sam,
                points_per_side=points_per_side,
                pred_iou_thresh=pred_iou_thresh,
                stability_score_thresh=stability_score_thresh,
                crop_n_layers=1,  # Faster
                crop_n_points_downscale_factor=2,  # Faster
                min_mask_region_area=100,  # Filter small masks
            )
            
            logger.info(f"SAM model loaded successfully from {checkpoint_path}")
            
        except Exception as e:
            logger.error(f"Failed to load SAM model: {e}")
            logger.warning("Falling back to demo mode with synthetic masks")
            self.sam = None
            self.mask_generator = None
    
    def generate_masks(self, image: np.ndarray) -> Tuple[List[dict], float]:
        """
        Generate segmentation masks for an image.
        
        Args:
            image: Input image (RGB format)
        
        Returns:
            Tuple of (masks_list, inference_time_ms)
            Each mask dict contains:
            - segmentation: binary mask array
            - area: mask area
            - bbox: bounding box [x, y, w, h]
            - predicted_iou: quality score
            - stability_score: mask stability
        """
        start_time = time.time()
        
        try:
            if self.mask_generator is None:
                # Demo mode - generate synthetic masks
                masks = self._generate_demo_masks(image.shape)
            else:
                # Real SAM inference
                # Convert BGR to RGB if needed
                if len(image.shape) == 3 and image.shape[2] == 3:
                    # Check if it's BGR (OpenCV format)
                    if np.mean(image[:, :, 0]) > np.mean(image[:, :, 2]):
                        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
                # Generate masks
                masks = self.mask_generator.generate(image)
                
                # Sort by area (largest first)
                masks = sorted(masks, key=lambda x: x['area'], reverse=True)
                
                # Limit number of masks for performance
                max_masks = 10
                masks = masks[:max_masks]
            
            inference_time = (time.time() - start_time) * 1000
            
            logger.debug(
                f"Generated {len(masks)} masks in {inference_time:.2f}ms"
            )
            
            return masks, inference_time
            
        except Exception as e:
            logger.error(f"Mask generation failed: {e}")
            inference_time = (time.time() - start_time) * 1000
            return [], inference_time
    
    def _generate_demo_masks(self, image_shape: Tuple[int, int, int]) -> List[dict]:
        """
        Generate synthetic masks for demo when model is not available.
        
        Args:
            image_shape: Shape of the input image (H, W, C)
        
        Returns:
            List of synthetic mask dictionaries
        """
        h, w = image_shape[:2]
        masks = []
        
        # Generate 2-3 random masks
        num_masks = np.random.randint(2, 4)
        
        for i in range(num_masks):
            # Random position and size
            mask_w = int(w * np.random.uniform(0.15, 0.35))
            mask_h = int(h * np.random.uniform(0.15, 0.35))
            x = np.random.randint(0, max(1, w - mask_w))
            y = np.random.randint(0, max(1, h - mask_h))
            
            # Create binary mask
            mask = np.zeros((h, w), dtype=bool)
            
            # Create ellipse or rectangle
            if np.random.random() > 0.5:
                # Ellipse
                center = (x + mask_w // 2, y + mask_h // 2)
                axes = (mask_w // 2, mask_h // 2)
                cv2.ellipse(mask.astype(np.uint8), center, axes, 0, 0, 360, 1, -1)
                mask = mask.astype(bool)
            else:
                # Rectangle
                mask[y:y+mask_h, x:x+mask_w] = True
            
            area = int(np.sum(mask))
            
            mask_dict = {
                'segmentation': mask,
                'area': area,
                'bbox': [x, y, mask_w, mask_h],
                'predicted_iou': np.random.uniform(0.75, 0.95),
                'stability_score': np.random.uniform(0.85, 0.98),
            }
            masks.append(mask_dict)
        
        return masks
    
    def get_model_info(self) -> dict:
        """
        Get model information.
        
        Returns:
            Dictionary with model metadata
        """
        return {
            "model": "Segment Anything Model (SAM)",
            "version": self.model_version,
            "device": self.device,
            "type": "segmentation",
            "points_per_side": self.points_per_side,
            "loaded": self.sam is not None,
        }

