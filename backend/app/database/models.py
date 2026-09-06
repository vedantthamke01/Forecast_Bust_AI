"""
SQLAlchemy ORM Data Models for Forecast Bust Detection Platform.
Enforces typed schemas across locations, forecasts, references, errors,
bust labels, predictions, models, datasets, and pipeline execution runs.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, Float, String, Boolean, DateTime,
    ForeignKey, Text, Index
)
from sqlalchemy.orm import relationship
from backend.app.database.database import Base


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    city = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=True, index=True)
    state = Column(String(100), nullable=True, index=True)
    country = Column(String(100), default="India", nullable=False)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    elevation = Column(Float, default=0.0)  # meters
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_location_lat_lon", "latitude", "longitude"),
    )


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    provider = Column(String(50), nullable=False)  # open-meteo, ecmwf, gfs, google
    model = Column(String(50), nullable=False)     # ncum, ifs, gfs, ensemble
    initialization_time = Column(DateTime, nullable=False, index=True)
    valid_time = Column(DateTime, nullable=False, index=True)
    lead_hours = Column(Integer, nullable=False, index=True)  # 24 to 240 (Day 1 to 10)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)

    # Core NWP Variables
    temperature_2m = Column(Float, nullable=True)          # Celsius
    precipitation = Column(Float, nullable=True)           # mm/24h
    wind_speed_10m = Column(Float, nullable=True)          # m/s
    pressure_msl = Column(Float, nullable=True)            # hPa
    relative_humidity_2m = Column(Float, nullable=True)    # %
    cloud_cover = Column(Float, nullable=True)             # %

    # Ensemble & Run Revision features
    ensemble_spread = Column(Float, default=0.0)
    run_revision = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_forecast_init_valid", "initialization_time", "valid_time"),
        Index("idx_forecast_coords_lead", "latitude", "longitude", "lead_hours"),
    )


class ReferenceWeather(Base):
    __tablename__ = "reference_weather"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    source = Column(String(50), nullable=False)  # era5, imd_station, reanalysis
    valid_time = Column(DateTime, nullable=False, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)

    # Observed / Reanalysis Variables
    temperature_2m = Column(Float, nullable=True)
    precipitation = Column(Float, nullable=True)
    wind_speed_10m = Column(Float, nullable=True)
    pressure_msl = Column(Float, nullable=True)
    relative_humidity_2m = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_reference_time_coords", "valid_time", "latitude", "longitude"),
    )


class ForecastError(Base):
    __tablename__ = "forecast_errors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    forecast_id = Column(Integer, ForeignKey("forecasts.id"), nullable=True)
    reference_id = Column(Integer, ForeignKey("reference_weather.id"), nullable=True)
    variable = Column(String(50), nullable=False, index=True)  # precipitation, temperature, wind, pressure
    lead_hours = Column(Integer, nullable=False, index=True)

    forecast_value = Column(Float, nullable=False)
    reference_value = Column(Float, nullable=False)
    absolute_error = Column(Float, nullable=False)
    relative_error = Column(Float, nullable=True)
    normalized_error = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class BustLabel(Base):
    __tablename__ = "bust_labels"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    forecast_id = Column(Integer, ForeignKey("forecasts.id"), nullable=True)
    variable = Column(String(50), nullable=False, index=True)
    lead_hours = Column(Integer, nullable=False, index=True)
    region = Column(String(100), default="India", nullable=False)

    is_bust = Column(Boolean, nullable=False, index=True)
    bust_severity = Column(String(20), default="NONE")  # NONE, MODERATE, SEVERE, EXTREME
    threshold_method = Column(String(50), nullable=False)  # ABSOLUTE, PERCENTILE, LEAD_TIME_DYNAMIC, COMPOUND
    threshold_value = Column(Float, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model_version = Column(String(50), nullable=False, index=True)
    prediction_time = Column(DateTime, default=datetime.utcnow, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    lead_hours = Column(Integer, nullable=False, index=True)
    variable = Column(String(50), nullable=False)

    forecast_value = Column(Float, nullable=False)
    bust_probability = Column(Float, nullable=False)       # 0.0 to 1.0 (Calibrated)
    reliability_score = Column(Float, nullable=False)      # 0.0 to 1.0
    risk_category = Column(String(20), nullable=False)     # LOW, MODERATE, HIGH, VERY_HIGH
    prediction_explanation = Column(Text, nullable=True)   # JSON string with SHAP values & factors


class ModelRecord(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model_version = Column(String(50), unique=True, nullable=False, index=True)
    training_dataset_version = Column(String(50), nullable=False)
    training_period = Column(String(100), nullable=False)
    feature_version = Column(String(50), default="f_v1")
    algorithm = Column(String(100), nullable=False)        # LightGBM, LogisticRegression
    metrics = Column(Text, nullable=False)                 # JSON string with PR-AUC, ROC-AUC, F1, etc.
    calibration_metrics = Column(Text, nullable=False)     # JSON string with Brier, ECE
    creation_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="CANDIDATE")       # CANDIDATE, VALIDATED, PRODUCTION, RETIRED
    artifact_path = Column(String(255), nullable=False)


class DatasetRecord(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    version = Column(String(50), unique=True, nullable=False, index=True)
    source = Column(String(100), nullable=False)           # ERA5 + Open-Meteo Ensemble
    start_date = Column(String(20), nullable=False)
    end_date = Column(String(20), nullable=False)
    variables = Column(Text, nullable=False)               # JSON array of variables
    rows = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    checksum = Column(String(64), nullable=True)
    status = Column(String(20), default="READY")           # READY, PENDING, FAILED


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(String(64), unique=True, nullable=False, index=True)
    task = Column(String(50), nullable=False)              # DOWNLOAD, UPDATE, QC, LABEL, TRAIN, RETRAIN
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(20), default="RUNNING")         # RUNNING, SUCCESS, FAILED
    records_downloaded = Column(Integer, default=0)
    records_processed = Column(Integer, default=0)
    errors = Column(Text, nullable=True)
    dataset_version = Column(String(50), nullable=True)
    model_version = Column(String(50), nullable=True)
