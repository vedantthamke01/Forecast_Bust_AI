"""
Automated Verification Script for global_v001 Integration & 30-Day Global Horizon
Tests the 5 required locations: Nagpur, Tokyo, London, New York, Sydney
across 6 lead hours: 24h, 72h, 168h, 240h, 360h, 720h.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_system_provenance():
    h = client.get('/health').json()
    assert h['model_version'] == 'global_v001'
    assert h['dataset_version'] == 'dataset_global_v001'
    assert h['data_type'] == 'REAL'
    assert h['is_demo_model'] is False

    m = client.get('/api/models/current').json()
    assert m['model_version'] == 'global_v001'
    assert m['provenance'] == 'REAL'

@pytest.mark.parametrize("name,lat,lon", [
    ('Nagpur', 21.1458, 79.0882),
    ('Tokyo', 35.6762, 139.6503),
    ('London', 51.5074, -0.1278),
    ('New York', 40.7128, -74.0060),
    ('Sydney', -33.8688, 151.2093),
])
@pytest.mark.parametrize("lead", [24, 72, 168, 240, 360, 720])
def test_location_horizon_inference(name, lat, lon, lead):
    resp = client.get(
        f'/api/risk/location?lat={lat}&lon={lon}&lead_hours={lead}&variable=precipitation&forecast_value=5.0&ensemble_spread=1.2'
    )
    assert resp.status_code == 200, f"Inference failed for {name} ({lat}, {lon}) at {lead}h: {resp.text}"
    data = resp.json()
    ai_risk = data['AI_BUST_RISK']

    assert 'bust_probability' in ai_risk
    assert 'reliability_score' in ai_risk
    assert 'risk_level' in ai_risk

    v_status = ai_risk.get('validation_status')
    if lead <= 168:
        assert v_status == 'SCIENTIFICALLY_VALIDATED', f"Expected validated for Day {lead//24}, got {v_status}"
    else:
        assert v_status == 'UNVALIDATED_EXTENDED_RANGE', f"Expected unvalidated for Day {lead//24}, got {v_status}"

def test_weather_forecast_30_days():
    wf = client.get('/api/weather/forecast?lat=21.1458&lon=79.0882&days=30&demo=true')
    assert wf.status_code == 200
    data = wf.json()
    assert data['forecast_days'] == 30
    assert len(data['horizons']) == 30

def test_spatial_risk_map_both_domains():
    # Regional India
    rm_in = client.get('/api/risk/map?lead_hours=240&region=india')
    assert rm_in.status_code == 200
    assert len(rm_in.json()['stations']) >= 20

    # Global Benchmark Network
    rm_gl = client.get('/api/risk/map?lead_hours=720&region=global')
    assert rm_gl.status_code == 200
    assert len(rm_gl.json()['stations']) >= 50
