"""
Tests for Genuine NWP Forecast Retrieval, ERA5 Alignment, and Provenance Tracking.
Verifies:
1. Hard valid-time equality constraint
2. Hard lead-time consistency constraint (valid_time - initialization_time == lead_hours)
3. Unmatched forecast rejection and tracking
4. Provenance tracking (REAL vs SYNTHETIC)
5. Zero-leakage feature isolation
"""
import pytest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from data_pipeline.aligner import ForecastReferenceAligner
from data_pipeline.providers.historical_nwp import HistoricalNWPProvider
from data_pipeline.quality import assess_dataframe_quality
from ml_pipeline.features import extract_features, check_data_leakage
from ml_pipeline.train import temporal_split


def test_aligner_hard_valid_time_constraint():
    """Validates that forecasts and references with different valid times are NEVER paired."""
    aligner = ForecastReferenceAligner(spatial_tolerance_deg=0.5)

    # Forecast valid for 2024-06-01 12:00
    fc = [{
        "provider": "open-meteo-previous-runs",
        "model": "gfs-seamless",
        "initialization_time": "2024-05-28T12:00:00",
        "valid_time": "2024-06-01T12:00:00",
        "lead_hours": 96,
        "latitude": 18.52,
        "longitude": 73.85,
        "temperature_2m": 29.5,
        "precipitation": 12.0
    }]

    # Reference valid for 2024-06-02 12:00 (mismatched valid time!)
    ref = [{
        "source": "era5-reanalysis",
        "valid_time": "2024-06-02T12:00:00",
        "latitude": 18.52,
        "longitude": 73.85,
        "temperature_2m": 27.0,
        "precipitation": 15.0
    }]

    df = aligner.align(fc, ref)
    # Must reject the match because valid times do not match
    assert len(df) == 0
    assert aligner.alignment_stats["unmatched_forecasts"] == 1
    assert aligner.alignment_stats["unmatched_temporal"] == 1


def test_aligner_hard_lead_time_constraint():
    """Validates that inconsistent lead_hours (not matching valid - init) is rejected."""
    aligner = ForecastReferenceAligner(spatial_tolerance_deg=0.5)

    # Inconsistent lead hours: valid - init = 96h, but lead_hours claimed = 24h
    fc = [{
        "provider": "open-meteo-previous-runs",
        "model": "gfs-seamless",
        "initialization_time": "2024-05-28T12:00:00",
        "valid_time": "2024-06-01T12:00:00",
        "lead_hours": 24,  # INCONSISTENT!
        "latitude": 18.52,
        "longitude": 73.85,
        "temperature_2m": 29.5,
        "precipitation": 12.0
    }]

    ref = [{
        "source": "era5-reanalysis",
        "valid_time": "2024-06-01T12:00:00",
        "latitude": 18.52,
        "longitude": 73.85,
        "temperature_2m": 27.0,
        "precipitation": 15.0
    }]

    df = aligner.align(fc, ref)
    # Inconsistent lead time must be rejected
    assert len(df) == 0
    assert aligner.alignment_stats["unmatched_lead_inconsistency"] == 1


def test_aligner_genuine_pair_success_and_provenance():
    """Validates correct error calculation and provenance assignment when pair is authentic."""
    aligner = ForecastReferenceAligner(spatial_tolerance_deg=0.5)

    fc = [{
        "provider": "open-meteo-previous-runs",
        "model": "gfs-seamless",
        "initialization_time": "2024-05-28T12:00:00",
        "valid_time": "2024-06-01T12:00:00",
        "lead_hours": 96,
        "latitude": 18.52,
        "longitude": 73.85,
        "temperature_2m": 30.5,
        "precipitation": 45.0,
        "wind_speed_10m": 12.0,
        "pressure_msl": 1008.0
    }]

    ref = [{
        "source": "era5-reanalysis",
        "valid_time": "2024-06-01T12:00:00",
        "latitude": 18.52,
        "longitude": 73.85,
        "temperature_2m": 28.0,
        "precipitation": 20.0,
        "wind_speed_10m": 8.0,
        "pressure_msl": 1010.0
    }]

    df = aligner.align(fc, ref)
    assert len(df) == 1
    row = df.iloc[0]

    # Provenance
    assert row["data_type"] == "REAL"
    assert row["forecast_provider"] == "open-meteo-previous-runs"
    assert row["reference_source"] == "era5-reanalysis"

    # Real errors
    assert row["error_temperature"] == pytest.approx(2.5, abs=1e-2)
    assert row["error_precipitation"] == pytest.approx(25.0, abs=1e-2)
    assert row["error_wind"] == pytest.approx(4.0, abs=1e-2)
    assert row["error_pressure"] == pytest.approx(2.0, abs=1e-2)


def test_strict_anti_leakage_on_aligned_dataset():
    """Proves that ground-truth reference and error fields cannot enter the feature matrix."""
    aligned_df = pd.DataFrame([{
        "initialization_time": "2024-05-28T12:00:00",
        "valid_time": "2024-06-01T12:00:00",
        "lead_hours": 96,
        "latitude": 18.52,
        "longitude": 73.85,
        "forecast_temperature": 30.5,
        "forecast_precipitation": 45.0,
        "forecast_wind": 12.0,
        "forecast_pressure": 1008.0,
        "forecast_humidity": 80.0,
        "forecast_cloud_cover": 75.0,
        "ensemble_spread": 2.2,
        "run_revision": 0.5,
        # Realized ground-truth and error fields (MUST BE EXCLUDED FROM X)
        "reference_temperature": 28.0,
        "reference_precipitation": 20.0,
        "error_temperature": 2.5,
        "error_precipitation": 25.0,
        "is_bust": 1
    }])

    X, y = extract_features(aligned_df, is_training=True)

    # Verification: check all columns in feature matrix X
    for col in X.columns:
        col_lower = col.lower()
        assert "reference" not in col_lower, f"Leakage detected: {col}"
        assert "actual" not in col_lower, f"Leakage detected: {col}"
        assert "error" not in col_lower, f"Leakage detected: {col}"
        assert "observed" not in col_lower, f"Leakage detected: {col}"
        assert "target" not in col_lower, f"Leakage detected: {col}"
        assert "is_bust" not in col_lower, f"Target in feature matrix: {col}"

    assert len(y) == 1
    assert y.iloc[0] == 1


def test_chronological_split_zero_overlap():
    """Proves that chronological splitting completely isolates unseen future time horizons."""
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    df = pd.DataFrame({
        "valid_time": [d.strftime("%Y-%m-%d %H:%M:%S") for d in dates],
        "lead_hours": [96] * 100,
        "is_bust": [0] * 80 + [1] * 20
    })

    df_train, df_val, df_test, split_ranges = temporal_split(df)

    max_train_date = pd.to_datetime(df_train["valid_time"]).max()
    min_val_date = pd.to_datetime(df_val["valid_time"]).min()
    max_val_date = pd.to_datetime(df_val["valid_time"]).max()
    min_test_date = pd.to_datetime(df_test["valid_time"]).min()

    # Assert strict chronological ordering: train < val < test
    assert max_train_date < min_val_date, f"Train overlaps with Val: {max_train_date} >= {min_val_date}"
    assert max_val_date < min_test_date, f"Val overlaps with Test: {max_val_date} >= {min_test_date}"
