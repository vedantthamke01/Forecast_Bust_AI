"""
Tests for Extended Forecast Horizons (Day 3 to Day 30) and Non-Linear Saturation Thresholding.
Verifies that thresholds for Day 11-30 remain physically reasonable and do not explode.
"""
import pytest
import pandas as pd
import numpy as np
from data_pipeline.labeler import BustLabeler, get_lead_time_group


def test_lead_time_group_classification():
    """Verify that lead horizons 24h to 720h are classified into principled regimes."""
    # Day 1-2: 24h, 48h
    assert get_lead_time_group(24) == "Day 1-2"
    assert get_lead_time_group(48) == "Day 1-2"

    # Day 3-5: 72h, 96h, 120h
    assert get_lead_time_group(72) == "Day 3-5"
    assert get_lead_time_group(96) == "Day 3-5"
    assert get_lead_time_group(120) == "Day 3-5"

    # Day 6-10: 144h, 168h, 240h
    assert get_lead_time_group(144) == "Day 6-10"
    assert get_lead_time_group(240) == "Day 6-10"

    # Day 11-15: 264h to 360h
    assert get_lead_time_group(264) == "Day 11-15"
    assert get_lead_time_group(360) == "Day 11-15"

    # Day 16-20: 384h to 480h
    assert get_lead_time_group(384) == "Day 16-20"
    assert get_lead_time_group(480) == "Day 16-20"

    # Day 21-30: 504h to 720h
    assert get_lead_time_group(504) == "Day 21-30"
    assert get_lead_time_group(720) == "Day 21-30"


def test_saturation_threshold_bounds():
    """
    Verify that saturation thresholding stays within physically plausible bounds.
    At Day 30 (720h), rainfall threshold must remain <= 60 mm (not 112 mm).
    """
    labeler = BustLabeler(strategy="lead_time_saturation")

    # Day 1 (24h) base threshold
    th_day1 = labeler.get_saturation_threshold(25.0, 24)
    assert th_day1 == 25.0

    # Day 4 (96h)
    th_day4 = labeler.get_saturation_threshold(25.0, 96)
    assert 30.0 <= th_day4 <= 40.0

    # Day 10 (240h)
    th_day10 = labeler.get_saturation_threshold(25.0, 240)
    assert 40.0 <= th_day10 <= 52.0

    # Day 30 (720h)
    th_day30 = labeler.get_saturation_threshold(25.0, 720)
    assert 50.0 <= th_day30 <= 56.0, f"Day 30 threshold unphysically large: {th_day30}"

    # Temperature threshold saturation check
    th_temp_day30 = labeler.get_saturation_threshold(4.0, 720, alpha=0.85)
    assert 6.0 <= th_temp_day30 <= 8.0, f"Day 30 temp threshold unphysically large: {th_temp_day30}"


def test_label_dataframe_with_extended_horizons():
    """Test full dataframe labeling with Day 3 to Day 30 records."""
    df = pd.DataFrame({
        "lead_hours": [72, 120, 240, 360, 480, 720],
        "error_precipitation": [35.0, 15.0, 60.0, 20.0, 70.0, 10.0],
        "error_temperature": [2.0, 5.5, 3.0, 8.0, 2.0, 1.0],
        "error_wind": [3.0, 4.0, 5.0, 6.0, 16.0, 2.0]
    })

    labeler = BustLabeler(strategy="lead_time_saturation")
    labeled = labeler.label_dataframe(df)

    assert "is_bust" in labeled.columns
    assert "lead_time_group" in labeled.columns
    assert "operational_threshold" in labeled.columns

    # Verify group assignments
    assert list(labeled["lead_time_group"]) == ["Day 3-5", "Day 3-5", "Day 6-10", "Day 11-15", "Day 16-20", "Day 21-30"]

    # Verify bust flagging is boolean (0 or 1)
    assert set(labeled["is_bust"].unique()).issubset({0, 1})
