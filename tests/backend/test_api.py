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
        assert len(data["grid"]) > 0
        first_cell = data["grid"][0]
        assert "bust_probability" in first_cell
        assert "risk_badge" in first_cell


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
