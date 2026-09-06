"""
Web Dashboard Static Serving Integration Test.
Verifies that the HTML5/CSS3/Vanilla JS Meteorological Dashboard is accessible.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_dashboard_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/dashboard/")
        assert resp.status_code == 200
        assert "NCMRWF" in resp.text
        assert "AI-Based Forecast Bust Detection Platform" in resp.text
        assert "leaf-let" not in resp.text.lower() or "leaflet" in resp.text.lower()
