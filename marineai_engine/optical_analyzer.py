"""
Optical & Aerial Drone RGB Slick Detection Module
Analyzes visible optical imagery (Sentinel-2, Landsat, Drone/Aerial RGB) for oil sheen,
emulsified dark crude, and spectral separation from biogenic algae or ship wakes.
"""

import numpy as np
import cv2
from typing import Dict, Any, Tuple, List

def compute_optical_indices(bgr: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Computes spectral proxy indices from RGB channels:
    - Hydrocarbon Reflectance Index (HRI): Highlights dark crude & metallic absorption
    - Chlorophyll Algae Proxy (NDAP): Measures green dominance over blue/red (algae has high green/NIR)
    - Iridescent Sheen Index (ISI): High local chromatic variance with specular sheen
    """
    b = bgr[:, :, 0].astype(np.float32)
    g = bgr[:, :, 1].astype(np.float32)
    r = bgr[:, :, 2].astype(np.float32)
    
    epsilon = 1e-5
    
    # NDAP proxy: In normal ocean B > G > R. In algae bloom G > B and G > R.
    # Algae proxy: (Green - Blue) / (Green + Blue + eps)
    algae_green_dominance = (g - b) / (g + b + epsilon)
    
    # Clean ocean water ratio: Blue is dominant (B > G > R)
    water_blue_ratio = (b - r) / (b + r + epsilon)
    
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    
    # HSV color space analysis
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1].astype(np.float32)
    value = hsv[:, :, 2].astype(np.float32)
    
    return {
        "algae_proxy": algae_green_dominance,
        "water_index": water_blue_ratio,
        "gray": gray,
        "saturation": saturation,
        "value": value
    }

def analyze_optical_image(image: np.ndarray, km_per_pixel: float = 0.005) -> Dict[str, Any]:
    """
    Full Optical / Drone Oil Slick Analysis Pipeline.
    
    Args:
        image: BGR format image (from satellite or drone camera).
        km_per_pixel: Resolution in km/pixel (e.g. 5m / 0.005km for drone/high-res optical).
        
    Returns:
        Segmentation masks, slick core vs sheen fractions, and spectral metrics.
    """
    if len(image.shape) == 2:
        # If grayscale, convert to BGR for unified processing
        bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    else:
        bgr = image.copy()
        
    indices = compute_optical_indices(bgr)
    gray = indices["gray"]
    algae_proxy = indices["algae_proxy"]
    saturation = indices["saturation"]
    value = indices["value"]
    
    # 1. Open ocean water baseline estimation
    h, w, _ = bgr.shape
    ocean_mean_val = float(np.median(value))
    ocean_mean_sat = float(np.median(saturation))
    
    # 2. Dark crude oil detection (low luminance, low algae proxy, dark bitumen tone)
    dark_oil_mask = (value < (ocean_mean_val * 0.72)) & (algae_proxy < 0.05)
    
    # 3. Sheen / Metallic thin film detection
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    
    # Texture smoothness: oil dampens capillary wave texture
    blur_sq = cv2.blur(gray ** 2, (7, 7))
    blur_avg = cv2.blur(gray, (7, 7))
    local_std = np.sqrt(np.maximum(blur_sq - (blur_avg ** 2), 0))
    
    ocean_std_median = float(np.median(local_std))
    smooth_surface = local_std < (ocean_std_median * 0.75)
    
    # Look-alike check: algae has strong green-over-blue dominance (algae_proxy > 0.20)
    algae_mask = (algae_proxy > 0.20) & (value > 50)
    algae_pixel_ratio = float(np.sum(algae_mask)) / (h * w)
    
    # Look-alike check: Ship wake has high brightness (> 210) & bubbly texture
    wake_mask = (value > 210) & (local_std > ocean_std_median * 1.4)
    wake_pixel_ratio = float(np.sum(wake_mask)) / (h * w)
    
    # Combine slick candidates: either thick dark oil or thin smooth hydrocarbon sheen, excluding algae and wakes
    slick_candidate = (dark_oil_mask | (smooth_surface & (value < ocean_mean_val * 0.88))) & (~algae_mask) & (~wake_mask)
    
    # Morphological cleaning
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    slick_clean = cv2.morphologyEx(slick_candidate.astype(np.uint8) * 255, cv2.MORPH_OPEN, kernel)
    slick_clean = cv2.morphologyEx(slick_clean, cv2.MORPH_CLOSE, kernel, iterations=2)
    
    # Find contours
    contours, _ = cv2.findContours(slick_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    total_spill_pixels = 0
    thick_core_pixels = 0
    spill_patches = []
    
    final_mask = np.zeros((h, w), dtype=np.uint8)
    
    for cnt in contours:
        area_px = cv2.contourArea(cnt)
        if area_px < 35:  # skip tiny noise
            continue
            
        total_spill_pixels += area_px
        cv2.drawContours(final_mask, [cnt], -1, 255, -1)
        
        # Check thick crude core inside this patch
        patch_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.drawContours(patch_mask, [cnt], -1, 255, -1)
        core_px = np.sum((patch_mask > 0) & dark_oil_mask)
        thick_core_pixels += core_px
        
        perimeter_px = cv2.arcLength(cnt, True)
        x, y, pw, ph = cv2.boundingRect(cnt)
        aspect_ratio = float(pw) / max(ph, 1)
        if aspect_ratio < 1.0:
            aspect_ratio = 1.0 / aspect_ratio
            
        patch_area_km2 = area_px * (km_per_pixel ** 2)
        spill_patches.append({
            "area_px": int(area_px),
            "area_km2": round(patch_area_km2, 5),
            "perimeter_km": round(perimeter_px * km_per_pixel, 4),
            "thick_core_ratio": round(float(core_px) / max(area_px, 1), 3),
            "aspect_ratio": round(aspect_ratio, 2),
            "bounding_box": [int(x), int(y), int(pw), int(ph)]
        })
        
    total_area_km2 = total_spill_pixels * (km_per_pixel ** 2)
    thick_ratio = float(thick_core_pixels) / max(total_spill_pixels, 1) if total_spill_pixels > 0 else 0.0
    
    # Bonn distribution estimate:
    # If thick crude > 40%: Code 4 or 5
    # If thick crude 10-40%: Code 3 (Metallic)
    # If mostly thin sheen: Code 1 or 2 (Sheen/Rainbow)
    if total_spill_pixels > 0:
        if thick_ratio > 0.45:
            bonn_distribution = {5: 0.4, 4: 0.35, 3: 0.15, 2: 0.1}
        elif thick_ratio > 0.15:
            bonn_distribution = {4: 0.25, 3: 0.45, 2: 0.2, 1: 0.1}
        else:
            bonn_distribution = {3: 0.15, 2: 0.50, 1: 0.35}
    else:
        bonn_distribution = {1: 1.0}

    return {
        "is_optical": True,
        "total_spill_pixels": int(total_spill_pixels),
        "total_spill_area_km2": round(total_area_km2, 5),
        "thick_core_ratio": round(thick_ratio, 3),
        "patches_count": len(spill_patches),
        "patches": spill_patches,
        "algae_biomass_index": round(algae_pixel_ratio, 4),
        "ship_wake_index": round(wake_pixel_ratio, 4),
        "bonn_distribution": bonn_distribution,
        "mask": final_mask
    }
