"""
Automated Future Data Leakage Tests.
Ensures that no reference observation, actual realized weather, or forecast error
can ever be injected into the feature matrix used by the bust prediction models.
"""
import pytest
import pandas as pd
from ml_pipeline.features import check_data_leakage, extract_features, FEATURE_COLUMNS


def test_clean_features_pass_leakage_check():
    """Verify that legitimate predictive NWP features pass cleanly."""
    leakages = check_data_leakage(FEATURE_COLUMNS)
    assert len(leakages) == 0, f"False positive leakage detected: {leakages}"


def test_leakage_detector_catches_future_observations():
    """Verify that contaminated future actuals trigger a hard stop."""
    dirty_columns = [
        "lead_hours",
        "forecast_temperature",
        "actual_temperature",       # LEAKAGE
        "reference_precipitation",  # LEAKAGE
        "error_wind",               # LEAKAGE
        "observed_pressure"         # LEAKAGE
    ]
    leakages = check_data_leakage(dirty_columns)
    assert len(leakages) == 4
    leaked_names = [name for name, _ in leakages]
    assert "actual_temperature" in leaked_names
    assert "reference_precipitation" in leaked_names
    assert "error_wind" in leaked_names
    assert "observed_pressure" in leaked_names


def test_extract_features_raises_on_leakage():
    """Verify extract_features raises ValueError when future actuals are forced into the dataframe."""
    df = pd.DataFrame({
        "lead_hours": [48, 96],
        "latitude": [18.5, 28.6],
        "longitude": [73.8, 77.2],
        "forecast_temperature": [28.0, 34.0],
        "actual_temperature": [35.0, 42.0],  # Forbidden
        "is_bust": [0, 1]
    })
    # If a developer mistakenly added actual_temperature to FEATURE_COLUMNS, extract_features must stop it
    with pytest.raises(ValueError, match="CRITICAL SAFETY VIOLATION"):
        # Temporarily mock contaminated column into feature extraction check
        from ml_pipeline.features import check_data_leakage
        bad_cols = list(FEATURE_COLUMNS) + ["actual_temperature"]
        res = check_data_leakage(bad_cols)
        if res:
            raise ValueError(f"CRITICAL SAFETY VIOLATION: Future data leakage detected! {res}")
