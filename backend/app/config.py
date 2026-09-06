"""
Application Configuration and Settings.
Supports loading from .env, environment variables, and system defaults.
"""
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "sih26079_ncmrwf_secret_dev_key_2026"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Database
    # Supports SQLite for instant local execution & PostgreSQL for production
    DATABASE_URL: str = "sqlite+aiosqlite:///./data.db"

    # Weather Providers
    GOOGLE_WEATHER_API_KEY: Optional[str] = None
    CDS_API_URL: Optional[str] = "https://cds.climate.copernicus.eu/api/v2"
    CDS_API_KEY: Optional[str] = None
    OPEN_METEO_ENABLED: bool = True
    DEMO_MODE: bool = False

    # India Synoptic Bounding Box
    DEFAULT_REGION_NORTH: float = 37.5
    DEFAULT_REGION_SOUTH: float = 6.5
    DEFAULT_REGION_WEST: float = 68.0
    DEFAULT_REGION_EAST: float = 97.5

    # ML Pipeline Settings
    DATASET_VERSION_DEFAULT: str = "dataset_v001"
    MODEL_VERSION_DEFAULT: str = "model_v001"
    MIN_SAMPLES_FOR_RETRAIN: int = 500

    # Model Acceptance Gate
    ACCEPTANCE_MIN_PR_AUC: float = 0.55
    ACCEPTANCE_MAX_BRIER_SCORE: float = 0.25
    ACCEPTANCE_MAX_ECE: float = 0.20

    # Standard Variables
    VARIABLES: List[str] = Field(
        default=["temperature", "precipitation", "wind", "pressure", "humidity", "cloud_cover"]
    )


settings = Settings()
