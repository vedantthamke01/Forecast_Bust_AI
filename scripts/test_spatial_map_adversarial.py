"""
Spatial Map Adversarial and Robustness Test Script.
Tests /api/risk/map across all horizons (72, 96, 120, 168, 192, 216, 240)
and all variables (precipitation, temperature, wind, pressure).
"""
import urllib.request
import json
import sys

BASE = "http://127.0.0.1:8000"
leads = [72, 96, 120, 168, 192, 216, 240]
variables = ["precipitation", "temperature", "wind", "pressure"]

def run_tests():
    total_tests = 0
    all_passed = True
    print("Testing /api/risk/map across all 7 horizons and 4 variables (28 combinations)...")

    for l in leads:
        for v in variables:
            url = f"{BASE}/api/risk/map?lead_hours={l}&variable={v}"
            try:
                with urllib.request.urlopen(url, timeout=10) as r:
                    assert r.status == 200
                    d = json.loads(r.read())
                    stations = d.get("stations", [])
                    assert len(stations) == 25, f"Expected 25 stations, got {len(stations)}"
                    names = set()
                    probs = []
                    for s in stations:
                        assert -90 <= s["latitude"] <= 90
                        assert -180 <= s["longitude"] <= 180
                        assert 0.0 <= s["bust_probability"] <= 1.0
                        assert abs((s["bust_probability"] + s["reliability_score"]) - 1.0) < 1e-4
                        assert s["name"] not in names, f"Duplicate station {s['name']}"
                        names.add(s["name"])
                        probs.append(s["bust_probability"])
                    
                    # Verify spatial variation exists (not accidentally constant)
                    assert len(set(probs)) > 1, f"Identical probabilities across all stations for {l}h {v}"
                    total_tests += 1
            except Exception as e:
                print(f"FAILED: {l}h {v}: {e}")
                all_passed = False

    if all_passed:
        print(f"ALL {total_tests} SPATIAL MAP TESTS PASSED.")
        print("Verified: 25 stations valid, coordinates valid, no duplicate stations, probabilities bounded [0, 1], reliability = 1 - prob, spatial variation genuine.")
        sys.exit(0)
    else:
        print("SPATIAL MAP TESTS FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
