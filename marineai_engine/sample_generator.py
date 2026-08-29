"""
High-Fidelity Sample Imagery Generator for MarineAI
Generates benchmark satellite SAR radar images, drone optical RGB slicks,
clean ocean scenes, and marine look-alikes for validation and interactive testing.
"""

import os
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple

def generate_sar_oil_spill_image(width: int = 512, height: int = 512, seed: int = 42) -> np.ndarray:
    """
    Generates realistic Sentinel-1 C-band SAR ocean imagery with an active dark oil spill formation.
    Features Rayleigh sea clutter distribution, capillary wave dampening, and edge gradient.
    """
    np.random.seed(seed)
    
    # 1. Base Sea Clutter: Rayleigh-like distribution with speckle
    base_sea = np.random.rayleigh(scale=35.0, size=(height, width))
    base_sea = cv2.GaussianBlur(base_sea, (3, 3), 0)
    
    # Add ambient low-frequency ocean wave ripples
    x = np.linspace(0, 10 * np.pi, width)
    y = np.linspace(0, 10 * np.pi, height)
    xx, yy = np.meshgrid(x, y)
    wave_pattern = 10 * np.sin(0.4 * xx + 0.3 * yy) + 5 * np.cos(0.2 * xx - 0.5 * yy)
    sea_intensity = np.clip(base_sea + wave_pattern + 90, 20, 240).astype(np.float32)
    
    # 2. Construct irregular oil slick morphology (elongated spline-like contour)
    slick_mask = np.zeros((height, width), dtype=np.uint8)
    
    # Center points for main slick body and drift tail
    cx, cy = width // 2, height // 2
    points = []
    num_pts = 16
    for i in range(num_pts):
        angle = (2 * np.pi * i) / num_pts
        # Make elongated along 45 degrees
        r_base = 90 + 50 * np.sin(2 * angle + 0.5)
        r_noise = np.random.uniform(-25, 25)
        r = r_base + r_noise
        px = int(cx + r * np.cos(angle) + 40 * np.sin(angle))
        py = int(cy + r * np.sin(angle) - 30 * np.cos(angle))
        points.append([px, py])
        
    pts_arr = np.array(points, dtype=np.int32)
    cv2.fillPoly(slick_mask, [pts_arr], 255)
    
    # Add secondary drift tail plume
    tail_pts = np.array([
        [cx + 70, cy - 50],
        [cx + 140, cy - 90],
        [cx + 180, cy - 110],
        [cx + 160, cy - 80],
        [cx + 90, cy - 30]
    ], dtype=np.int32)
    cv2.fillPoly(slick_mask, [tail_pts], 255)
    
    # Smooth edges with slight feathering for realistic radar transition
    slick_mask_smoothed = cv2.GaussianBlur(slick_mask.astype(np.float32), (11, 11), 0) / 255.0
    
    # Oil dampens capillary waves -> backscatter drops by ~4-8 dB (intensity drops to ~20-35%)
    damped_sea = sea_intensity * (1.0 - 0.72 * slick_mask_smoothed)
    
    # Add slight speckle inside the slick (lower variance than open sea)
    slick_speckle = np.random.normal(0, 4.0, size=(height, width))
    result = np.clip(damped_sea + slick_speckle, 0, 255).astype(np.uint8)
    
    return cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

def generate_drone_optical_slick_image(width: int = 512, height: int = 512, seed: int = 101) -> np.ndarray:
    """
    Generates high-resolution drone/aerial RGB imagery of marine oil slick.
    Displays dark brown/black crude core surrounded by iridescent rainbow sheen and deep blue sea.
    """
    np.random.seed(seed)
    
    # 1. Base open ocean (Deep Azure Blue)
    img = np.zeros((height, width, 3), dtype=np.float32)
    
    # Ocean color gradient: B: 155, G: 105, R: 45
    x = np.linspace(0, 1, width)
    y = np.linspace(0, 1, height)
    xx, yy = np.meshgrid(x, y)
    
    wave_noise = 8 * np.sin(15 * xx + 10 * yy) + 4 * np.random.randn(height, width)
    img[:, :, 0] = np.clip(160 + wave_noise, 0, 255)  # Blue
    img[:, :, 1] = np.clip(100 + wave_noise * 0.7, 0, 255)  # Green
    img[:, :, 2] = np.clip(35 + wave_noise * 0.4, 0, 255)   # Red
    
    # 2. Main slick core (Thick crude - dark brownish black)
    core_mask = np.zeros((height, width), dtype=np.float32)
    cx, cy = width // 2 - 20, height // 2 + 10
    
    core_pts = []
    for i in range(12):
        angle = (2 * np.pi * i) / 12
        r = 60 + 25 * np.sin(3 * angle) + np.random.uniform(-10, 10)
        px = int(cx + r * np.cos(angle))
        py = int(cy + r * np.sin(angle))
        core_pts.append([px, py])
    cv2.fillPoly(core_mask, [np.array(core_pts, dtype=np.int32)], 1.0)
    core_mask = cv2.GaussianBlur(core_mask, (15, 15), 0)
    
    # 3. Outer sheen zone (Iridescent rainbow/metallic thin film)
    sheen_mask = np.zeros((height, width), dtype=np.float32)
    sheen_pts = []
    for i in range(16):
        angle = (2 * np.pi * i) / 16
        r = 130 + 45 * np.cos(2 * angle) + np.random.uniform(-15, 15)
        px = int(cx + r * np.cos(angle) + 20 * np.sin(angle))
        py = int(cy + r * np.sin(angle) - 15 * np.cos(angle))
        sheen_pts.append([px, py])
    cv2.fillPoly(sheen_mask, [np.array(sheen_pts, dtype=np.int32)], 1.0)
    sheen_mask = cv2.GaussianBlur(sheen_mask, (25, 25), 0)
    
    # Sheen color modulation (Metallic rainbow sheen)
    rainbow_b = 130 + 35 * np.sin(10 * xx + 5 * yy)
    rainbow_g = 145 + 40 * np.cos(8 * xx - 6 * yy)
    rainbow_r = 120 + 50 * np.sin(6 * xx + 12 * yy)
    
    # Apply sheen layer
    for c, col in enumerate([rainbow_b, rainbow_g, rainbow_r]):
        img[:, :, c] = img[:, :, c] * (1.0 - sheen_mask * 0.75) + col * (sheen_mask * 0.75)
        
    # Apply dark thick crude core (Dark bitumen/tar black-brown: B: 30, G: 32, R: 38)
    img[:, :, 0] = img[:, :, 0] * (1.0 - core_mask * 0.88) + 28 * (core_mask * 0.88)
    img[:, :, 1] = img[:, :, 1] * (1.0 - core_mask * 0.88) + 32 * (core_mask * 0.88)
    img[:, :, 2] = img[:, :, 2] * (1.0 - core_mask * 0.88) + 40 * (core_mask * 0.88)
    
    return np.clip(img, 0, 255).astype(np.uint8)

def generate_clean_ocean_sar_image(width: int = 512, height: int = 512, seed: int = 7) -> np.ndarray:
    """
    Generates clean ocean Synthetic Aperture Radar image with natural homogeneous sea clutter.
    """
    np.random.seed(seed)
    base_sea = np.random.rayleigh(scale=35.0, size=(height, width))
    base_sea = cv2.GaussianBlur(base_sea, (3, 3), 0)
    
    x = np.linspace(0, 8 * np.pi, width)
    y = np.linspace(0, 8 * np.pi, height)
    xx, yy = np.meshgrid(x, y)
    waves = 12 * np.sin(0.3 * xx + 0.4 * yy) + 8 * np.cos(0.2 * xx - 0.3 * yy)
    
    sea = np.clip(base_sea + waves + 88, 15, 240).astype(np.uint8)
    return cv2.cvtColor(sea, cv2.COLOR_GRAY2BGR)

def generate_algal_bloom_image(width: int = 512, height: int = 512, seed: int = 55) -> np.ndarray:
    """
    Generates look-alike optical imagery: Marine Algal Bloom / Sargassum green filaments.
    """
    np.random.seed(seed)
    img = np.zeros((height, width, 3), dtype=np.float32)
    
    # Base blue sea
    img[:, :, 0] = 150 + np.random.normal(0, 5, (height, width))  # B
    img[:, :, 1] = 95 + np.random.normal(0, 4, (height, width))   # G
    img[:, :, 2] = 30 + np.random.normal(0, 3, (height, width))   # R
    
    # Algae filament patches (Green chlorophyll-rich vegetation)
    algae_mask = np.zeros((height, width), dtype=np.float32)
    for _ in range(6):
        cx = np.random.randint(80, width - 80)
        cy = np.random.randint(80, height - 80)
        axes = (np.random.randint(40, 110), np.random.randint(15, 35))
        angle = np.random.randint(0, 180)
        cv2.ellipse(algae_mask, (cx, cy), axes, angle, 0, 360, 1.0, -1)
        
    algae_mask = cv2.GaussianBlur(algae_mask, (19, 19), 0)
    
    # Algae coloration (B: 45, G: 165, R: 95)
    img[:, :, 0] = img[:, :, 0] * (1.0 - algae_mask) + 40 * algae_mask
    img[:, :, 1] = img[:, :, 1] * (1.0 - algae_mask) + 165 * algae_mask
    img[:, :, 2] = img[:, :, 2] * (1.0 - algae_mask) + 90 * algae_mask
    
    return np.clip(img, 0, 255).astype(np.uint8)

def generate_ship_wake_image(width: int = 512, height: int = 512, seed: int = 99) -> np.ndarray:
    """
    Generates look-alike imagery: Ship turbulent Kelvin wake with bright aerated foam.
    """
    np.random.seed(seed)
    img = np.zeros((height, width, 3), dtype=np.float32)
    
    # Dark blue open ocean
    img[:, :, 0] = 160 + np.random.normal(0, 5, (height, width))
    img[:, :, 1] = 100 + np.random.normal(0, 4, (height, width))
    img[:, :, 2] = 35 + np.random.normal(0, 3, (height, width))
    
    # V-shaped wake pattern
    wake_mask = np.zeros((height, width), dtype=np.float32)
    cv2.line(wake_mask, (width // 2, 80), (width // 2 - 140, height - 40), 1.0, 14)
    cv2.line(wake_mask, (width // 2, 80), (width // 2 + 140, height - 40), 1.0, 14)
    cv2.line(wake_mask, (width // 2, 80), (width // 2, height - 20), 1.0, 18)
    
    wake_mask = cv2.GaussianBlur(wake_mask, (15, 15), 0)
    
    # Frothy white-cyan wake bubbles
    img[:, :, 0] = img[:, :, 0] * (1.0 - wake_mask) + 245 * wake_mask
    img[:, :, 1] = img[:, :, 1] * (1.0 - wake_mask) + 240 * wake_mask
    img[:, :, 2] = img[:, :, 2] * (1.0 - wake_mask) + 225 * wake_mask
    
    return np.clip(img, 0, 255).astype(np.uint8)

def generate_all_sample_assets(output_dir: str) -> Dict[str, str]:
    """
    Generate all sample test benchmark imagery into static directory.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    samples = {
        "sar_spill_01.png": {
            "fn": generate_sar_oil_spill_image,
            "title": "Sentinel-1 SAR Radar Slick",
            "type": "SAR",
            "description": "Satellite Synthetic Aperture Radar dark-spot anomaly with wave damping."
        },
        "drone_optical_01.png": {
            "fn": generate_drone_optical_slick_image,
            "title": "Drone Aerial Hydrocarbon Slick",
            "type": "Optical",
            "description": "High-resolution drone RGB capture showing crude core and iridescent sheen."
        },
        "clean_ocean_sar_01.png": {
            "fn": generate_clean_ocean_sar_image,
            "title": "Clean Ocean Surface (SAR)",
            "type": "SAR",
            "description": "Homogeneous open water backscatter with normal sea clutter distribution."
        },
        "lookalike_algal_bloom.png": {
            "fn": generate_algal_bloom_image,
            "title": "Look-alike: Algal Bloom (Sargassum)",
            "type": "Optical",
            "description": "Biogenic vegetative bloom exhibiting high chlorophyll green/NIR reflectance."
        },
        "lookalike_ship_wake.png": {
            "fn": generate_ship_wake_image,
            "title": "Look-alike: Ship Kelvin Wake",
            "type": "Optical",
            "description": "Turbulent aeration foam and bubble tracks behind a marine vessel."
        }
    }
    
    file_map = {}
    for filename, meta in samples.items():
        file_dest = out_path / filename
        img = meta["fn"]()
        cv2.imwrite(str(file_dest), img)
        file_map[filename] = {
            "filename": filename,
            "title": meta["title"],
            "type": meta["type"],
            "description": meta["description"],
            "url": f"/static/samples/{filename}"
        }
        
    return file_map
