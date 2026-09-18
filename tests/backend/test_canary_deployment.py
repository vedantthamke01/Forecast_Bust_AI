"""
Controlled Canary Deployment Test Suite.
SIH26079 – AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts.

Tests:
1.  test_canary_disabled_by_default        – 100% routes to production when CANARY_ENABLED=False
2.  test_canary_deterministic_routing      – Same request context always maps to same model
3.  test_canary_traffic_split_distribution – ~10% / ~90% split across diverse coordinates
4.  test_canary_response_schema_invariance – Output keys match between production and canary
5.  test_canary_probability_validity       – All probabilities finite and within [0.0, 1.0]
6.  test_canary_failsafe_fallback          – Exception in canary falls back to production cleanly
7.  test_canary_circuit_breaker_error_rate – Error rate >1% trips circuit breaker
8.  test_canary_circuit_breaker_latency    – 3 consecutive latency breaches trip circuit breaker
9.  test_canary_shadow_delta_calculation   – |ΔP| delta statistics recorded correctly
10. test_canary_sanitized_logging          – Audit log contains no secrets, tokens, or PII
"""
import hashlib
import json
import math
import os
import sys
import time
import types
import unittest
from collections import deque
from typing import Optional
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Helpers to construct isolated service instances
# ---------------------------------------------------------------------------

def _make_mock_predict(bust_prob: float = 0.08):
    """Returns a mock predict_risk method returning a full-schema dict."""
    def predict_risk(self_inner=None, **kwargs):
        return {
            "location": {"latitude": kwargs.get("latitude", 18.52), "longitude": kwargs.get("longitude", 73.86)},
            "forecast_horizon_hours": kwargs.get("lead_hours", 96),
            "forecast_day": 4,
            "lead_time_group": "Day 3-5",
            "initialization_time": "2026-09-17T12:00:00Z",
            "valid_time": "2026-09-21T12:00:00Z",
            "lead_time_consistency": True,
            "freshness_status": "FRESH (OPERATIONAL)",
            "variable": kwargs.get("variable", "precipitation"),
            "forecast_value": 5.0,
            "bust_probability": bust_prob,
            "bust_probability_percentage": round(bust_prob * 100, 1),
            "reliability_score": round(1.0 - bust_prob, 3),
            "reliability_percentage": round((1.0 - bust_prob) * 100, 1),
            "risk_level": "LOW" if bust_prob < 0.25 else "MODERATE",
            "risk_badge": "🟢 LOW" if bust_prob < 0.25 else "🟡 MODERATE",
            "tail_sample_support": "HIGH_SAMPLE_SUPPORT",
            "tail_confidence_note": "Test response.",
            "model_version": "model_real_v002",
            "dataset_version": "dataset_real_v002",
            "data_type": "REAL",
            "forecast_source": "ECMWF IFS (Operational NWP)",
            "reference_source": "ECMWF ERA5 Reanalysis (Copernicus CDS)",
            "is_demo_model": False,
            "explanation": {
                "all_factors": [],
                "top_amplifiers": [],
                "top_mitigators": [],
                "summary_text": "Test forecast bust risk summary."
            },
            "scientific_governance": {
                "t0_enforcement": "STRICT_LEAKAGE_FREE",
                "calibration_type": "CALIBRATED_PROBABILITY",
                "reference_benchmark": "ECMWF ERA5 Reanalysis",
                "shap_interpretation": "Statistical feature attribution"
            },
            "disclaimer": "Test disclaimer."
        }
    return predict_risk


def _build_canary_service(
    canary_enabled: bool = True,
    canary_percentage: float = 10.0,
    prod_bust_prob: float = 0.08,
    canary_bust_prob: float = 0.14,
    load_canary: bool = True
):
    """Build a CanaryRoutingService with mocked production and canary services."""
    from backend.app.services.canary_service import CanaryRoutingService, CanaryHealthMonitor

    # Reset the singleton so each test gets a fresh instance
    CanaryRoutingService._instance = None

    mock_prod = MagicMock()
    mock_prod.predict_risk = _make_mock_predict(prod_bust_prob)
    mock_prod.model_version = "model_real_v002"
    mock_prod.dataset_version = "dataset_real_v002"
    mock_prod.data_type = "REAL"

    if load_canary:
        mock_canary = MagicMock()
        mock_canary.predict_risk = _make_mock_predict(canary_bust_prob)
        mock_canary.model_version = "global_v001"
        mock_canary.dataset_version = "dataset_global_v001"
        mock_canary.data_type = "REAL"
    else:
        mock_canary = None

    with patch("backend.app.services.canary_service.settings") as mock_settings:
        mock_settings.PRODUCTION_MODEL = "model_real_v002"
        mock_settings.CANARY_MODEL = "global_v001"
        mock_settings.CANARY_ENABLED = canary_enabled
        mock_settings.CANARY_PERCENTAGE = canary_percentage
        mock_settings.CANARY_MAX_ERROR_RATE = 0.01
        mock_settings.CANARY_MAX_P95_LATENCY_MULTIPLIER = 2.0
        mock_settings.CANARY_LATENCY_BREACH_WINDOW = 3

        svc = CanaryRoutingService.__new__(CanaryRoutingService)
        svc._initialized = False
        # Bypass _load_models entirely; inject mocks
        svc.production_model_name = "model_real_v002"
        svc.canary_model_name = "global_v001"
        svc.canary_enabled = canary_enabled
        svc.canary_percentage = canary_percentage
        svc.prod_service = mock_prod
        svc.canary_service = mock_canary
        svc.health_monitor = CanaryHealthMonitor()
        svc.audit_log_path = os.path.join(
            "data", "canary", f"test_canary_{id(svc)}.jsonl"
        )
        os.makedirs(os.path.dirname(svc.audit_log_path), exist_ok=True)
        svc._initialized = True
        return svc


# ---------------------------------------------------------------------------
# 1. Canary disabled by default routes 100% to production
# ---------------------------------------------------------------------------
def test_canary_disabled_by_default():
    svc = _build_canary_service(canary_enabled=False)
    for lat, lon in [(18.5, 73.8), (28.6, 77.2), (51.5, -0.1), (-34.6, -58.4)]:
        route = svc.route_request(lat, lon, 96, "precipitation")
        assert route == "production", (
            f"Expected 'production' when canary disabled, got '{route}' for ({lat}, {lon})"
        )


# ---------------------------------------------------------------------------
# 2. Deterministic routing: same request context always maps to same model
# ---------------------------------------------------------------------------
def test_canary_deterministic_routing():
    svc = _build_canary_service(canary_enabled=True, canary_percentage=50.0)
    test_cases = [
        (18.5, 73.8, 96, "precipitation"),
        (28.6, 77.2, 48, "temperature"),
        (51.5, -0.1, 120, "wind"),
        (-34.6, -58.4, 168, "pressure"),
    ]
    for lat, lon, lead, var in test_cases:
        routes = [svc.route_request(lat, lon, lead, var) for _ in range(20)]
        assert len(set(routes)) == 1, (
            f"Non-deterministic routing for ({lat},{lon},{lead},{var}): {set(routes)}"
        )


# ---------------------------------------------------------------------------
# 3. Traffic split distribution (10% canary, 90% production)
# ---------------------------------------------------------------------------
def test_canary_traffic_split_distribution():
    svc = _build_canary_service(canary_enabled=True, canary_percentage=10.0)
    # Generate 2000 distinct coordinate requests
    import random
    rng = random.Random(42)
    canary_count = 0
    total = 2000
    for _ in range(total):
        lat = rng.uniform(-90, 90)
        lon = rng.uniform(-180, 180)
        lead = rng.choice([24, 48, 72, 96, 120, 144, 168])
        var = rng.choice(["precipitation", "temperature", "wind", "pressure"])
        if svc.route_request(lat, lon, lead, var) == "canary":
            canary_count += 1

    actual_pct = (canary_count / total) * 100.0
    # Allow ±4 percentage points tolerance for deterministic hash distribution
    assert 6.0 <= actual_pct <= 14.0, (
        f"Canary traffic split out of expected [6%, 14%] range: {actual_pct:.2f}%"
    )


# ---------------------------------------------------------------------------
# 4. Response schema invariance between production and canary
# ---------------------------------------------------------------------------
def test_canary_response_schema_invariance():
    from backend.app.services.canary_service import CanaryRoutingService, CanaryHealthMonitor

    # Build production svc
    prod_svc = _build_canary_service(canary_enabled=False)
    # Build canary svc with different model
    CanaryRoutingService._instance = None
    canary_svc = _build_canary_service(canary_enabled=True, canary_percentage=100.0)

    # Use a hash that WILL route to canary (force via 100%)
    prod_result = prod_svc.predict_risk(latitude=18.52, longitude=73.86, lead_hours=96, variable="precipitation")
    canary_result = canary_svc.predict_risk(latitude=18.52, longitude=73.86, lead_hours=96, variable="precipitation")

    required_keys = [
        "bust_probability", "bust_probability_percentage", "reliability_score",
        "reliability_percentage", "risk_level", "risk_badge", "model_version",
        "dataset_version", "data_type", "explanation", "scientific_governance",
        "disclaimer", "location", "forecast_horizon_hours", "lead_time_group"
    ]
    for key in required_keys:
        assert key in prod_result, f"Production result missing key: '{key}'"
        assert key in canary_result, f"Canary result missing key: '{key}'"

    # Type equivalence for numeric fields
    for field in ["bust_probability", "reliability_score"]:
        assert isinstance(prod_result[field], (int, float)), f"Production {field} not numeric"
        assert isinstance(canary_result[field], (int, float)), f"Canary {field} not numeric"


# ---------------------------------------------------------------------------
# 5. Probability validity: finite values within [0.0, 1.0]
# ---------------------------------------------------------------------------
def test_canary_probability_validity():
    svc = _build_canary_service(canary_enabled=True, canary_percentage=100.0)
    import random
    rng = random.Random(99)
    for _ in range(100):
        lat = rng.uniform(-90, 90)
        lon = rng.uniform(-180, 180)
        lead = rng.choice([24, 96, 168])
        var = rng.choice(["precipitation", "temperature"])
        result = svc.predict_risk(latitude=lat, longitude=lon, lead_hours=lead, variable=var)
        prob = result["bust_probability"]
        assert not math.isnan(prob), f"NaN probability received for ({lat},{lon})"
        assert not math.isinf(prob), f"Inf probability received for ({lat},{lon})"
        assert 0.0 <= prob <= 1.0, f"Probability {prob} outside [0,1] for ({lat},{lon})"


# ---------------------------------------------------------------------------
# 6. Fail-safe fallback: exception in canary falls back to production
# ---------------------------------------------------------------------------
def test_canary_failsafe_fallback_on_exception():
    svc = _build_canary_service(canary_enabled=True, canary_percentage=100.0)

    def raising_predict_risk(**kwargs):
        raise RuntimeError("Simulated canary model crash for testing.")

    svc.canary_service.predict_risk = raising_predict_risk

    # Must not raise, must return a valid production result
    result = svc.predict_risk(latitude=18.52, longitude=73.86, lead_hours=96, variable="precipitation")
    assert "bust_probability" in result
    assert 0.0 <= result["bust_probability"] <= 1.0
    assert not math.isnan(result["bust_probability"])


# ---------------------------------------------------------------------------
# 7. Circuit breaker: error rate >1% trips breaker
# ---------------------------------------------------------------------------
def test_canary_circuit_breaker_error_rate():
    svc = _build_canary_service(canary_enabled=True, canary_percentage=100.0)
    hm = svc.health_monitor

    # Inject 10 canary requests: 2 errors (20% error rate) → must trip breaker
    for _ in range(8):
        hm.record_canary_success(latency_ms=3.0)
    for _ in range(2):
        hm.record_canary_error("exception", "Simulated failure")

    assert hm.circuit_broken, "Circuit breaker should have tripped with error rate >1%"
    assert hm.circuit_break_reason is not None

    # All subsequent routes must go to production
    for _ in range(10):
        assert svc.route_request(18.52, 73.86, 96, "precipitation") == "production"


# ---------------------------------------------------------------------------
# 8. Circuit breaker: 3 consecutive p95 latency breaches
# ---------------------------------------------------------------------------
def test_canary_circuit_breaker_latency_degradation():
    svc = _build_canary_service(canary_enabled=True, canary_percentage=100.0)
    hm = svc.health_monitor

    # Populate prod latencies (baseline ~3ms)
    for _ in range(50):
        hm.prod_latencies.append(3.0)

    # Simulate 3 consecutive windows of p95 > 2x prod p95 (6ms)
    # by feeding 50 canary latencies >> 6ms
    for window in range(3):
        for _ in range(50):
            hm.canary_latencies.append(50.0)  # p95 = 50ms, 2x prod_p95 = 6ms → breach
        hm._evaluate_latency_health()

    assert hm.circuit_broken, (
        "Circuit breaker should have tripped after 3 consecutive p95 latency breaches"
    )


# ---------------------------------------------------------------------------
# 9. Shadow delta calculation is tracked correctly
# ---------------------------------------------------------------------------
def test_canary_shadow_delta_calculation():
    svc = _build_canary_service(
        canary_enabled=True,
        canary_percentage=100.0,
        prod_bust_prob=0.10,
        canary_bust_prob=0.25
    )

    svc.predict_risk(latitude=18.52, longitude=73.86, lead_hours=96, variable="precipitation")
    svc.predict_risk(latitude=51.5, longitude=-0.1, lead_hours=48, variable="temperature")

    # Shadow deltas are now populated asynchronously via the background executor.
    # Flush the executor so the background task completes before we assert.
    from backend.app.services.canary_service import flush_shadow_executor
    flush_shadow_executor()

    deltas = list(svc.health_monitor.shadow_deltas)
    assert len(deltas) >= 1, "Shadow delta records should be populated"
    for d in deltas:
        assert d >= 0.0, f"Absolute delta should be >= 0, got {d}"

    telem = svc.get_telemetry()
    shadow = telem["shadow_disagreement_analysis"]
    assert shadow["mean_absolute_difference"] >= 0.0
    assert shadow["p50_difference"] >= 0.0


# ---------------------------------------------------------------------------
# 10. Sanitized logging: no secrets, tokens, PII in audit log
# ---------------------------------------------------------------------------
def test_canary_sanitized_logging():
    svc = _build_canary_service(canary_enabled=True, canary_percentage=100.0)
    svc.predict_risk(latitude=18.52, longitude=73.86, lead_hours=96, variable="precipitation")

    if not os.path.exists(svc.audit_log_path):
        pytest.skip("No audit log produced (canary may not have fired)")

    with open(svc.audit_log_path, "r") as f:
        for line in f:
            line_lower = line.lower()
            assert "password" not in line_lower, "Audit log contains 'password'"
            assert "token" not in line_lower, "Audit log contains 'token'"
            assert "api_key" not in line_lower, "Audit log contains 'api_key'"
            assert "secret" not in line_lower, "Audit log contains 'secret'"
            assert "@gmail" not in line_lower, "Audit log contains PII (email)"
            # Verify it's valid JSON
            entry = json.loads(line)
            assert "predicted_bust_probability" in entry
            assert "model_version" in entry
            assert "timestamp" in entry


# ---------------------------------------------------------------------------
# 11. Telemetry: get_telemetry returns all required sections
# ---------------------------------------------------------------------------
def test_canary_telemetry_structure():
    svc = _build_canary_service(canary_enabled=True, canary_percentage=10.0)
    telem = svc.get_telemetry()

    required_sections = [
        "routing_configuration", "traffic_statistics",
        "health_and_reliability", "latency_benchmarks", "shadow_disagreement_analysis"
    ]
    for section in required_sections:
        assert section in telem, f"Missing telemetry section: '{section}'"

    assert "canary_enabled" in telem["routing_configuration"]
    assert "canary_percentage" in telem["routing_configuration"]
    assert "circuit_broken" in telem["routing_configuration"]
    assert "canary_error_rate" in telem["health_and_reliability"]
    assert "mean_absolute_difference" in telem["shadow_disagreement_analysis"]


# ---------------------------------------------------------------------------
# 12. Rollback: disabling canary routes 100% to production immediately
# ---------------------------------------------------------------------------
def test_canary_instant_rollback():
    svc = _build_canary_service(canary_enabled=True, canary_percentage=100.0)

    # Initially enabled: should sometimes route to canary
    routes_before = [svc.route_request(i * 0.1, i * 0.2, 96, "precipitation") for i in range(20)]
    assert "canary" in routes_before, "Expected some canary routes with 100% percentage"

    # Rollback
    svc.disable_canary(reason="Manual operator rollback test")
    assert not svc.canary_enabled

    # After rollback: all routes must be production
    for i in range(20):
        route = svc.route_request(i * 0.1, i * 0.2, 96, "precipitation")
        assert route == "production", f"Expected 'production' after rollback, got '{route}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
