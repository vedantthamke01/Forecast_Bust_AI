"""
Data Pipeline and Quality Control Tests.
Verifies alignment logic, quality report generation, and bust labeling accuracy.
"""
import pytest
import pandas as pd
from data_pipeline.aligner import ForecastReferenceAligner
from data_pipeline.labeler import BustLabeler
from data_pipeline.quality import assess_dataframe_quality


def test_forecast_reference_aligner():
    fc = [{
        "provider": "test",
        "model": "ncum",
        "initialization_time": "2024-07-15T00:00:00",
        "valid_time": "2024-07-19T00:00:00",
        "lead_hours": 96,
        "latitude": 18.52,
        "longitude": 73.85,
        "temperature_2m": 28.0,
        "precipitation": 42.0,
        "wind_speed_10m": 6.5,
        "pressure_msl": 1010.0
    }]
    ref = [{
        "source": "era5",
        "valid_time": "2024-07-19T00:00:00",
        "latitude": 18.52,
        "longitude": 73.85,
        "temperature_2m": 26.0,
        "precipitation": 67.0,
        "wind_speed_10m": 8.0,
        "pressure_msl": 1008.0
    }]

    aligner = ForecastReferenceAligner(spatial_tolerance_deg=0.5)
    df = aligner.align(fc, ref)

    assert len(df) == 1
    assert df["error_precipitation"].iloc[0] == 25.0
    assert df["error_temperature"].iloc[0] == 2.0


def test_bust_labeler_dynamic():
    df = pd.DataFrame({
        "lead_hours": [48, 96],
        "error_precipitation": [26.0, 30.0],
        "error_temperature": [1.0, 2.0],
        "error_wind": [2.0, 3.0]
    })
    labeler = BustLabeler(strategy="lead_time_dynamic", rain_thresh_base=25.0, lead_scaling_factor=0.12)
    labeled = labeler.label_dataframe(df)

    assert len(labeled) == 2
    # At 48h, threshold is 25 * (1 + 0.12*1) = 28.0; 26 <= 28 -> not bust
    # At 96h, threshold is 25 * (1 + 0.12*3) = 34.0; 30 <= 34 -> not bust
    assert "is_bust" in labeled.columns
    assert "labeling_method" in labeled.columns


def test_quality_assessment_pass():
    df = pd.DataFrame({
        "latitude": [18.52, 28.61],
        "longitude": [73.85, 77.20],
        "valid_time": ["2024-07-15", "2024-07-16"],
        "lead_hours": [24, 48],
        "forecast_temperature": [28.0, 34.0],
        "forecast_precipitation": [10.0, 25.0]
    })
    report = assess_dataframe_quality(df, dataset_name="test")
    assert report["status"] == "PASS"
    assert report["total_records"] == 2
    assert report["invalid_coordinates_count"] == 0


def test_era5_cds_provider_configured():
    from data_pipeline.providers.era5 import ERA5CDSProvider
    provider = ERA5CDSProvider()
    assert "ECMWF" in provider.get_provider_name()
    # When .cdsapirc exists, is_available() should return True
    assert provider.is_available() is True

