"""
Adversarial Robustness and Failure-Injection Test Suite.
Verifies system resilience against input fuzzing, physical boundary violations,
future data leakage, non-existent record lookups, variable cross-contamination,
and ensures strict probability-reliability mathematical consistency.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from ml_pipeline.features import check_data_leakage, FORBIDDEN_LEAKAGE_SUBSTRINGS


@pytest.mark.asyncio
async def test_nan_inf_rejection_http_422():
    """Verify that NaN and Infinity are strictly rejected with HTTP 422 without server crashes."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        bad_params = [
            {"lat": "nan", "lon": 73.85, "lead_hours": 96},
            {"lat": "inf", "lon": 73.85, "lead_hours": 96},
            {"lat": 18.52, "lon": "nan", "lead_hours": 96},
            {"lat": 18.52, "lon": "inf", "lead_hours": 96},
            {"lat": 18.52, "lon": 73.85, "lead_hours": 96, "forecast_value": "nan"},
            {"lat": 18.52, "lon": 73.85, "lead_hours": 96, "forecast_value": "inf"},
            {"lat": 18.52, "lon": 73.85, "lead_hours": 96, "ensemble_spread": "nan"},
            {"lat": 18.52, "lon": 73.85, "lead_hours": 96, "ensemble_spread": "inf"},
        ]
        for p in bad_params:
            resp = await client.get("/api/risk/location", params=p)
            assert resp.status_code == 422, f"Failed on params {p}: got HTTP {resp.status_code}"
            data = resp.json()
            assert "detail" in data


@pytest.mark.asyncio
async def test_physical_plausibility_bounds():
    """Verify physically impossible values and invalid variables are rejected with HTTP 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        cases = [
            # Negative precipitation
            {"lat": 18.52, "lon": 73.85, "lead_hours": 96, "variable": "precipitation", "forecast_value": -5.0},
            # Physically impossible precipitation (> 2000 mm)
            {"lat": 18.52, "lon": 73.85, "lead_hours": 96, "variable": "precipitation", "forecast_value": 2500.0},
            # Impossible temperature (< -100°C)
            {"lat": 18.52, "lon": 73.85, "lead_hours": 96, "variable": "temperature", "forecast_value": -150.0},
            # Impossible temperature (> 75°C)
            {"lat": 18.52, "lon": 73.85, "lead_hours": 96, "variable": "temperature", "forecast_value": 85.0},
            # Negative wind speed
            {"lat": 18.52, "lon": 73.85, "lead_hours": 96, "variable": "wind", "forecast_value": -10.0},
            # Impossible wind speed (> 150 m/s)
            {"lat": 18.52, "lon": 73.85, "lead_hours": 96, "variable": "wind", "forecast_value": 200.0},
            # Negative pressure
            {"lat": 18.52, "lon": 73.85, "lead_hours": 96, "variable": "pressure", "forecast_value": -20.0},
            # Unsupported variable
            {"lat": 18.52, "lon": 73.85, "lead_hours": 96, "variable": "tornado", "forecast_value": 10.0},
            # Negative ensemble spread
            {"lat": 18.52, "lon": 73.85, "lead_hours": 96, "ensemble_spread": -2.0},
        ]
        for c in cases:
            resp = await client.get("/api/risk/location", params=c)
            assert resp.status_code == 422, f"Failed on case {c}: got HTTP {resp.status_code}"


@pytest.mark.asyncio
async def test_valid_extreme_weather_accepted():
    """Verify rare but physically possible weather conditions are correctly accepted with HTTP 200."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        valid_extremes = [
            # Extreme cold (Ladakh winter)
            {"lat": 34.15, "lon": 77.57, "lead_hours": 96, "variable": "temperature", "forecast_value": -45.0, "ensemble_spread": 2.0},
            # Extreme heat (Phalodi / Thar desert)
            {"lat": 27.13, "lon": 72.36, "lead_hours": 96, "variable": "temperature", "forecast_value": 51.5, "ensemble_spread": 1.8},
            # Super cyclone wind
            {"lat": 19.80, "lon": 85.80, "lead_hours": 96, "variable": "wind", "forecast_value": 68.0, "ensemble_spread": 4.5},
            # Tropical cyclone eye pressure
            {"lat": 19.80, "lon": 85.80, "lead_hours": 96, "variable": "pressure", "forecast_value": 920.0, "ensemble_spread": 3.0},
            # Extreme monsoon cloudburst
            {"lat": 25.30, "lon": 91.70, "lead_hours": 96, "variable": "precipitation", "forecast_value": 450.0, "ensemble_spread": 5.0},
        ]
        for ex in valid_extremes:
            resp = await client.get("/api/risk/location", params=ex)
            assert resp.status_code == 200, f"Valid extreme weather failed on {ex}: got HTTP {resp.status_code}"
            data = resp.json()
            assert 0.0 <= data["bust_probability"] <= 1.0
            assert 0.0 <= data["reliability_score"] <= 1.0
            assert abs((data["bust_probability"] + data["reliability_score"]) - 1.0) < 1e-4


@pytest.mark.asyncio
async def test_probability_reliability_boundary_invariants():
    """Verify probability invariants across full range: Rel = 1 - Prob, risk bands correspond accurately."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for val, spread in [(0.0, 0.5), (10.0, 1.2), (35.0, 2.5), (90.0, 5.0)]:
            resp = await client.get("/api/risk/location", params={
                "lat": 18.52, "lon": 73.85, "lead_hours": 96,
                "variable": "precipitation", "forecast_value": val, "ensemble_spread": spread
            })
            assert resp.status_code == 200
            d = resp.json()
            prob = d["bust_probability"]
            rel = d["reliability_score"]
            assert 0.0 <= prob <= 1.0
            assert 0.0 <= rel <= 1.0
            assert abs((prob + rel) - 1.0) < 1e-4

            # Risk level category invariant
            if prob < 0.25:
                assert d["risk_level"] == "LOW"
            elif prob < 0.50:
                assert d["risk_level"] == "MODERATE"
            elif prob < 0.75:
                assert d["risk_level"] == "HIGH"
            else:
                assert d["risk_level"] == "VERY_HIGH"


@pytest.mark.asyncio
async def test_variable_cross_contamination_isolation():
    """Verify modifying temperature or wind does NOT cross-contaminate precipitation or other variables."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Request temperature scenario
        r_temp = await client.get("/api/risk/location", params={
            "lat": 18.52, "lon": 73.85, "lead_hours": 96,
            "variable": "temperature", "forecast_value": 38.5, "ensemble_spread": 1.5
        })
        assert r_temp.status_code == 200
        d_temp = r_temp.json()
        assert d_temp["variable"] == "temperature"
        assert d_temp["forecast_value"] == 38.5

        # Request wind scenario
        r_wind = await client.get("/api/risk/location", params={
            "lat": 18.52, "lon": 73.85, "lead_hours": 96,
            "variable": "wind", "forecast_value": 18.2, "ensemble_spread": 1.5
        })
        assert r_wind.status_code == 200
        d_wind = r_wind.json()
        assert d_wind["variable"] == "wind"
        assert d_wind["forecast_value"] == 18.2

        # Request pressure scenario
        r_press = await client.get("/api/risk/location", params={
            "lat": 18.52, "lon": 73.85, "lead_hours": 96,
            "variable": "pressure", "forecast_value": 992.0, "ensemble_spread": 1.5
        })
        assert r_press.status_code == 200
        d_press = r_press.json()
        assert d_press["variable"] == "pressure"
        assert d_press["forecast_value"] == 992.0


def test_leakage_detector_catches_all_forbidden_substrings():
    """Verify FeaturePipeline leakage gate detects all 9 forbidden substrings in all casing/affix permutations."""
    test_cases = [
        "actual_precipitation",
        "REFERENCE_TEMP",
        "observed_wind",
        "future_error",
        "ground_truth_label",
        "target_probability",
        "model_label_class",
        "future_verification_state",
        "PRE_verification_POST",
        "error_temperature",
        "OBSERVED_CLOUD",
        "Ground_Truth_Metric",
    ]
    for col in test_cases:
        leakages = check_data_leakage([col])
        assert len(leakages) > 0, f"Leakage detector failed to intercept '{col}'"

    # Verify no false positives on legitimate meteorological NWP features
    legit_cols = [
        "lead_hours", "latitude", "longitude",
        "forecast_temperature", "forecast_precipitation",
        "forecast_wind", "forecast_pressure", "forecast_humidity",
        "ensemble_spread", "run_revision"
    ]
    assert len(check_data_leakage(legit_cols)) == 0


@pytest.mark.asyncio
async def test_non_existent_forecast_comparison_returns_404():
    """Verify that querying a non-existent forecast comparison ID returns HTTP 404 without fabrication."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/forecast/NON_EXISTENT_FAKE_ID_999999/comparison")
        assert resp.status_code == 404
        data = resp.json()
        assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_spatial_risk_map_bounds_and_completeness():
    """Verify /api/risk/map across all horizons returns 25 valid, bounded, unique stations."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for lead in [72, 96, 120, 168, 192, 216, 240]:
            resp = await client.get(f"/api/risk/map?lead_hours={lead}&variable=precipitation")
            assert resp.status_code == 200
            data = resp.json()
            assert data["grid_points_count"] == 25
            stations = data.get("stations") or data.get("grid")
            assert len(stations) == 25
            names = set()
            for s in stations:
                assert -90.0 <= s["latitude"] <= 90.0
                assert -180.0 <= s["longitude"] <= 180.0
                assert 0.0 <= s["bust_probability"] <= 1.0
                assert 0.0 <= s["reliability_score"] <= 1.0
                assert abs((s["bust_probability"] + s["reliability_score"]) - 1.0) < 1e-4
                assert s["name"] not in names
                names.add(s["name"])


@pytest.mark.asyncio
async def test_system_provenance_and_model_version_integrity():
    """Verify active model version is model_real_v002, dataset is dataset_real_v002, and data_type is REAL."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # /health
        r_h = await client.get("/health")
        assert r_h.status_code == 200
        d_h = r_h.json()
        assert d_h["model_version"] == "model_real_v002"
        assert d_h["dataset_version"] == "dataset_real_v002"
        assert d_h["data_type"] == "REAL"
        assert d_h["is_demo_model"] is False

        # /api/models/current
        r_m = await client.get("/api/models/current")
        assert r_m.status_code == 200
        d_m = r_m.json()
        assert d_m["model_version"] == "model_real_v002"
        assert d_m["dataset_version"] == "dataset_real_v002"
        assert d_m["provenance"] == "REAL"

        # /api/datasets/status
        r_d = await client.get("/api/datasets/status")
        assert r_d.status_code == 200
        d_d = r_d.json()
        assert d_d["dataset_version"] == "dataset_real_v002"
        assert d_d["total_records"] == 37800
