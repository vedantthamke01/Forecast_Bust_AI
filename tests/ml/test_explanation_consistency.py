"""
Explainability & Natural-Language Summary Consistency Tests.
Verifies that natural-language summary text is strictly consistent with
the calibrated bust probability and final assigned risk level (LOW, MODERATE, HIGH, VERY HIGH).
Ensures zero contradictory claims (e.g. no 'elevated' language for LOW risk)
and verifies that feature attributions represent model contributions rather than physical causality.
"""
import pytest
import pandas as pd
from ml_pipeline.explainability import generate_scientific_summary, MeteorologicalExplainer
from backend.app.services.bust_service import BustPredictionService
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


def test_summary_low_risk_consistency():
    """LOW risk summaries must never use 'elevated' or 'concerning' language for overall risk."""
    amps = [
        {"feature": "forecast_precipitation", "description": "Forecasted 24h Precipitation (42.0 mm)", "shap_value": 0.048, "impact": "AMPLIFIER"},
        {"feature": "cos_day_of_year", "description": "Climatological Solar Position", "shap_value": 0.045, "impact": "AMPLIFIER"}
    ]
    mits = [
        {"feature": "forecast_wind", "description": "Forecasted 10m Wind Speed (6.0 m/s)", "shap_value": -0.21, "impact": "MITIGATOR"},
        {"feature": "latitude", "description": "Latitude Coordinate (18.5°N)", "shap_value": -0.14, "impact": "MITIGATOR"}
    ]

    summary = generate_scientific_summary(amps, mits, risk_level="LOW", bust_prob=0.007)

    assert "Overall bust risk is LOW (0.7%)" in summary
    assert "highly reliable" in summary
    assert "elevated" not in summary.lower()
    assert "concerning" not in summary.lower()
    assert "The main factors increasing the estimated risk are" in summary
    assert "Forecasted 24h Precipitation (42.0 mm)" in summary
    assert "The strongest mitigating factors are" in summary
    assert "Forecasted 10m Wind Speed (6.0 m/s)" in summary


def test_summary_moderate_risk_consistency():
    """MODERATE risk summaries must state moderate risk and reliability concerns."""
    amps = [
        {"feature": "lead_hours", "description": "Extended Forecast Horizon (Day 4)", "shap_value": 0.12, "impact": "AMPLIFIER"}
    ]
    mits = [
        {"feature": "forecast_pressure", "description": "Mean Sea Level Pressure (1012.0 hPa)", "shap_value": -0.05, "impact": "MITIGATOR"}
    ]

    summary = generate_scientific_summary(amps, mits, risk_level="MODERATE", bust_prob=0.352)

    assert "Overall bust risk is MODERATE (35.2%)" in summary
    assert "reliability concerns" in summary
    assert "The main factor increasing the estimated risk is Extended Forecast Horizon (Day 4)" in summary
    assert "The strongest mitigating factor is Mean Sea Level Pressure (1012.0 hPa)" in summary


def test_summary_high_risk_consistency():
    """HIGH risk summaries must state high risk and elevated risk of significant forecast error."""
    amps = [
        {"feature": "ensemble_spread", "description": "NWP Ensemble Spread / Dispersion (3.8)", "shap_value": 0.35, "impact": "AMPLIFIER"},
        {"feature": "run_revision", "description": "Consecutive Model Run Jumpiness / Revision (2.1)", "shap_value": 0.22, "impact": "AMPLIFIER"}
    ]
    mits = []

    summary = generate_scientific_summary(amps, mits, risk_level="HIGH", bust_prob=0.62)

    assert "Overall bust risk is HIGH (62.0%)" in summary
    assert "elevated risk of a significant forecast error" in summary
    assert "The main factors increasing the estimated risk are" in summary


def test_summary_very_high_risk_consistency():
    """VERY HIGH risk summaries must state severe risk."""
    amps = [
        {"feature": "ensemble_spread", "description": "NWP Ensemble Spread / Dispersion (5.0)", "shap_value": 0.45, "impact": "AMPLIFIER"}
    ]
    mits = []

    summary = generate_scientific_summary(amps, mits, risk_level="VERY HIGH", bust_prob=0.815)

    assert "Overall bust risk is VERY HIGH (81.5%)" in summary
    assert "severe risk of a significant forecast error" in summary


def test_summary_edge_cases():
    """Verifies edge cases: no amplifiers, no mitigators, only amplifiers, only mitigators, boundaries."""
    # 1. No amplifiers, no mitigators
    s1 = generate_scientific_summary([], [], risk_level="LOW", bust_prob=0.01)
    assert "Overall bust risk is LOW (1.0%)" in s1
    assert "Atmospheric indicators and model dispersion are within baseline climatological ranges." in s1

    # 2. Only mitigators
    mits = [{"feature": "forecast_wind", "description": "Forecasted 10m Wind Speed (7.0 m/s)", "impact": "MITIGATOR"}]
    s2 = generate_scientific_summary([], mits, risk_level="LOW", bust_prob=0.02)
    assert "Overall bust risk is LOW (2.0%)" in s2
    assert "The strongest mitigating factor is Forecasted 10m Wind Speed (7.0 m/s)." in s2
    assert "increasing" not in s2

    # 3. Only amplifiers
    amps = [{"feature": "lead_hours", "description": "Extended Forecast Horizon (Day 7)", "impact": "AMPLIFIER"}]
    s3 = generate_scientific_summary(amps, [], risk_level="MODERATE", bust_prob=0.45)
    assert "Overall bust risk is MODERATE (45.0%)" in s3
    assert "The main factor increasing the estimated risk is Extended Forecast Horizon (Day 7)." in s3
    assert "mitigating" not in s3

    # 4. Boundary thresholds
    # 0.249 -> LOW
    s_b1 = generate_scientific_summary([], [], risk_level="LOW", bust_prob=0.249)
    assert "Overall bust risk is LOW (24.9%)" in s_b1
    # 0.250 -> MODERATE
    s_b2 = generate_scientific_summary([], [], risk_level="MODERATE", bust_prob=0.25)
    assert "Overall bust risk is MODERATE (25.0%)" in s_b2
    # 0.499 -> MODERATE
    s_b3 = generate_scientific_summary([], [], risk_level="MODERATE", bust_prob=0.499)
    assert "Overall bust risk is MODERATE (49.9%)" in s_b3
    # 0.500 -> HIGH
    s_b4 = generate_scientific_summary([], [], risk_level="HIGH", bust_prob=0.50)
    assert "Overall bust risk is HIGH (50.0%)" in s_b4
    # 0.749 -> HIGH
    s_b5 = generate_scientific_summary([], [], risk_level="HIGH", bust_prob=0.749)
    assert "Overall bust risk is HIGH (74.9%)" in s_b5
    # 0.750 -> VERY HIGH
    s_b6 = generate_scientific_summary([], [], risk_level="VERY HIGH", bust_prob=0.75)
    assert "Overall bust risk is VERY HIGH (75.0%)" in s_b6


def test_predict_risk_service_consistency():
    """Verifies that BustPredictionService produces consistent explanation and metadata."""
    service = BustPredictionService()
    res = service.predict_risk(
        latitude=18.5204,
        longitude=73.8567,
        lead_hours=96,
        variable="precipitation",
        forecast_val=42.0,
        ensemble_spread=1.5
    )

    assert res["risk_level"] == "LOW"
    assert res["bust_probability"] < 0.25
    assert "explanation" in res
    exp = res["explanation"]
    assert "summary_text" in exp
    assert "Overall bust risk is LOW" in exp["summary_text"]
    assert "elevated" not in exp["summary_text"].lower()
    assert res["model_version"] == "model_real_v002"
    assert res["dataset_version"] == "dataset_real_v002"
    assert res["data_type"] == "REAL"
    assert res["is_demo_model"] is False


@pytest.mark.asyncio
async def test_api_risk_location_explanation_consistency():
    """Integration test: API endpoint returns consistent summary and preserved schema."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/risk/location?lat=18.5204&lon=73.8567&lead_hours=96&variable=precipitation&forecast_value=42&ensemble_spread=1.5")
        assert resp.status_code == 200
        data = resp.json()

        # Check required top-level schema fields
        for field in [
            "location", "forecast_horizon_hours", "forecast_day", "variable", "forecast_value",
            "bust_probability", "bust_probability_percentage", "reliability_score", "reliability_percentage",
            "risk_level", "risk_badge", "model_version", "dataset_version", "data_type",
            "forecast_source", "reference_source", "is_demo_model", "explanation", "disclaimer"
        ]:
            assert field in data, f"Missing required field: {field}"

        # Check explanation fields
        exp = data["explanation"]
        for exp_field in ["all_factors", "top_amplifiers", "top_mitigators", "summary_text"]:
            assert exp_field in exp, f"Missing explanation field: {exp_field}"

        # Check logical consistency
        assert data["risk_level"] == "LOW"
        assert data["bust_probability"] < 0.25
        assert "Overall bust risk is LOW" in exp["summary_text"]
        assert "elevated" not in exp["summary_text"].lower()
        assert "concerning" not in exp["summary_text"].lower()
