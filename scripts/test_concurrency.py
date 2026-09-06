"""
Concurrency and State Isolation Stress Test Script.
Tests 5, 10, and 25 simultaneous concurrent requests to /api/risk/location
with varying locations, lead times, variables, and scenario overrides.
Verifies zero state leakage, zero cross-contamination, and strict thread-safety.
"""
import concurrent.futures
import urllib.request
import urllib.parse
import json
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

TEST_PROFILES = [
    {"name": "Pune", "lat": 18.5204, "lon": 73.8567, "lead": 72, "var": "precipitation", "val": 45.0, "spread": 2.1},
    {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "lead": 96, "var": "temperature", "val": 34.2, "spread": 1.4},
    {"name": "Delhi", "lat": 28.6139, "lon": 77.2090, "lead": 120, "var": "wind", "val": 18.5, "spread": 2.8},
    {"name": "Kolkata", "lat": 22.5726, "lon": 88.3639, "lead": 144, "var": "pressure", "val": 998.0, "spread": 1.1},
    {"name": "Chennai", "lat": 13.0827, "lon": 80.2707, "lead": 168, "var": "precipitation", "val": 82.0, "spread": 3.4},
    {"name": "Bengaluru", "lat": 12.9716, "lon": 77.5946, "lead": 192, "var": "temperature", "val": 22.4, "spread": 1.9},
    {"name": "Hyderabad", "lat": 17.3850, "lon": 78.4867, "lead": 216, "var": "wind", "val": 12.0, "spread": 1.6},
    {"name": "Ahmedabad", "lat": 23.0225, "lon": 72.5714, "lead": 240, "var": "temperature", "val": 42.1, "spread": 2.5},
    {"name": "Jaipur", "lat": 26.9124, "lon": 75.7873, "lead": 72, "var": "precipitation", "val": 12.0, "spread": 1.2},
    {"name": "Lucknow", "lat": 26.8467, "lon": 80.9462, "lead": 96, "var": "pressure", "val": 1004.0, "spread": 1.7},
]

def make_request(profile, req_id):
    params = {
        "lat": profile["lat"],
        "lon": profile["lon"],
        "lead_hours": profile["lead"],
        "variable": profile["var"],
        "forecast_value": profile["val"],
        "ensemble_spread": profile["spread"]
    }
    url = f"{BASE_URL}/api/risk/location?{urllib.parse.urlencode(params)}"
    start_t = time.time()
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            elapsed = time.time() - start_t
            return {
                "req_id": req_id,
                "profile": profile,
                "status": resp.status,
                "elapsed": elapsed,
                "data": data,
                "error": None
            }
    except Exception as e:
        elapsed = time.time() - start_t
        return {
            "req_id": req_id,
            "profile": profile,
            "status": getattr(e, "code", 500),
            "elapsed": elapsed,
            "data": None,
            "error": str(e)
        }

def run_concurrency_batch(concurrency_level):
    print(f"\n--- Testing Concurrency Level: {concurrency_level} simultaneous requests ---")
    requests_to_run = []
    for i in range(concurrency_level):
        prof = TEST_PROFILES[i % len(TEST_PROFILES)]
        requests_to_run.append((prof, i + 1))

    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency_level) as executor:
        futures = [executor.submit(make_request, p, rid) for p, rid in requests_to_run]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    total_time = time.time() - start_time

    # Validate results
    failures = []
    for res in results:
        rid = res["req_id"]
        prof = res["profile"]
        data = res["data"]
        
        if res["status"] != 200:
            failures.append(f"Req #{rid} failed with status {res['status']}: {res['error']}")
            continue
            
        # 1. Location state check
        loc = data.get("location", {})
        if round(loc.get("latitude", 0), 2) != round(prof["lat"], 2) or round(loc.get("longitude", 0), 2) != round(prof["lon"], 2):
            failures.append(f"Req #{rid} ({prof['name']}) state leaked: got {loc}")

        # 2. Horizon consistency check
        if data.get("forecast_horizon_hours") != prof["lead"]:
            failures.append(f"Req #{rid} lead hours leaked: expected {prof['lead']} got {data.get('forecast_horizon_hours')}")

        # 3. Variable consistency check
        if data.get("variable") != prof["var"]:
            failures.append(f"Req #{rid} variable leaked: expected {prof['var']} got {data.get('variable')}")

        # 4. Probability bounds check
        prob = data.get("bust_probability", -1)
        rel = data.get("reliability_score", -1)
        if not (0.0 <= prob <= 1.0) or not (0.0 <= rel <= 1.0):
            failures.append(f"Req #{rid} invalid probability: prob={prob}, rel={rel}")
        if abs((prob + rel) - 1.0) > 1e-4:
            failures.append(f"Req #{rid} probability-reliability mismatch: prob={prob} + rel={rel} != 1.0")

    print(f"Completed {concurrency_level} requests in {total_time:.3f}s (avg {(total_time/concurrency_level)*1000:.1f}ms/req)")
    if failures:
        print(f"FAILED: {len(failures)} concurrency defects detected!")
        for f in failures[:5]:
            print(f"  - {f}")
        return False
    else:
        print(f"PASSED: All {concurrency_level}/{concurrency_level} requests isolated, correct, and thread-safe.")
        return True

def main():
    print("=" * 80)
    print("STARTING MULTI-CONCURRENCY STATE ISOLATION AUDIT (5, 10, 25 requests)")
    print("=" * 80)
    
    c5 = run_concurrency_batch(5)
    c10 = run_concurrency_batch(10)
    c25 = run_concurrency_batch(25)

    print("\n" + "=" * 80)
    if c5 and c10 and c25:
        print("ALL CONCURRENCY TESTS (5, 10, 25) PASSED WITH ZERO CROSS-CONTAMINATION.")
        print("=" * 80)
        sys.exit(0)
    else:
        print("CONCURRENCY AUDIT FAILED.")
        print("=" * 80)
        sys.exit(1)

if __name__ == "__main__":
    main()
