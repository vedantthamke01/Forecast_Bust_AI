"""
API Input Fuzzing and Stress Test Script for /api/risk/location.
Tests edge cases, boundary conditions, invalid parameters, and physical plausibility.
"""
import urllib.request
import urllib.error
import json
import math

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(url):
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return resp.status, data
    except urllib.error.HTTPError as e:
        try:
            err_data = json.loads(e.read().decode('utf-8'))
            return e.code, err_data
        except Exception:
            return e.code, str(e)
    except urllib.error.URLError as e:
        return 0, f"Client network/timeout error: {e}"
    except Exception as e:
        return 0, f"Client error: {e}"

def run_fuzzing():
    print("=" * 80)
    print("STARTING API INPUT FUZZING: /api/risk/location")
    print("=" * 80)
    
    test_cases = [
        # 1. Coordinates Fuzzing
        ("Lat -90 (South Pole)", "/api/risk/location?lat=-90&lon=0&lead_hours=96", [200]),
        ("Lat +90 (North Pole)", "/api/risk/location?lat=90&lon=0&lead_hours=96", [200]),
        ("Lat 0 (Equator)", "/api/risk/location?lat=0&lon=0&lead_hours=96", [200]),
        ("Lon -180 (Date Line)", "/api/risk/location?lat=0&lon=-180&lead_hours=96", [200]),
        ("Lon +180 (Date Line)", "/api/risk/location?lat=0&lon=180&lead_hours=96", [200]),
        ("Lat -91 (Out of bounds)", "/api/risk/location?lat=-91&lon=0&lead_hours=96", [422]),
        ("Lat +91 (Out of bounds)", "/api/risk/location?lat=91&lon=0&lead_hours=96", [422]),
        ("Lon -181 (Out of bounds)", "/api/risk/location?lat=0&lon=-181&lead_hours=96", [422]),
        ("Lon +181 (Out of bounds)", "/api/risk/location?lat=0&lon=181&lead_hours=96", [422]),
        ("Lat string (Invalid)", "/api/risk/location?lat=pune&lon=0&lead_hours=96", [422]),
        ("Missing lat", "/api/risk/location?lon=73.85&lead_hours=96", [422]),
        ("Missing lon", "/api/risk/location?lat=18.52&lead_hours=96", [422]),
        ("Lat NaN", "/api/risk/location?lat=nan&lon=73.85&lead_hours=96", [422]),
        ("Lat Inf", "/api/risk/location?lat=inf&lon=73.85&lead_hours=96", [422]),

        # 2. Lead Hours Fuzzing
        ("Lead 24 (Day 1 min)", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=24", [200]),
        ("Lead 72 (Day 3)", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=72", [200]),
        ("Lead 168 (Day 7 archive limit)", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=168", [200]),
        ("Lead 192 (Day 8 op inference)", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=192", [200]),
        ("Lead 216 (Day 9 op inference)", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=216", [200]),
        ("Lead 240 (Day 10 max)", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=240", [200]),
        ("Lead 23 (Below min 24)", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=23", [422]),
        ("Lead 25 (Non-24 interval)", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=25", [200, 422]),
        ("Lead 241 (Above max 240)", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=241", [422]),
        ("Lead 300 (Too far)", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=300", [422]),
        ("Lead negative -24", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=-24", [422]),
        ("Lead decimal 96.5", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96.5", [422]),
        ("Lead string 'tomorrow'", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=tomorrow", [422]),

        # 3. Variable Fuzzing
        ("Variable precipitation", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&variable=precipitation", [200]),
        ("Variable temperature", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&variable=temperature", [200]),
        ("Variable wind", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&variable=wind", [200]),
        ("Variable pressure", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&variable=pressure", [200]),
        ("Variable UPPERCASE PRECIPITATION", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&variable=PRECIPITATION", [200]),
        ("Variable Mixed Temperature", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&variable=TeMpErAtUrE", [200]),
        ("Variable with whitespace ' wind '", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&variable=%20wind%20", [200]),
        ("Variable unsupported 'tornado'", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&variable=tornado", [200, 422]),
        ("Variable empty string", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&variable=", [200, 422]),

        # 4. Forecast Value Fuzzing
        ("Forecast 0.0 (Zero rain)", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&variable=precipitation&forecast_value=0.0", [200]),
        ("Forecast negative precip -5.0", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&variable=precipitation&forecast_value=-5.0", [200, 422]),
        ("Forecast extreme rain 250.0 mm", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&variable=precipitation&forecast_value=250.0", [200]),
        ("Forecast normal temp 28.5 C", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&variable=temperature&forecast_value=28.5", [200]),
        ("Forecast extreme cold -45.0 C (Ladakh)", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&variable=temperature&forecast_value=-45.0", [200]),
        ("Forecast extreme heat 52.0 C (Phalodi)", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&variable=temperature&forecast_value=52.0", [200]),
        ("Forecast impossible temp -200 C", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&variable=temperature&forecast_value=-200.0", [200, 422]),
        ("Forecast zero wind 0.0 m/s", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&variable=wind&forecast_value=0.0", [200]),
        ("Forecast extreme wind 65.0 m/s (Super Cyclone)", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&variable=wind&forecast_value=65.0", [200]),
        ("Forecast negative wind -10.0 m/s", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&variable=wind&forecast_value=-10.0", [200, 422]),
        ("Forecast normal pressure 1012 hPa", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&variable=pressure&forecast_value=1012.0", [200]),
        ("Forecast deep low 940 hPa", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&variable=pressure&forecast_value=940.0", [200]),
        ("Forecast negative pressure -10 hPa", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&variable=pressure&forecast_value=-10.0", [200, 422]),
        ("Forecast NaN", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&variable=precipitation&forecast_value=nan", [422]),
        ("Forecast Inf", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&variable=precipitation&forecast_value=inf", [422]),

        # 5. Ensemble Spread Fuzzing
        ("Spread 0.0", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&ensemble_spread=0.0", [200]),
        ("Spread normal 1.5", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&ensemble_spread=1.5", [200]),
        ("Spread large 8.0", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&ensemble_spread=8.0", [200]),
        ("Spread negative -1.0", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&ensemble_spread=-1.0", [422]),
        ("Spread NaN", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&ensemble_spread=nan", [422]),
        ("Spread Inf", "/api/risk/location?lat=18.52&lon=73.85&lead_hours=96&ensemble_spread=inf", [422]),
    ]

    results = []
    crashes = []
    for desc, path, allowed_statuses in test_cases:
        url = f"{BASE_URL}{path}"
        status, data = test_endpoint(url)
        passed = status in allowed_statuses
        if status >= 500:
            crashes.append((desc, url, status, data))
        results.append((desc, status, passed, data))
        mark = "[PASS]" if passed else "[FAIL]"
        print(f"{mark} {desc:45} -> HTTP {status} (Expected {allowed_statuses})")
        if not passed:
            print(f"       URL: {url}")
            print(f"       Response: {str(data)[:150]}")

    print("\n" + "=" * 80)
    print(f"SUMMARY: {sum(1 for r in results if r[2])}/{len(results)} tests passed.")
    if crashes:
        print(f"CRITICAL: {len(crashes)} server crash(es) (HTTP 500) detected!")
        for c in crashes:
            print(f"  - {c[0]}: HTTP {c[2]}")
    else:
        print("EXCELLENT: ZERO server crashes (HTTP 500) occurred under fuzzing.")
    print("=" * 80)

if __name__ == "__main__":
    run_fuzzing()
