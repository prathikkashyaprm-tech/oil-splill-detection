"""
MarineAI Core Detection & Analysis Orchestrator
Coordinates image ingestion, sensor modality detection, CV pipelines,
classification, Bonn quantification, and visual overlay synthesis.
"""

import base64
import io
import cv2
import numpy as np
from PIL import Image
from typing import Dict, Any, Union, Optional

from .sar_analyzer import analyze_sar_image
from .optical_analyzer import analyze_optical_image
from .classifier import classify_marine_scene
from .bonn_scale import calculate_bonn_metrics

def detect_sensor_modality(image: np.ndarray) -> str:
    """
    Automatically detects if an image is SAR grayscale radar or Optical RGB.
    """
    if len(image.shape) == 2:
        return "SAR"
    
    # Check channel difference
    b, g, r = image[:, :, 0], image[:, :, 1], image[:, :, 2]
    diff_bg = np.mean(np.abs(b.astype(float) - g.astype(float)))
    diff_gr = np.mean(np.abs(g.astype(float) - r.astype(float)))
    
    # If channels are nearly identical, it's a grayscale/SAR radar image
    if diff_bg < 4.0 and diff_gr < 4.0:
        return "SAR"
    return "OPTICAL"

def create_visual_overlay(
    original_bgr: np.ndarray,
    mask: np.ndarray,
    classification: Dict[str, Any],
    patches: list
) -> str:
    """
    Synthesize high-tech visual HUD overlay on the detection image.
    Returns base64 PNG data URL.
    """
    h, w = original_bgr.shape[:2]
    overlay = original_bgr.copy()
    
    is_spill = classification.get("is_spill_positive", False)
    
    if is_spill and mask is not None and np.any(mask > 0):
        # Create crimson-orange slick mask overlay
        color_mask = np.zeros_like(original_bgr)
        # Red channel high, Green moderate, Blue low (Amber/Crimson alert glow)
        color_mask[mask > 0] = [25, 70, 240]  # BGR
        
        # Blend overlay (40% alpha mask + 60% original)
        cv2.addWeighted(color_mask, 0.45, overlay, 0.55, 0, overlay)
        
        # Draw contour boundary lines with cyan/neon border
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(overlay, contours, -1, (255, 230, 0), 2)  # Neon cyan/yellow border
        
        # Draw bounding boxes and patch annotations
        for i, p in enumerate(patches[:5]):
            bbox = p.get("bounding_box")
            if bbox:
                bx, by, bw, bh = bbox
                cv2.rectangle(overlay, (bx, by), (bx + bw, by + bh), (0, 240, 255), 1)
                label_text = f"SLICK #{i+1} ({p.get('area_km2', 0):.2f} km2)"
                cv2.putText(overlay, label_text, (bx, max(15, by - 6)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 240, 255), 1, cv2.LINE_AA)
                            
    # Encode to PNG and Base64 string
    _, buffer = cv2.imencode('.png', overlay)
    b64_str = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/png;base64,{b64_str}"

def process_marine_image(
    image_input: Union[np.ndarray, bytes, str],
    sensor_type: Optional[str] = "AUTO",
    km_per_pixel: Optional[float] = None
) -> Dict[str, Any]:
    """
    Main entry point for MarineAI detection.
    
    Args:
        image_input: Raw image numpy array, bytes, or file path.
        sensor_type: "AUTO", "SAR", or "OPTICAL".
        km_per_pixel: Resolution override (km/pixel).
        
    Returns:
        Structured dictionary with detection verdict, mask, bonn metrics, and base64 overlay.
    """
    # 1. Load image
    if isinstance(image_input, str):
        img_bgr = cv2.imread(image_input)
        if img_bgr is None:
            raise ValueError(f"Failed to load image from path: {image_input}")
    elif isinstance(image_input, bytes):
        nparr = np.frombuffer(image_input, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            raise ValueError("Failed to decode image bytes.")
    elif isinstance(image_input, np.ndarray):
        img_bgr = image_input.copy()
        if len(img_bgr.shape) == 2:
            img_bgr = cv2.cvtColor(img_bgr, cv2.COLOR_GRAY2BGR)
    else:
        raise TypeError("Unsupported image input format.")

    # 2. Determine Sensor Modality
    if sensor_type is None or sensor_type.upper() == "AUTO":
        detected_sensor = detect_sensor_modality(img_bgr)
    else:
        detected_sensor = sensor_type.upper()

    # Default resolution calibration
    if km_per_pixel is None or km_per_pixel <= 0:
        km_per_pixel = 0.03 if detected_sensor == "SAR" else 0.008  # 30m for SAR, 8m for Drone/Optical

    # 3. Execute Specialized Modality Pipeline
    if detected_sensor == "SAR":
        sar_res = analyze_sar_image(img_bgr, km_per_pixel=km_per_pixel)
        optical_res = {}
        classification = classify_marine_scene(sar_res, optical_res, is_sar_mode=True)
        detected_area_km2 = sar_res["total_spill_area_km2"]
        mask = sar_res["mask"]
        patches = sar_res["patches"]
        bonn_dist = None
    else:
        optical_res = analyze_optical_image(img_bgr, km_per_pixel=km_per_pixel)
        sar_res = {}
        classification = classify_marine_scene(sar_res, optical_res, is_sar_mode=False)
        detected_area_km2 = optical_res["total_spill_area_km2"]
        mask = optical_res["mask"]
        patches = optical_res["patches"]
        bonn_dist = optical_res.get("bonn_distribution")

    # 4. If positive spill, calculate Bonn Agreement volume & metrics
    if classification["is_spill_positive"]:
        bonn_metrics = calculate_bonn_metrics(
            spill_area_km2=detected_area_km2,
            bonn_code=3,
            coverage_distribution=bonn_dist
        )
    else:
        bonn_metrics = calculate_bonn_metrics(spill_area_km2=0.0)

    # 5. Generate visual overlay
    overlay_data_url = create_visual_overlay(img_bgr, mask, classification, patches)
    
    # Original image as data URL for clean side-by-side comparison
    _, orig_buf = cv2.imencode('.png', img_bgr)
    original_data_url = f"data:image/png;base64,{base64.b64encode(orig_buf).decode('utf-8')}"

    # Clean telemetry to ensure 100% JSON serializability (remove raw ndarrays)
    sar_clean = None
    if detected_sensor == "SAR" and sar_res:
        sar_clean = {k: v for k, v in sar_res.items() if not isinstance(v, np.ndarray)}
        
    optical_clean = None
    if detected_sensor != "SAR" and optical_res:
        optical_clean = {k: v for k, v in optical_res.items() if not isinstance(v, np.ndarray)}

    return {
        "status": "success",
        "sensor_modality": detected_sensor,
        "resolution_km_per_pixel": km_per_pixel,
        "image_dimensions": {"width": int(img_bgr.shape[1]), "height": int(img_bgr.shape[0])},
        "classification": classification,
        "bonn_metrics": bonn_metrics,
        "sar_telemetry": sar_clean,
        "optical_telemetry": optical_clean,
        "visual_overlay_url": overlay_data_url,
        "original_image_url": original_data_url
    }
