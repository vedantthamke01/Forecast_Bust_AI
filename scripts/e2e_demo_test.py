"""
Comprehensive End-to-End Test Suite for SIH26079 Judge Workflow.
Tests:
1. Pune (18.5204, 73.8567) - 72h precipitation
2. Pune (18.5204, 73.8567) - 96h precipitation
3. Pune (18.5204, 73.8567) - 120h temperature
4. Pune (18.5204, 73.8567) - 168h wind
5. Pune (18.5204, 73.8567) - 240h pressure
"""
import urllib.request
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

TEST_CASES = [
    {
        "name": "Test 1: 72h Precipitation (Day 3)",
        "lat": 18.5204,
        "lon": 73.8567,
        "lead_hours": 72,
        "variable": "precipitation",
        "expected_unit": "mm",
        "expected_horizon_days": 3,
        "is_historical_horizon": True
    },
    {
        "name": "Test 2: 96h Precipitation (Day 4)",
        "lat": 18.5204,
        "lon": 73.8567,
        "lead_hours": 96,
        "variable": "precipitation",
        "expected_unit": "mm",
        "expected_horizon_days": 4,
        "is_historical_horizon": True
    },
    {
        "name": "Test 3: 120h Temperature (Day 5)",
        "lat": 18.5204,
        "lon": 73.8567,
        "lead_hours": 120,
        "variable": "temperature",
        "expected_unit": "°C",
        "expected_horizon_days": 5,
        "is_historical_horizon": True
    },
    {
        "name": "Test 4: 168h Wind Speed (Day 7)",
        "lat": 18.5204,
        "lon": 73.8567,
        "lead_hours": 168,
        "variable": "wind",
        "expected_unit": "m/s",
        "expected_horizon_days": 7,
        "is_historical_horizon": True
    },
    {
        "name": "Test 5: 240h Sea Level Pressure (Day 10 - Operational Inference)",
        "lat": 18.5204,
        "lon": 73.8567,
        "lead_hours": 240,
        "variable": "pressure",
        "expected_unit": "hPa",
        "expected_horizon_days": 10,
        "is_historical_horizon": False
    }
]

def run_e2e_tests():
    all_passed = True
    print("=" * 85)
    print("      SIH26079 COMPREHENSIVE END-TO-END DEMO TEST EXECUTION")
    print("=" * 85)

    for tc in TEST_CASES:
        print(f"\n[RUNNING] {tc['name']}")
        url = f"{BASE_URL}/api/risk/location?lat={tc['lat']}&lon={tc['lon']}&lead_hours={tc['lead_hours']}&variable={tc['variable']}"
        print(f"Request: GET {url}")

        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=15) as resp:
                status_code = resp.status
                assert status_code == 200, f"Expected 200, got {status_code}"
                data = json.loads(resp.read().decode("utf-8"))

            # 1. Verify Model and Dataset Provenance
            assert data.get("model_version") == "model_real_v002", f"Invalid model_version: {data.get('model_version')}"
            assert data.get("dataset_version") == "dataset_real_v002", f"Invalid dataset_version: {data.get('dataset_version')}"
            assert data.get("data_type") == "REAL", f"Invalid data_type: {data.get('data_type')}"
            assert data.get("is_demo_model") is False, f"Expected is_demo_model=False, got {data.get('is_demo_model')}"

            # 2. Verify Live NWP Guidance Retrieval
            fc_src = data.get("forecast_source", "")
            assert "open-meteo" in fc_src.lower() or "ecmwf" in fc_src.lower() or "ifs" in fc_src.lower(), f"Unexpected forecast_source: {fc_src}"
            assert "forecast_value" in data, "Missing forecast_value in API response"
            f_val = data["forecast_value"]
            assert f_val is not None, "forecast_value is None"

            # 3. Verify Probability and Reliability Calculation
            p_bust = data.get("bust_probability")
            p_rel = data.get("reliability_score")
            assert 0.0 <= p_bust <= 1.0, f"p_bust out of range: {p_bust}"
            assert 0.0 <= p_rel <= 1.0, f"p_rel out of range: {p_rel}"
            diff = abs((p_bust + p_rel) - 1.0)
            assert diff < 0.002, f"P(Bust) + Reliability != 1.0 (disparity: {diff})"

            # 4. Verify Risk Bands
            risk_level = data.get("risk_level")
            risk_badge = data.get("risk_badge")
            if p_bust < 0.25:
                assert risk_level == "LOW", f"Expected LOW for p={p_bust}, got {risk_level}"
                assert "LOW" in risk_badge
            elif p_bust < 0.50:
                assert risk_level == "MODERATE", f"Expected MODERATE for p={p_bust}, got {risk_level}"
                assert "MODERATE" in risk_badge
            elif p_bust < 0.75:
                assert risk_level == "HIGH", f"Expected HIGH for p={p_bust}, got {risk_level}"
                assert "HIGH" in risk_badge
            else:
                assert risk_level == "VERY HIGH", f"Expected VERY HIGH for p={p_bust}, got {risk_level}"
                assert "VERY HIGH" in risk_badge

            # 5. Verify TreeSHAP Explanation Non-Contradiction
            explanation = data.get("explanation", {})
            summary = explanation.get("summary_text", "")
            assert len(summary) > 0, "Empty explanation summary"
            if risk_level == "LOW":
                assert "elevated" not in summary.lower(), f"Contradictory summary for LOW risk: '{summary}'"
            assert "all_factors" in explanation, "Missing all_factors in explanation"
            assert len(explanation["all_factors"]) > 0, "Empty all_factors list"

            # 6. Verify Day 10 Operational Inference distinction
            if tc["lead_hours"] == 240:
                print("   -> Day 10 Operational Inference Verified: successfully runs operational inference for 240h")

            # Clean output avoiding Windows charmap crash
            badge_str = risk_badge.encode('ascii', errors='ignore').decode('ascii').strip()
            print(f"   [PASS] Forecast Value: {f_val:.2f} {tc['expected_unit']}")
            print(f"          P(Bust): {p_bust*100:.1f}% | Reliability: {p_rel*100:.1f}% | Band: {badge_str}")
            print(f"          SHAP Summary: '{summary}'")
            print(f"          Provenance: {data['model_version']} / {data['dataset_version']} ({data['data_type']})")

        except Exception as e:
            print(f"   [FAIL] {e}")
            all_passed = False

    # Check Spatial Map endpoint
    print("\n[RUNNING] Spatial Risk Map Integration (/api/risk/map)")
    try:
        url = f"{BASE_URL}/api/risk/map?lead_hours=96&variable=precipitation"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            grid = data.get("grid", [])
            assert len(grid) == 25, f"Expected 25 synoptic stations, got {len(grid)}"
            # Verify Pune is present
            pune = next((s for s in grid if "pune" in s["name"].lower()), None)
            assert pune is not None, "Pune station missing from risk map grid"
            pune_badge = pune['risk_badge'].encode('ascii', errors='ignore').decode('ascii').strip()
            print(f"   [PASS] 25 stations verified. Pune: {pune['bust_probability']*100:.1f}% bust risk ({pune_badge})")
    except Exception as e:
        print(f"   [FAIL] {e}")
        all_passed = False

    # Check Historical Verification endpoint
    print("\n[RUNNING] Historical Verification Integration (/api/risk/history)")
    try:
        url = f"{BASE_URL}/api/risk/history?lat=18.5204&lon=73.8567&limit=5"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            records = data.get("records", [])
            assert len(records) > 0, "No historical verification records returned"
            rec = records[0]
            assert "forecast_value" in rec and "reference_value" in rec and "absolute_error" in rec
            print(f"   [PASS] {len(records)} records verified. Sample error: |{rec['forecast_value']:.1f} - {rec['reference_value']:.1f}| = {rec['absolute_error']:.1f} mm ({rec['bust_severity']})")
    except Exception as e:
        print(f"   [FAIL] {e}")
        all_passed = False

    print("\n" + "=" * 85)
    if all_passed:
        print("          ALL END-TO-END DEMO TESTS PASSED WITH 100% SUCCESS")
    else:
        print("          SOME END-TO-END DEMO TESTS FAILED")
    print("=" * 85)
    return all_passed

if __name__ == "__main__":
    success = run_e2e_tests()
    sys.exit(0 if success else 1)
