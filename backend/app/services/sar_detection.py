"""
MarineGuard AI - SAR Oil Spill Detection Service
Preprocesses Sentinel-1 SAR imagery with Lee speckle filtering, runs U-Net segmentation,
polygonizes contours, classifies according to Bonn Agreement standards, and filters look-alikes.
"""

import os
import cv2
import base64
import numpy as np
from typing import Dict, Any, Tuple, Optional
from ml.inference import SAROilSpillInference, apply_lee_filter, extract_glcm_features
from backend.app.core.config import settings

_inference_engine = None


def get_inference_engine():
    global _inference_engine
    if _inference_engine is None:
        _inference_engine = SAROilSpillInference(model_path=settings.UNET_MODEL_PATH)
    return _inference_engine


def decode_base64_image(base64_string: str) -> np.ndarray:
    """Decode base64 encoded image string to OpenCV BGR array"""
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]
    img_bytes = base64.b64decode(base64_string)
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img


def encode_image_to_base64(img_bgr: np.ndarray) -> str:
    """Encode OpenCV image to base64 PNG data URI"""
    _, buffer = cv2.imencode('.png', img_bgr)
    b64_str = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/png;base64,{b64_str}"


def process_sar_imagery(image_array: np.ndarray, center_lat: float, center_lon: float, pixel_res_m: float = 10.0) -> Dict[str, Any]:
    """
    Complete SAR detection workflow:
    1. Preprocessing & Speckle filtering
    2. Deep U-Net segmentation
    3. Look-alike vs Mineral Oil discrimination
    4. Bonn scale thickness & volume quantification
    5. GeoJSON polygon generation
    6. Mask & HUD overlay image generation
    """
    engine = get_inference_engine()
    results = engine.predict(image_array, center_lat=center_lat, center_lon=center_lon, pixel_res_m=pixel_res_m)

    # Generate visual mask and overlay
    h, w = image_array.shape[:2]
    gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY) if len(image_array.shape) == 3 else image_array.copy()
    lee = apply_lee_filter(gray)
    
    # Render glowing neon cyan/red mask overlay
    overlay = cv2.cvtColor(lee, cv2.COLOR_GRAY2BGR)
    mask_viz = np.zeros((h, w, 3), dtype=np.uint8)

    for poly in results.get("spill_polygons", []):
        coords = poly["coordinates"][0]
        # Project back to pixels
        deg_per_pixel_lat = pixel_res_m / 111000.0
        deg_per_pixel_lon = pixel_res_m / (111000.0 * max(0.1, np.cos(np.radians(center_lat))))

        pts = []
        for lon, lat in coords:
            px = int(w / 2.0 + (lon - center_lon) / deg_per_pixel_lon)
            py = int(h / 2.0 - (lat - center_lat) / deg_per_pixel_lat)
            pts.append([px, py])

        pts_arr = np.array(pts, dtype=np.int32)
        if len(pts_arr) > 2:
            # Color by Bonn code: Code 5 (magenta), Code 4 (red), Code 3 (amber), Code 2 (cyan)
            color = (0, 0, 255) if poly["bonn_code"] >= 4 else (0, 165, 255) if poly["bonn_code"] == 3 else (255, 255, 0)
            cv2.fillPoly(mask_viz, [pts_arr], color)
            cv2.polylines(overlay, [pts_arr], True, (0, 255, 255), 2)

    combined_overlay = cv2.addWeighted(overlay, 0.7, mask_viz, 0.6, 0)

    results["raw_image_url"] = encode_image_to_base64(image_array)
    results["mask_image_url"] = encode_image_to_base64(mask_viz)
    results["overlay_image_url"] = encode_image_to_base64(combined_overlay)

    return results
