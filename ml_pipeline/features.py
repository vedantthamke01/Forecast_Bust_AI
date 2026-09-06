"""
Feature Engineering Engine for Forecast Bust Prediction.
CRITICAL SAFETY RULE: Strictly prevents target and future data leakage.
Only features available at forecast initialization time T are computed.
"""
from typing import List, Tuple
import pandas as pd
import numpy as np


FORBIDDEN_LEAKAGE_SUBSTRINGS = [
    "actual", "reference", "observed", "error", "ground_truth", "target", "label"
]

FEATURE_COLUMNS = [
    "lead_hours",
    "latitude",
    "longitude",
    "forecast_temperature",
    "forecast_precipitation",
    "forecast_wind",
    "forecast_pressure",
    "forecast_humidity",
    "forecast_cloud_cover",
    "ensemble_spread",
    "run_revision",
    "sin_day_of_year",
    "cos_day_of_year",
    "month",
    "is_monsoon_season",
    "pressure_anomaly",
    "temp_dew_depression_proxy"
]


def check_data_leakage(columns: List[str]) -> List[str]:
    """
    Automated Data Leakage Detector.
    Scans feature column names for any forbidden substring that represents
    realized future ground truth or calculation errors.
    Returns list of offending column names.
    """
    detected_leakages = []
    for col in columns:
        col_lower = col.lower()
        # Allow target variable 'is_bust' during labeling/target extraction, but NEVER as input feature
        for pattern in FORBIDDEN_LEAKAGE_SUBSTRINGS:
            if pattern in col_lower:
                detected_leakages.append((col, pattern))
                break
    return detected_leakages


def extract_features(df: pd.DataFrame, is_training: bool = False) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Extracts and standardizes physically relevant predictor features.
    If is_training=True, also validates target variable and returns (X, y).
    """
    df = df.copy()

    # Time-based cyclical features
    if "initialization_time" in df.columns:
        init_dt = pd.to_datetime(df["initialization_time"])
        day_of_year = init_dt.dt.dayofyear
        df["sin_day_of_year"] = np.sin(2 * np.pi * day_of_year / 365.25)
        df["cos_day_of_year"] = np.cos(2 * np.pi * day_of_year / 365.25)
        df["month"] = init_dt.dt.month
        # Indian Southwest Monsoon season: June through September (months 6 to 9)
        df["is_monsoon_season"] = df["month"].isin([6, 7, 8, 9]).astype(int)
    else:
        df["sin_day_of_year"] = 0.0
        df["cos_day_of_year"] = 1.0
        df["month"] = 7
        df["is_monsoon_season"] = 1

    # Meteorological dynamic proxies
    # Pressure deviation from standard sea level (1013.25 hPa)
    if "forecast_pressure" in df.columns:
        df["pressure_anomaly"] = df["forecast_pressure"] - 1013.25
    else:
        df["pressure_anomaly"] = 0.0

    # Moisture saturation proxy (approximated from RH)
    if "forecast_humidity" in df.columns and "forecast_temperature" in df.columns:
        # High RH -> small depression; Low RH -> large depression
        df["temp_dew_depression_proxy"] = (100.0 - df["forecast_humidity"].clip(0, 100)) * 0.2
    else:
        df["temp_dew_depression_proxy"] = 5.0

    # Fill defaults for optional columns if missing
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = 0.0

    X = df[FEATURE_COLUMNS].copy()

    # STRICT LEAKAGE AUDIT
    leakages = check_data_leakage(list(X.columns))
    if leakages:
        raise ValueError(
            f"CRITICAL SAFETY VIOLATION: Future data leakage detected in feature matrix! "
            f"Offending columns: {leakages}"
        )

    # Impute missing values with median
    X = X.fillna(X.median(numeric_only=True)).fillna(0.0)

    y = None
    if is_training:
        if "is_bust" not in df.columns:
            raise ValueError("Training dataset must contain labeled 'is_bust' target column.")
        y = df["is_bust"].astype(int)

    return X, y
