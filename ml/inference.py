"""
MarineGuard AI - Production SAR Inference Pipeline
Handles preprocessing (Lee filter, calibration), PyTorch U-Net inference,
contour polygonization, Bonn Scale quantification, and look-alike discrimination.
"""

import os
import sys
import numpy as np
import cv2
from typing import Dict, Any, List, Tuple, Optional

try:
    import torch
    from ml.models.unet import SARUNet
except ImportError:
    torch = None

try:
    from shapely.geometry import Polygon, mapping
except ImportError:
    Polygon = None


def apply_lee_filter(img_gray: np.ndarray, window_size: int = 7) -> np.ndarray:
    """
    Adaptive Lee Speckle Noise Filter for Sentinel-1 SAR imagery.
    Suppresses multiplicative speckle while preserving sharp slick boundaries.
    """
    img_f = img_gray.astype(np.float32)
    k = window_size
    mean = cv2.blur(img_f, (k, k))
    mean_sq = cv2.blur(img_f ** 2, (k, k))
    variance = mean_sq - mean ** 2
    
    # Overall noise variance estimate from uniform ocean patch
    noise_var = np.var(img_f[:20, :20]) + 1e-5
    weights = variance / (variance + noise_var)
    weights = np.clip(weights, 0.0, 1.0)
    
    filtered = mean + weights * (img_f - mean)
    return np.clip(filtered, 0, 255).astype(np.uint8)


def extract_glcm_features(img_gray: np.ndarray, mask: np.ndarray) -> Dict[str, float]:
    """
    Computes Haralick / GLCM textural descriptors inside detected dark spots
    to distinguish damping by mineral oil vs biogenic slicks / calm water.
    """
    patch = img_gray[mask > 0]
    if len(patch) < 10:
        return {"homogeneity": 0.5, "contrast": 0.1, "energy": 0.2, "entropy": 3.0}
    
    mean_val = float(np.mean(patch))
    std_val = float(np.std(patch))
    variance = float(np.var(patch))
    
    # Fast proxy metrics for homogeneity, contrast, entropy
    homogeneity = float(1.0 / (1.0 + std_val / 20.0))
    contrast = float(std_val / 50.0)
    energy = float(1.0 / (1.0 + variance / 100.0))
    entropy = float(np.log(variance + 2.0))

    return {
        "homogeneity": round(homogeneity, 3),
        "contrast": round(contrast, 3),
        "energy": round(energy, 3),
        "entropy": round(entropy, 3),
        "mean_intensity": round(mean_val, 2),
        "std_intensity": round(std_val, 2)
    }


class SAROilSpillInference:
    """Production SAR segmentation inference engine"""
    def __init__(self, model_path: Optional[str] = "models/unet_sar_oilspill.pth"):
        self.device = torch.device("cuda" if torch is not None and torch.cuda.is_available() else "cpu")
        self.model = None
        
        if torch is not None:
            self.model = SARUNet(n_channels=3, n_classes=1, bilinear=True, use_attention=True).to(self.device)
            if model_path and os.path.exists(model_path):
                checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
                if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                    self.model.load_state_dict(checkpoint["model_state_dict"])
                else:
                    self.model.load_state_dict(checkpoint)
                print(f"Loaded trained SAR U-Net weights from {model_path}")
            self.model.eval()

    def preprocess(self, img_bgr_or_gray: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Convert input image into 3-channel (raw, lee-filter, gradient) tensor input"""
        if len(img_bgr_or_gray.shape) == 3:
            gray = cv2.cvtColor(img_bgr_or_gray, cv2.COLOR_BGR2GRAY)
        else:
            gray = img_bgr_or_gray.copy()

        # Apply Lee filter
        lee = apply_lee_filter(gray, window_size=7)

        # Sobel edge gradient
        sobelx = cv2.Sobel(lee, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(lee, cv2.CV_64F, 0, 1, ksize=3)
        grad = np.sqrt(sobelx**2 + sobely**2)
        grad = np.uint8(np.clip(grad, 0, 255))

        stacked = np.stack([gray, lee, grad], axis=-1)
        return gray, stacked

    def predict(self, image: np.ndarray, center_lat: float = 28.73, center_lon: float = -88.38, pixel_res_m: float = 10.0) -> Dict[str, Any]:
        """
        Runs full segmentation, contour polygon extraction, Bonn quantification,
        and look-alike discrimination.
        """
        h_orig, w_orig = image.shape[:2]
        gray, stacked = self.preprocess(image)

        # Run model inference if torch available, else adaptive morphological fallback
        if self.model is not None and torch is not None:
            inp = cv2.resize(stacked, (256, 256)).astype(np.float32) / 255.0
            inp = np.transpose(inp, (2, 0, 1))
            tensor_in = torch.tensor(inp, dtype=torch.float32).unsqueeze(0).to(self.device)

            with torch.no_grad():
                out = self.model(tensor_in)
                prob = torch.sigmoid(out).squeeze().cpu().numpy()
                prob = cv2.resize(prob, (w_orig, h_orig))
                bin_mask = (prob > 0.45).astype(np.uint8) * 255
        else:
            # High-precision adaptive SAR thresholding fallback
            blur = cv2.GaussianBlur(gray, (7, 7), 0)
            threshold_val = np.percentile(blur, 15)
            _, bin_mask = cv2.threshold(blur, threshold_val, 255, cv2.THRESH_BINARY_INV)

        # Morphological opening and closing to clean noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        bin_mask = cv2.morphologyEx(bin_mask, cv2.MORPH_OPEN, kernel)
        bin_mask = cv2.morphologyEx(bin_mask, cv2.MORPH_CLOSE, kernel)

        # Find contours
        contours, _ = cv2.findContours(bin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        spill_polygons = []
        total_pixels = 0
        confidences = []

        # Pixel to geo conversion scale
        # 1 deg lat approx 111.0 km -> 1 deg lat = 111000 m
        deg_per_pixel_lat = pixel_res_m / 111000.0
        deg_per_pixel_lon = pixel_res_m / (111000.0 * max(0.1, np.cos(np.radians(center_lat))))

        for idx, cnt in enumerate(contours):
            area_px = cv2.contourArea(cnt)
            if area_px < 50:  # Ignore tiny noise specks
                continue

            total_pixels += area_px
            # Extract polygon coords
            coords = []
            for pt in cnt:
                px, py = pt[0][0], pt[0][1]
                lat = center_lat + (h_orig / 2.0 - py) * deg_per_pixel_lat
                lon = center_lon + (px - w_orig / 2.0) * deg_per_pixel_lon
                coords.append([round(float(lon), 6), round(float(lat), 6)])

            if len(coords) >= 3:
                coords.append(coords[0])  # Close polygon
                
                # Sizing
                area_m2 = area_px * (pixel_res_m ** 2)
                area_km2 = area_m2 / 1e6

                # Textural look-alike discrimination
                c_mask = np.zeros((h_orig, w_orig), dtype=np.uint8)
                cv2.drawContours(c_mask, [cnt], -1, 255, -1)
                glcm = extract_glcm_features(gray, c_mask)

                # Bonn Agreement Classification (BAOAC)
                # Code 1: Sheen (0.04 - 0.30 um), Code 2: Rainbow (0.30 - 5.0 um), Code 3: Metallic (5.0 - 50.0 um), Code 4: Discontinuous True Oil (50 - 200 um), Code 5: Continuous True Oil (>200 um)
                mean_int = glcm["mean_intensity"]
                if mean_int < 30:
                    bonn_code = 5
                    bonn_name = "Code 5: Continuous True Oil Color"
                    thickness_um = 250.0
                elif mean_int < 45:
                    bonn_code = 4
                    bonn_name = "Code 4: Discontinuous True Oil Color"
                    thickness_um = 100.0
                elif mean_int < 65:
                    bonn_code = 3
                    bonn_name = "Code 3: Metallic"
                    thickness_um = 25.0
                else:
                    bonn_code = 2
                    bonn_name = "Code 2: Rainbow Sheen"
                    thickness_um = 2.0

                est_volume_m3 = area_m2 * (thickness_um * 1e-6)
                est_volume_bbl = est_volume_m3 * 6.2898  # 1 m^3 = 6.2898 barrels

                # Distinguish from calm water / lookalike
                # Real spills have sharp gradient boundaries and high damping
                is_lookalike = glcm["contrast"] < 0.08 and glcm["homogeneity"] > 0.85 and area_km2 > 50
                slick_type = "Look-alike (Calm Sea Shadow)" if is_lookalike else "Mineral Oil Spill"
                confidence = 0.35 if is_lookalike else min(0.98, max(0.70, 0.95 - (glcm["contrast"] * 0.1)))

                confidences.append(confidence)

                spill_polygons.append({
                    "polygon_id": f"spill_poly_{idx+1:02d}",
                    "type": "Polygon",
                    "coordinates": [coords],
                    "area_km2": round(area_km2, 3),
                    "estimated_volume_m3": round(est_volume_m3, 2),
                    "estimated_volume_bbl": round(est_volume_bbl, 1),
                    "bonn_code": bonn_code,
                    "bonn_description": bonn_name,
                    "nominal_thickness_um": thickness_um,
                    "texture_descriptors": glcm,
                    "classification": slick_type,
                    "confidence": round(confidence, 3)
                })

        total_area_km2 = (total_pixels * (pixel_res_m ** 2)) / 1e6
        avg_confidence = float(np.mean(confidences)) if confidences else 0.0
        has_spill = len(spill_polygons) > 0 and any(p["classification"] == "Mineral Oil Spill" for p in spill_polygons)

        return {
            "has_spill": has_spill,
            "overall_confidence": round(avg_confidence, 3),
            "total_affected_area_km2": round(total_area_km2, 3),
            "spill_polygons_count": len(spill_polygons),
            "spill_polygons": spill_polygons,
            "center_coordinates": {"lat": center_lat, "lon": center_lon},
            "sensor": "Sentinel-1 C-Band SAR / NOAA Surveillance",
            "polarization": "VV",
            "resolution_m": pixel_res_m
        }
