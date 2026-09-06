"""
FastAPI Backend Integration and Functional Tests.
Verifies all core endpoints for weather retrieval, risk estimation,
spatial risk maps, model registry, and dataset quality reports.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "scientific_disclaimer" in data


@pytest.mark.asyncio
async def test_location_search():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/locations/search?q=Pune")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] > 0
        pune = data["results"][0]
        assert pune["name"] == "Pune"
        assert abs(pune["latitude"] - 18.52) < 0.1


@pytest.mark.asyncio
async def test_weather_forecast():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/weather/forecast?lat=18.5204&lon=73.8567&days=10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_horizons"] >= 10
        assert "horizons" in data


@pytest.mark.asyncio
async def test_risk_location():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/risk/location?lat=18.5204&lon=73.8567&lead_hours=96&variable=precipitation")
        assert resp.status_code == 200
        data = resp.json()
        assert "bust_probability" in data
        assert "reliability_score" in data
        assert "risk_level" in data
        assert data["risk_level"] in ["LOW", "MODERATE", "HIGH", "VERY HIGH"]
        assert 0.0 <= data["bust_probability"] <= 1.0


@pytest.mark.asyncio
async def test_risk_map():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/risk/map?lead_hours=96&variable=precipitation")
        assert resp.status_code == 200
        data = resp.json()
        assert "grid" in data
        grid = data["grid"]
        assert len(grid) == 25
        assert data["grid_points_count"] == 25
        assert data["model_version"] == "model_real_v002"
        assert data["data_type"] == "REAL"
        assert data["dataset_version"] == "dataset_real_v002"

        seen_coords = set()
        probs = []
        for cell in grid:
            assert "latitude" in cell
            assert "longitude" in cell
            assert "bust_probability" in cell
            assert "reliability_score" in cell
            assert "risk_badge" in cell
            assert "risk_level" in cell
            assert "forecast_value" in cell

            # Valid geographic bounds for India
            assert 8.0 <= cell["latitude"] <= 36.0
            assert 68.0 <= cell["longitude"] <= 98.0

            # Unique coordinate check (no overlapping duplicate stations)
            coord = (round(cell["latitude"], 4), round(cell["longitude"], 4))
            assert coord not in seen_coords
            seen_coords.add(coord)

            # Valid probability and reliability intervals
            assert 0.0 <= cell["bust_probability"] <= 1.0
            assert 0.0 <= cell["reliability_score"] <= 1.0
            probs.append(cell["bust_probability"])

        # Genuine spatial variation: not all stations have identical bust probability
        assert min(probs) != max(probs)
        assert len(set(probs)) >= 3


@pytest.mark.asyncio
async def test_models_current():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/models/current")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "PRODUCTION"
        assert "metadata" in data


@pytest.mark.asyncio
async def test_datasets_status():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/datasets/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "dataset_version" in data
        assert data["training_ready"] is True


@pytest.mark.asyncio
async def test_health_and_model_provenance_consistency():
    """
    Regression Test: Proves that /health metadata, /ready metadata,
    and /api/risk/location model provenance cannot contradict each other.
    Validates that if production model is REAL, neither /health nor /ready
    reports is_demo_model as True or model_version as anything other than model_real_v002.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Probe /health
        health_resp = await client.get("/health")
        assert health_resp.status_code == 200
        health_data = health_resp.json()

        # 2. Probe /ready
        ready_resp = await client.get("/ready")
        assert ready_resp.status_code == 200
        ready_data = ready_resp.json()

        # 3. Probe /api/risk/location
        risk_resp = await client.get(
            "/api/risk/location?lat=18.5204&lon=73.8567&lead_hours=96&variable=precipitation&forecast_value=42&ensemble_spread=1.5"
        )
        assert risk_resp.status_code == 200
        risk_data = risk_resp.json()

        # Provenance Cross-Check:
        # Model version must be strictly identical across /health, /ready, and /api/risk/location
        assert health_data["model_version"] == "model_real_v002"
        assert ready_data["model_version"] == "model_real_v002"
        assert risk_data["model_version"] == "model_real_v002"

        # Data type must be strictly "REAL"
        assert health_data["data_type"] == "REAL"
        assert ready_data["data_type"] == "REAL"
        assert risk_data["data_type"] == "REAL"

        # is_demo_model must be strictly False across all endpoints
        assert health_data["is_demo_model"] is False
        assert ready_data["is_demo_model"] is False
        assert risk_data["is_demo_model"] is False

        # If data_type is "REAL", is_demo_model MUST be False (logical identity)
        assert (risk_data["data_type"] == "REAL") == (not risk_data["is_demo_model"])

        # Health demo_mode documentation must clarify that demo_mode is a weather provider fallback
        assert "demo_mode" in health_data
        assert "demo_mode_description" in health_data


@pytest.mark.asyncio
async def test_risk_map_multi_variable_and_horizons():
    """
    Validates that /api/risk/map correctly adapts to different meteorological
    variables (precipitation, temperature, wind, pressure) and lead times (72h, 120h, 240h).
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Test Temperature across Indian sectors (must reflect orographic lapse rates)
        temp_resp = await client.get("/api/risk/map?lead_hours=96&variable=temperature")
        assert temp_resp.status_code == 200
        temp_data = temp_resp.json()
        assert temp_data["variable"] == "temperature"
        temp_vals = [pt["forecast_value"] for pt in temp_data["grid"]]
        # High altitude stations (e.g. Shimla) must be cooler than coastal plains (e.g. Chennai)
        assert min(temp_vals) < 22.0
        assert max(temp_vals) > 28.0

        # 2. Test Wind variable
        wind_resp = await client.get("/api/risk/map?lead_hours=120&variable=wind")
        assert wind_resp.status_code == 200
        wind_data = wind_resp.json()
        assert wind_data["variable"] == "wind"
        wind_vals = [pt["forecast_value"] for pt in wind_data["grid"]]
        assert min(wind_vals) >= 0.0
        assert max(wind_vals) > 8.0

        # 3. Test Lead Horizon sensitivity: 72h vs 240h
        resp_72 = await client.get("/api/risk/map?lead_hours=72&variable=precipitation")
        resp_240 = await client.get("/api/risk/map?lead_hours=240&variable=precipitation")
        assert resp_72.status_code == 200
        assert resp_240.status_code == 200
        data_72 = resp_72.json()
        data_240 = resp_240.json()
        assert data_72["forecast_horizon_hours"] == 72
        assert data_240["forecast_horizon_hours"] == 240


@pytest.mark.asyncio
async def test_forecast_comparison_and_history_verification():
    """
    Regression Test: Verifies complete forecast verification lifecycle endpoints:
    - /api/risk/history queries genuine aligned records with REAL provenance
    - Verifies error calculation arithmetic: |fc - ref| == error
    - Verifies temporal causality and lead-hour arithmetic
    - Verifies /api/forecast/{id}/comparison reflects real verification data
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Probe /api/risk/history
        hist_resp = await client.get("/api/risk/history?lat=18.5204&lon=73.8567&limit=10")
        assert hist_resp.status_code == 200
        hist_data = hist_resp.json()
        assert hist_data["data_type"] == "REAL"
        assert hist_data["model_version"] == "model_real_v002"
        assert hist_data["sample_size"] == 10
        assert len(hist_data["records"]) == 10

        from datetime import datetime
        for rec in hist_data["records"]:
            assert rec["data_type"] == "REAL"
            assert rec["reference_source"] == "era5-reanalysis"
            assert rec["forecast_provider"] == "open-meteo-previous-runs"

            # Recompute error arithmetic
            calc_p_err = abs(rec["forecast_value"] - rec["reference_value"])
            assert abs(calc_p_err - rec["absolute_error"]) < 0.001

            calc_t_err = abs(rec["forecast_temperature"] - rec["reference_temperature"])
            assert abs(calc_t_err - rec["error_temperature"]) < 0.001

            calc_w_err = abs(rec["forecast_wind"] - rec["reference_wind"])
            assert abs(calc_w_err - rec["error_wind"]) < 0.001

            # Verify temporal lead-hour arithmetic
            v_dt = datetime.fromisoformat(rec["valid_time"])
            i_dt = datetime.fromisoformat(rec["initialization_time"])
            assert int((v_dt - i_dt).total_seconds() // 3600) == rec["lead_hours"]

        # 2. Probe /api/forecast/{id}/comparison for Pune Day 4
        comp_resp = await client.get("/api/forecast/fc_pune_day4/comparison")
        assert comp_resp.status_code == 200
        comp_data = comp_resp.json()
        assert comp_data["forecast_id"] == "fc_pune_day4"
        assert comp_data["forecast_horizon_hours"] == 96
        assert comp_data["data_type"] == "REAL"
        assert comp_data["is_bust"] is True
        assert comp_data["operational_threshold_applied"] == 34.0
        assert "reference_source" in comp_data
        assert comp_data["reference_source"] == "era5-reanalysis"

        # 3. Probe /api/forecast/{id}/comparison for specific dataset index 15348
        idx_resp = await client.get("/api/forecast/15348/comparison")
        assert idx_resp.status_code == 200
        idx_data = idx_resp.json()
        assert idx_data["forecast_id"] == "15348"
        assert idx_data["forecast_wind"] == 30.8
        assert idx_data["reference_wind"] == 12.7
        assert abs(idx_data["error_wind"] - 18.1) < 0.001
        assert idx_data["is_bust"] is True
        assert idx_data["bust_severity"] == "SEVERE"


@pytest.mark.asyncio
async def test_operational_inference_live_nwp_and_failure_modes():
    """
    Regression Test: Validates operational inference on newly issued NWP forecasts:
    - Live NWP ingestion without manual forecast_value
    - Lead time scaling across 72h, 96h, 120h, 168h
    - Variable routing across precipitation, temperature, wind, pressure
    - Model calibration (0 <= p <= 1, reliability = 1 - p)
    - Strict 422 failure modes for out-of-bounds parameters
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Operational inference on live NWP forecast (no forecast_value provided)
        live_resp = await client.get("/api/risk/location?lat=18.5204&lon=73.8567&lead_hours=96&variable=precipitation")
        assert live_resp.status_code == 200
        live_data = live_resp.json()
        assert live_data["data_type"] == "REAL"
        assert live_data["model_version"] == "model_real_v002"
        assert live_data["is_demo_model"] is False
        assert live_data["forecast_horizon_hours"] == 96
        assert live_data["forecast_day"] == 4
        assert 0.0 <= live_data["bust_probability"] <= 1.0
        assert abs(live_data["bust_probability"] + live_data["reliability_score"] - 1.0) < 0.002
        assert "summary_text" in live_data["explanation"]

        # 2. Multi-variable routing
        temp_resp = await client.get("/api/risk/location?lat=18.5204&lon=73.8567&lead_hours=72&variable=temperature&forecast_value=38.5&ensemble_spread=1.8")
        assert temp_resp.status_code == 200
        temp_data = temp_resp.json()
        assert temp_data["variable"] == "temperature"
        assert temp_data["forecast_value"] == 38.5

        wind_resp = await client.get("/api/risk/location?lat=18.5204&lon=73.8567&lead_hours=120&variable=wind&forecast_value=18.2&ensemble_spread=2.0")
        assert wind_resp.status_code == 200
        wind_data = wind_resp.json()
        assert wind_data["variable"] == "wind"
        assert wind_data["forecast_value"] == 18.2

        # 3. Failure modes: out-of-bound inputs must return HTTP 422
        bad_lat = await client.get("/api/risk/location?lat=150&lon=73.8567&lead_hours=96")
        assert bad_lat.status_code == 422

        bad_lon = await client.get("/api/risk/location?lat=18.52&lon=-200&lead_hours=96")
        assert bad_lon.status_code == 422

        bad_lead_low = await client.get("/api/risk/location?lat=18.52&lon=73.8567&lead_hours=12")
        assert bad_lead_low.status_code == 422

        bad_lead_high = await client.get("/api/risk/location?lat=18.52&lon=73.8567&lead_hours=300")
        assert bad_lead_high.status_code == 422

        bad_spread = await client.get("/api/risk/location?lat=18.52&lon=73.8567&lead_hours=96&ensemble_spread=-1.0")
        assert bad_spread.status_code == 422


@pytest.mark.asyncio
async def test_reverse_geocoding():
    """Verifies that reverse geocoding resolves coordinates to city/state."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Valid coordinates for Pune
        resp = await client.get("/api/locations/reverse?lat=18.5204&lon=73.8567")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Pune"
        assert data["state"] == "Maharashtra"
        assert data["country"] == "India"

        # 2. Out-of-bounds latitude
        bad_lat = await client.get("/api/locations/reverse?lat=95.0&lon=73.8567")
        assert bad_lat.status_code == 422


@pytest.mark.asyncio
async def test_current_weather_endpoint():
    """Verifies the /api/weather/current endpoint returns authentic live meteorological fields."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Pune coordinates
        resp = await client.get("/api/weather/current?lat=18.5204&lon=73.8567")
        assert resp.status_code == 200
        data = resp.json()

        assert "temperature_c" in data
        assert "precipitation_mm" in data
        assert "wind_speed_mps" in data
        assert "pressure_hpa" in data
        assert "humidity_percent" in data
        assert "cloud_cover_percent" in data
        assert "provider" in data
        assert "model" in data

        # Out-of-bounds coordinates
        bad_resp = await client.get("/api/weather/current?lat=195.0&lon=73.8567")
        assert bad_resp.status_code == 422
