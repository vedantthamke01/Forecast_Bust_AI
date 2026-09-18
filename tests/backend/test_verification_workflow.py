"""
Tests for Operational Forecast Verification Workflow.
Verifies temporal separation: T0 prediction logging vs post-valid-time realization audit.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.services.verification_service import VerificationService


def test_verification_service_workflow(tmp_path):
    """Verify local verification lifecycle from T0 prediction to ground-truth realization."""
    log_file = str(tmp_path / "test_verification.json")
    service = VerificationService(storage_path=log_file)

    # 1. Log T0 Prediction
    pred = service.record_t0_prediction(
        prediction_id="pred_test_001",
        initialization_time="2026-03-01T00:00:00Z",
        valid_time="2026-03-05T00:00:00Z",
        latitude=18.52,
        longitude=73.86,
        lead_hours=96,
        variable="precipitation",
        forecast_value=45.0,
        bust_probability=0.35,
        operational_threshold=32.0,
        model_version="model_real_v002"
    )

    assert pred["status"] == "AWAITING_REALIZATION"
    assert pred["reference_value"] is None
    assert pred["realized_bust_outcome"] is None

    # 2. Verify after valid time with realized observation
    # Case A: Forecast was 45.0mm, reference realized was 10.0mm -> error = 35.0mm > 32.0mm threshold -> BUST!
    verified = service.verify_prediction("pred_test_001", reference_value=10.0)
    assert verified is not None
    assert verified["status"] == "VERIFIED"
    assert verified["absolute_error"] == 35.0
    assert verified["realized_bust_outcome"] == 1
    # Brier contribution: (0.35 - 1.0)^2 = 0.4225
    assert abs(verified["brier_contribution"] - 0.4225) < 0.001

    # 3. Log and verify second non-bust forecast
    service.record_t0_prediction(
        prediction_id="pred_test_002",
        initialization_time="2026-03-01T00:00:00Z",
        valid_time="2026-03-03T00:00:00Z",
        latitude=28.61,
        longitude=77.20,
        lead_hours=48,
        variable="temperature",
        forecast_value=30.0,
        bust_probability=0.10,
        operational_threshold=4.5,
        model_version="model_real_v002"
    )
    # Reference was 31.0°C -> error = 1.0°C <= 4.5°C threshold -> NO BUST!
    verified_2 = service.verify_prediction("pred_test_002", reference_value=31.0)
    assert verified_2["realized_bust_outcome"] == 0

    # 4. Audit summary
    summary = service.get_verification_summary()
    assert summary["total_logged_predictions"] == 2
    assert summary["verified_predictions_count"] == 2
    assert summary["observed_bust_count"] == 1
    assert summary["overall_brier_score"] >= 0.0


@pytest.mark.asyncio
async def test_verification_api_endpoints():
    """Verify FastAPI verification audit and verification endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Verification audit endpoint
        audit_resp = await client.get("/api/verification/audit")
        assert audit_resp.status_code == 200
        audit_data = audit_resp.json()
        assert "total_logged_predictions" in audit_data

        # 2. Prediction endpoint returns prediction_id
        pred_resp = await client.get("/api/risk/location?lat=51.5&lon=-0.12&lead_hours=72&forecast_value=15.0")
        assert pred_resp.status_code == 200
        pred_data = pred_resp.json()
        assert "prediction_id" in pred_data
        p_id = pred_data["prediction_id"]

        # 3. Post-valid-time verification
        verify_resp = await client.post(f"/api/verification/verify?prediction_id={p_id}&reference_value=14.2")
        assert verify_resp.status_code == 200
        verify_data = verify_resp.json()
        assert verify_data["status"] == "VERIFIED"
        assert verify_data["absolute_error"] == 0.8
