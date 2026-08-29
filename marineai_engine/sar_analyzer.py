"""
Synthetic Aperture Radar (SAR) Dark-Spot Detection & Texture Analysis Module
Processes SAR imagery (e.g. Sentinel-1 C-band, TerraSAR-X, RADARSAT) for marine oil spill detection.
Features speckle noise filtering, adaptive thresholding, morphological clustering,
and GLCM (Gray-Level Co-occurrence Matrix) textural discrimination.
"""

import numpy as np
import cv2
from typing import Dict, Any, Tuple, List

def apply_lee_filter(image: np.ndarray, window_size: int = 5, damping_factor: float = 1.0) -> np.ndarray:
    """
    Apply Lee Speckle Noise Filter on SAR imagery to preserve edges while smoothing multiplicative speckle.
    """
    img = image.astype(np.float32)
    mean = cv2.blur(img, (window_size, window_size))
    mean_sq = cv2.blur(img ** 2, (window_size, window_size))
    variance = np.maximum(mean_sq - mean ** 2, 0)
    
    overall_variance = np.var(img)
    if overall_variance == 0:
        return image
    
    # Weight calculation k = Var(window) / (Var(window) + Overall_Var)
    weights = variance / (variance + (overall_variance / damping_factor) + 1e-7)
    weights = np.clip(weights, 0.0, 1.0)
    filtered = mean + weights * (img - mean)
    return np.clip(filtered, 0, 255).astype(np.uint8)

def compute_glcm_features(gray: np.ndarray, mask: np.ndarray) -> Dict[str, float]:
    """
    Compute Gray Level Co-occurrence Matrix (GLCM) textural descriptors
    (Homogeneity, Contrast, Energy, Entropy, Dissimilarity).
    """
    # Reduce gray levels to 16 bins for fast, robust co-occurrence stats
    quantized = (gray // 16).astype(np.uint8)
    h, w = quantized.shape
    
    # Shift right by 1 pixel for horizontal co-occurrence
    left = quantized[:, :-1]
    right = quantized[:, 1:]
    
    if mask is not None and mask.shape == gray.shape:
        valid = (mask[:, :-1] > 0) & (mask[:, 1:] > 0)
    else:
        valid = np.ones((h, w - 1), dtype=bool)
        
    if not np.any(valid):
        return {
            "glcm_homogeneity": 0.5,
            "glcm_contrast": 1.2,
            "glcm_energy": 0.2,
            "glcm_entropy": 3.1,
            "glcm_dissimilarity": 0.8
        }
        
    l_vals = left[valid]
    r_vals = right[valid]
    
    # 16x16 joint histogram
    glcm, _, _ = np.histogram2d(l_vals, r_vals, bins=16, range=[[0, 16], [0, 16]])
    total = np.sum(glcm)
    if total > 0:
        glcm /= total
    else:
        glcm = np.eye(16) / 16.0
        
    i, j = np.indices((16, 16))
    
    # GLCM metrics
    contrast = float(np.sum(glcm * ((i - j) ** 2)))
    dissimilarity = float(np.sum(glcm * np.abs(i - j)))
    homogeneity = float(np.sum(glcm / (1.0 + (i - j) ** 2)))
    energy = float(np.sum(glcm ** 2))
    
    non_zero = glcm[glcm > 0]
    entropy = float(-np.sum(non_zero * np.log2(non_zero)))
    
    return {
        "glcm_homogeneity": round(homogeneity, 4),
        "glcm_contrast": round(contrast, 4),
        "glcm_energy": round(energy, 4),
        "glcm_entropy": round(entropy, 4),
        "glcm_dissimilarity": round(dissimilarity, 4)
    }

def analyze_sar_image(image: np.ndarray, km_per_pixel: float = 0.03) -> Dict[str, Any]:
    """
    Full SAR Dark-Spot Detection Pipeline.
    
    Args:
        image: Input SAR image as BGR or Grayscale numpy array.
        km_per_pixel: Resolution in kilometers per pixel (Default: 30m / 0.03km for Sentinel-1 EW/IW).
        
    Returns:
        Dictionary containing detected dark spot mask, contours, metrics, and radar backscatter contrast.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
        
    # 1. Speckle Filtering via Lee-like adaptive filter
    filtered = apply_lee_filter(gray, window_size=5)
    
    # 2. Estimate background sea clutter mean and standard deviation
    bg_mean = float(np.mean(filtered))
    bg_std = float(np.std(filtered))
    
    # 3. Adaptive dark-spot thresholding (oil spill dampens backscatter by > 1.2 std)
    adaptive_thresh = max(10, int(bg_mean - 1.25 * bg_std))
    _, binary_dark = cv2.threshold(filtered, adaptive_thresh, 255, cv2.THRESH_BINARY_INV)
    
    # 4. Morphological opening/closing to remove isolated speckle artifacts & fill core
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    cleaned_mask = cv2.morphologyEx(binary_dark, cv2.MORPH_OPEN, kernel, iterations=1)
    cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    
    # 5. Extract contours and shape geometry
    contours, _ = cv2.findContours(cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    total_spill_pixels = 0
    spill_patches = []
    min_patch_pixels = 100  # filter insignificant speckle patches
    
    filtered_mask = np.zeros_like(cleaned_mask)
    border_gradients = []
    
    for cnt in contours:
        area_px = cv2.contourArea(cnt)
        if area_px < min_patch_pixels:
            continue
            
        total_spill_pixels += area_px
        cv2.drawContours(filtered_mask, [cnt], -1, 255, -1)
        
        perimeter_px = cv2.arcLength(cnt, True)
        
        # Bounding box & Aspect ratio
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = float(w) / max(h, 1)
        if aspect_ratio < 1.0:
            aspect_ratio = 1.0 / aspect_ratio
            
        # Circularity/Compactness: 4*pi*Area / P^2 (Oil slicks have irregular, low compactness)
        compactness = (4 * np.pi * area_px) / (perimeter_px ** 2 + 1e-5)
        
        # Mean intensity inside patch vs surround
        patch_mask = np.zeros_like(gray)
        cv2.drawContours(patch_mask, [cnt], -1, 255, -1)
        patch_mean = float(np.mean(filtered[patch_mask > 0]))
        
        # Measure boundary gradient steepness (Sobel gradient at contour edge)
        dilated = cv2.dilate(patch_mask, kernel, iterations=2)
        boundary_zone = dilated ^ patch_mask
        if np.any(boundary_zone > 0):
            grad_x = cv2.Sobel(filtered, cv2.CV_32F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(filtered, cv2.CV_32F, 0, 1, ksize=3)
            grad_mag = np.sqrt(grad_x ** 2 + grad_y ** 2)
            mean_grad = float(np.mean(grad_mag[boundary_zone > 0]))
            border_gradients.append(mean_grad)
        else:
            mean_grad = 0.0
            
        patch_area_km2 = area_px * (km_per_pixel ** 2)
        spill_patches.append({
            "area_px": int(area_px),
            "area_km2": round(patch_area_km2, 4),
            "perimeter_km": round(perimeter_px * km_per_pixel, 3),
            "compactness": round(compactness, 4),
            "aspect_ratio": round(aspect_ratio, 2),
            "mean_backscatter_intensity": round(patch_mean, 1),
            "boundary_gradient": round(mean_grad, 2),
            "bounding_box": [int(x), int(y), int(w), int(h)]
        })
        
    total_area_km2 = total_spill_pixels * (km_per_pixel ** 2)
    
    # Calculate GLCM Textural stats within detected dark region
    glcm_stats = compute_glcm_features(filtered, filtered_mask if total_spill_pixels > 0 else None)
    
    # Backscatter contrast (dB difference ~ 10 * log10(bg / slick))
    if total_spill_pixels > 0:
        slick_mean = float(np.mean(filtered[filtered_mask > 0]))
        backscatter_contrast_db = 10 * np.log10(max(bg_mean, 1) / max(slick_mean, 1))
    else:
        slick_mean = bg_mean
        backscatter_contrast_db = 0.0
        
    avg_border_grad = float(np.mean(border_gradients)) if border_gradients else 0.0

    return {
        "is_sar": True,
        "total_spill_pixels": int(total_spill_pixels),
        "total_spill_area_km2": round(total_area_km2, 4),
        "patches_count": len(spill_patches),
        "patches": spill_patches,
        "background_mean": round(bg_mean, 2),
        "slick_mean": round(slick_mean, 2),
        "backscatter_contrast_db": round(backscatter_contrast_db, 2),
        "average_boundary_gradient": round(avg_border_grad, 2),
        "glcm": glcm_stats,
        "mask": filtered_mask,
        "filtered_image": filtered
    }
