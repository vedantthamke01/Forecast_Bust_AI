"""
Comprehensive End-to-End Judge Demonstration Technical Verification Script.
Executes the exact 12-step technical demonstration sequence specified in Section 26.
Validates HTTP status, data contracts, and absence of manual intervention.
"""
import urllib.request
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def run_demo_step(name, url, validator):
    print(f"\n[DEMO STEP] {name}")
    print(f"  URL: {url}")
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            assert resp.status == 200, f"Expected HTTP 200, got {resp.status}"
            raw = resp.read()
            data = json.loads(raw.decode('utf-8')) if "json" in resp.headers.get("Content-Type", "") or raw.startswith(b"{") else raw
            validator(data)
            print(f"  -> SUCCESS: HTTP {resp.status} - Validated.")
            return True
    except Exception as e:
        print(f"  -> FAILED: {e}")
        return False

def main():
    print("=" * 80)
    print("EXECUTING SECTION 26 FINAL TECHNICAL DEMONSTRATION WORKFLOW")
    print("=" * 80)

    steps = [
        ("Step 1: Dashboard HTML Root Loading", f"{BASE_URL}/dashboard/", 
         lambda d: assert_in(b"NCMRWF", d)),
        ("Step 2: Dashboard CSS Stylesheet", f"{BASE_URL}/dashboard/css/dashboard.css", 
         lambda d: assert_in(b":root", d)),
        ("Step 3: Dashboard JS Application Logic", f"{BASE_URL}/dashboard/js/dashboard.js", 
         lambda d: assert_in(b"loadLocationRisk", d)),
        ("Step 4: Fetch Live Operational NWP (Pune)", f"{BASE_URL}/api/weather/forecast?lat=18.5204&lon=73.8567&days=10",
         lambda d: assert_true(len(d.get("horizons", [])) >= 8)),
        ("Step 5: Pune Day 4 Live NWP Bust Prediction (T0)", f"{BASE_URL}/api/risk/location?lat=18.5204&lon=73.8567&lead_hours=96&variable=precipitation",
         lambda d: (assert_true(0.0 <= d["bust_probability"] <= 1.0),
                    assert_equal(d["risk_level"], "LOW"),
                    assert_equal(d["model_version"], "model_real_v002"),
                    assert_equal(d["data_type"], "REAL"))),
        ("Step 6: Pune Day 4 TreeSHAP Factor Explanation", f"{BASE_URL}/api/risk/location?lat=18.5204&lon=73.8567&lead_hours=96&variable=precipitation",
         lambda d: (assert_true("explanation" in d),
                    assert_true(len(d["explanation"]["all_factors"]) > 0))),
        ("Step 7: Elevated Risk What-If Scenario (Kolkata High Wind)", f"{BASE_URL}/api/risk/location?lat=22.5726&lon=88.3639&lead_hours=72&variable=wind&forecast_value=28.7&ensemble_spread=4.0",
         lambda d: (assert_equal(d["risk_level"], "MODERATE"),
                    assert_true(d["bust_probability_percentage"] > 25.0),
                    assert_equal(d["forecast_source"], "Scenario / What-if Input Override"))),
        ("Step 8: Spatial Risk Map (India 25 Synoptic Stations)", f"{BASE_URL}/api/risk/map?lead_hours=96&variable=precipitation",
         lambda d: (assert_equal(d["grid_points_count"], 25),
                    assert_equal(len(d.get("stations", [])), 25))),
        ("Step 9: Post-Event Historical Verification (Pune)", f"{BASE_URL}/api/risk/history?lat=18.5204&lon=73.8567&limit=10",
         lambda d: (assert_equal(d["data_type"], "REAL"),
                    assert_equal(d["dataset_version"], "dataset_real_v002"),
                    assert_true(len(d["records"]) > 0))),
        ("Step 10: Single Historical Record Verification (fc_pune_day4)", f"{BASE_URL}/forecast/fc_pune_day4/comparison",
         lambda d: (assert_equal(d["data_type"], "REAL"),
                    assert_equal(d["reference_source"], "era5-reanalysis"),
                    assert_equal(d["is_bust"], True))),
        ("Step 11: Day 10 Operational Live Inference (240h)", f"{BASE_URL}/api/risk/location?lat=18.5204&lon=73.8567&lead_hours=240&variable=pressure",
         lambda d: (assert_equal(d["forecast_horizon_hours"], 240),
                    assert_true(0.0 <= d["bust_probability"] <= 1.0))),
        ("Step 12: Scientific Trust & Model Governance Metadata", f"{BASE_URL}/health",
         lambda d: (assert_equal(d["model_version"], "model_real_v002"),
                    assert_equal(d["dataset_version"], "dataset_real_v002"),
                    assert_equal(d["data_type"], "REAL"),
                    assert_equal(d["is_demo_model"], False))),
    ]

    all_passed = True
    for name, url, val in steps:
        if not run_demo_step(name, url, val):
            all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("ALL 12 TECHNICAL DEMO STEPS EXECUTED AND PASSED WITHOUT INTERVENTION.")
        print("=" * 80)
        sys.exit(0)
    else:
        print("TECHNICAL DEMO FAILED ON ONE OR MORE STEPS.")
        print("=" * 80)
        sys.exit(1)

def assert_in(needle, haystack):
    assert needle in haystack, f"Expected {needle} in payload"

def assert_true(condition):
    assert condition, "Assertion failed"

def assert_equal(a, b):
    assert a == b, f"Expected {a} == {b}"

if __name__ == "__main__":
    main()
