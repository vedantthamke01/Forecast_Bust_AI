"""
Feature Engineering Engine for Forecast Bust Prediction.
CRITICAL SAFETY RULE: Strictly prevents target and future data leakage.
Only features available at forecast initialization time T are computed.
"""
from typing import List, Tuple
import pandas as pd
import numpy as np


FORBIDDEN_LEAKAGE_SUBSTRINGS = [
    "actual", "reference", "observed", "error", "ground_truth", "truth",
    "target", "label", "future", "verification", "bias", "valid_val",
    "delta_obs", "lead_inconsistency", "is_bust", "severity"
]

# Standard 17 baseline features for backwards compatibility
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

# Extended 21 global features including Koppen climate regime, solar zenith, and non-linear horizon scaling
GLOBAL_FEATURE_COLUMNS = FEATURE_COLUMNS + [
    "solar_zenith_noon",
    "climate_regime_code",
    "is_mountain",
    "lead_scaling_norm"
]


def check_data_leakage(columns: List[str]) -> List[Tuple[str, str]]:
    """
    Automated Data Leakage Detector.
    Scans feature column names for any forbidden substring that represents
    realized future ground truth or calculation errors.
    Returns list of offending column names.
    """
    detected_leakages = []
    for col in columns:
        col_lower = col.lower().strip()
        for pattern in FORBIDDEN_LEAKAGE_SUBSTRINGS:
            if pattern in col_lower:
                detected_leakages.append((col, pattern))
                break
    return detected_leakages


def extract_features(
    df: pd.DataFrame,
    is_training: bool = False,
    feature_columns: List[str] = None
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Extracts and standardizes physically relevant predictor features available strictly at initialization T0.
    If is_training=True, also validates target variable and returns (X, y).
    """
    cols_to_use = feature_columns if feature_columns is not None else FEATURE_COLUMNS

    # STRICT LEAKAGE AUDIT UPFRONT
    leakages = check_data_leakage(list(cols_to_use))
    if leakages:
        raise ValueError(
            f"CRITICAL SAFETY VIOLATION: Future data leakage detected in feature matrix! "
            f"Offending columns: {leakages}"
        )

    df = df.copy()

    # Time-based cyclical and astronomical features
    if "initialization_time" in df.columns:
        init_dt = pd.to_datetime(df["initialization_time"])
        day_of_year = init_dt.dt.dayofyear
        df["sin_day_of_year"] = np.sin(2 * np.pi * day_of_year / 365.25)
        df["cos_day_of_year"] = np.cos(2 * np.pi * day_of_year / 365.25)
        df["month"] = init_dt.dt.month
        doy_series = day_of_year
    else:
        df["sin_day_of_year"] = 0.0
        df["cos_day_of_year"] = 1.0
        df["month"] = 7
        doy_series = pd.Series([196] * len(df), index=df.index)

    if "latitude" in df.columns:
        lats = pd.to_numeric(df["latitude"], errors="coerce").fillna(20.0)
    else:
        lats = pd.Series([20.0] * len(df), index=df.index)

    if "longitude" in df.columns:
        lons = pd.to_numeric(df["longitude"], errors="coerce").fillna(78.0)
    else:
        lons = pd.Series([78.0] * len(df), index=df.index)

    months = df["month"]

    # Global multi-region monsoon activity detection (strictly T0 spatial & calendar check)
    is_monsoon = np.zeros(len(df), dtype=int)
    # 1. Indian SW Monsoon: June to September (months 6 to 9)
    in_india_monsoon = (lats >= 6.0) & (lats <= 36.0) & (lons >= 68.0) & (lons <= 98.0) & months.isin([6, 7, 8, 9])
    # 2. Australian Monsoon: December to March (months 12, 1, 2, 3)
    in_aus_monsoon = (lats >= -25.0) & (lats <= -10.0) & (lons >= 110.0) & (lons <= 150.0) & months.isin([12, 1, 2, 3])
    # 3. West African Monsoon: July to September (months 7, 8, 9)
    in_wa_monsoon = (lats >= 5.0) & (lats <= 20.0) & (lons >= -18.0) & (lons <= 25.0) & months.isin([7, 8, 9])
    # 4. North American Monsoon: July to August (months 7, 8)
    in_na_monsoon = (lats >= 20.0) & (lats <= 35.0) & (lons >= -115.0) & (lons <= -100.0) & months.isin([7, 8])

    is_monsoon[in_india_monsoon | in_aus_monsoon | in_wa_monsoon | in_na_monsoon] = 1
    df["is_monsoon_season"] = is_monsoon

    # Solar declination & solar noon zenith angle proxy at T0
    rad_decl = 2.0 * np.pi * (doy_series + 10.0) / 365.25
    solar_declination = -23.44 * np.cos(rad_decl)
    df["solar_zenith_noon"] = np.abs(lats - solar_declination).round(2)

    # Macro Climate Regime classification (Tropical=0, Arid=1, Temperate=2, Continental=3, Polar/Alpine=4)
    if "elevation" in df.columns:
        elevs = pd.to_numeric(df["elevation"], errors="coerce").fillna(100.0)
    else:
        elevs = pd.Series([100.0] * len(df), index=df.index)

    abs_lats = np.abs(lats)
    regime_codes = np.full(len(df), 2, dtype=int)  # default Temperate (2)
    # Polar/Alpine: high latitudes or elevation >= 2000m
    regime_codes[(abs_lats >= 66.5) | (elevs >= 2000.0)] = 4
    # Tropical: low latitudes (< 23.5) without high elevation
    regime_codes[(abs_lats <= 23.5) & (elevs < 1500.0)] = 0
    # Arid: subtropical desert belts
    is_arid_zone = (abs_lats >= 15.0) & (abs_lats <= 38.0) & (
        ((lons >= -15.0) & (lons <= 60.0) & (lats > 12.0)) |
        ((lons >= 68.0) & (lons <= 76.0) & (lats >= 24.0) & (lats <= 32.0)) |
        ((lons >= -120.0) & (lons <= -100.0) & (lats >= 25.0) & (lats <= 38.0)) |
        ((lons >= 115.0) & (lons <= 145.0) & (lats >= -35.0) & (lats <= -18.0))
    )
    regime_codes[is_arid_zone] = 1
    # Continental: high-latitude northern interior
    is_continental = (lats >= 40.0) & ~((lons >= -15.0) & (lons <= 5.0))
    regime_codes[is_continental] = 3
    df["climate_regime_code"] = regime_codes
    df["is_mountain"] = (elevs >= 1000.0).astype(int)

    # Meteorological dynamic proxies
    if "forecast_pressure" in df.columns:
        df["pressure_anomaly"] = df["forecast_pressure"] - 1013.25
    else:
        df["pressure_anomaly"] = 0.0

    if "forecast_humidity" in df.columns and "forecast_temperature" in df.columns:
        df["temp_dew_depression_proxy"] = (100.0 - df["forecast_humidity"].clip(0, 100)) * 0.2
    else:
        df["temp_dew_depression_proxy"] = 5.0

    # Non-linear lead horizon saturation feature: tanh((tau - 24) / 168)
    if "lead_hours" in df.columns:
        lead_h = pd.to_numeric(df["lead_hours"], errors="coerce").fillna(24.0)
    else:
        lead_h = pd.Series([24.0] * len(df), index=df.index)
    df["lead_scaling_norm"] = np.tanh(np.maximum(0.0, lead_h - 24.0) / 168.0).round(4)

    # Fill defaults for missing target columns
    for col in cols_to_use:
        if col not in df.columns:
            df[col] = 0.0

    X = df[cols_to_use].copy()

    # Coerce to strictly numeric types
    for col in cols_to_use:
        X[col] = pd.to_numeric(X[col], errors="coerce")

    # Replace inf with NaN, then impute with medians / 0.0
    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.fillna(X.median(numeric_only=True)).fillna(0.0)

    y = None
    if is_training:
        if "is_bust" not in df.columns:
            raise ValueError("Training dataset must contain labeled 'is_bust' target column.")
        y = df["is_bust"].astype(int)

    return X, y
