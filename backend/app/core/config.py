"""
MarineGuard AI - Configuration Module
"""

import os
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseModel as BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "MarineGuard AI"
    VERSION: str = "2.0.0"
    API_PREFIX: str = "/api"
    DESCRIPTION: str = "Autonomous Maritime Oil-Spill Detection, Vessel Attribution & Ecological Impact System (SIH 2026 PS-1655)"
    
    # Database URL - defaults to local sqlite database with fallback, or postgresql if POSTGRES_URI is supplied
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./marineguard.db")
    
    # Model Weights
    UNET_MODEL_PATH: str = os.getenv("UNET_MODEL_PATH", "models/unet_sar_oilspill.pth")
    
    # Demo & Simulation Flags
    DEMO_MODE: bool = True
    ALLOW_ORIGIN_ALL: bool = True


settings = Settings()
