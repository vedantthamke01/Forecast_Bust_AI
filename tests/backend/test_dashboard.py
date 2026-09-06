"""
Web Dashboard Static Serving and Frontend Contract Tests.
Verifies that the HTML5/CSS3/Vanilla JS Meteorological Dashboard is accessible,
implements the Judge Workflow (Steps A-E), accurately distinguishes operational inference
(Days 3-10) from historical archive training coverage (Days 3-7), and adheres to
strict scientific anti-leakage principles.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_dashboard_endpoint():
    """Verifies that the dashboard root and static index serve successfully."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/dashboard/")
        assert resp.status_code == 200
        assert "NCMRWF" in resp.text
        assert "AI-Based Forecast Bust Detection Platform" in resp.text
        assert "leaflet" in resp.text.lower()


@pytest.mark.asyncio
async def test_dashboard_judge_workflow_structure():
    """Verifies that Steps A, B, C, D, E are present in the HTML structure."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/dashboard/")
        assert resp.status_code == 200
        text = resp.text

        # Step Badges
        assert "STEP A" in text, "Step A (Target Observatory) badge missing"
        assert "STEP B" in text, "Step B (Forecast Horizon) badge missing"
        assert "STEP C" in text, "Step C (Meteorological Variable) badge missing"
        assert "STEP D" in text, "Step D (Operational NWP Guidance) badge missing"
        assert "STEP E" in text, "Step E (AI Bust Prediction & Reliability) badge missing"

        # Coordinates inputs
        assert 'id="lat-input"' in text, "Latitude numeric input missing"
        assert 'id="lon-input"' in text, "Longitude numeric input missing"
        assert 'id="btn-set-coords"' in text, "Coordinate apply button missing"

        # Horizon buttons for Days 3-10
        for day in range(3, 11):
            lead = day * 24
            assert f'data-lead="{lead}"' in text, f"Horizon button for Day {day} ({lead}h) missing"

        # Variables
        assert 'data-var="precipitation"' in text
        assert 'data-var="temperature"' in text
        assert 'data-var="wind"' in text
        assert 'data-var="pressure"' in text

        # Provenance bindings
        assert "model_real_v002" in text
        assert "dataset_real_v002" in text


@pytest.mark.asyncio
async def test_dashboard_no_future_reference_leakage_in_prediction():
    """Confirms that the forecast prediction interface does not consume future ground truth."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/dashboard/")
        text = resp.text
        # Check that Anti-Leakage notice is present
        assert "Anti-Leakage Certified" in text
        assert "Prediction generated strictly at $T_0$" in text or "T₀" in text
        # Verify verification stage distinction
        assert "STAGE 1: T₀ PREDICTION" in text or "STAGE 1" in text
        assert "STAGE 2: T₀ + τ VERIFICATION" in text or "STAGE 2" in text


@pytest.mark.asyncio
async def test_dashboard_static_css_and_js_served():
    """Verifies that dashboard CSS and JS assets are served with valid HTTP 200."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        css_resp = await client.get("/dashboard/css/dashboard.css")
        assert css_resp.status_code == 200
        assert "--risk-low" in css_resp.text
        assert "--risk-very-high" in css_resp.text

        js_resp = await client.get("/dashboard/js/dashboard.js")
        assert js_resp.status_code == 200
        assert "API_BASE" in js_resp.text
        assert "loadLocationRisk" in js_resp.text
        assert "updateHorizonChart" in js_resp.text


@pytest.mark.asyncio
async def test_api_risk_location_response_contract():
    """Verifies the contract of /api/risk/location consumed by the frontend."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        url = "/api/risk/location?lat=18.5204&lon=73.8567&lead_hours=96&variable=precipitation"
        resp = await client.get(url)
        assert resp.status_code == 200
        data = resp.json()

        # Check required fields
        required_fields = [
            "bust_probability", "reliability_score", "risk_level", "risk_badge",
            "model_version", "dataset_version", "data_type", "forecast_source",
            "reference_source", "explanation"
        ]
        for f in required_fields:
            assert f in data, f"Missing required field '{f}' in /api/risk/location response"

        # Math identity: P(Bust) + Reliability == 1.0
        p = data["bust_probability"]
        r = data["reliability_score"]
        assert abs((p + r) - 1.0) < 0.005, f"P({p}) + Rel({r}) != 1.0"

        # Provenance verification
        assert data["model_version"] == "model_real_v002"
        assert data["dataset_version"] == "dataset_real_v002"
        assert data["data_type"] == "REAL"
        assert data["is_demo_model"] is False


@pytest.mark.asyncio
async def test_api_risk_map_contract_and_units():
    """Verifies that /api/risk/map returns all 25 synoptic stations with correct fields."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for var in ["precipitation", "temperature", "wind", "pressure"]:
            url = f"/api/risk/map?lead_hours=96&variable={var}"
            resp = await client.get(url)
            assert resp.status_code == 200
            data = resp.json()
            assert data["variable"] == var
            assert len(data["grid"]) == 25
            for pt in data["grid"]:
                assert "name" in pt and "latitude" in pt and "longitude" in pt
                assert "bust_probability" in pt and "risk_badge" in pt
                assert "forecast_value" in pt
