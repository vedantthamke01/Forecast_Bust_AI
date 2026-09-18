"""
Section 2 & 4: API Smoke Tests + Performance Benchmarks
Covers 7 locations x 3 variables x 4 lead times = 84 total predictions
Uses actual predict_risk signature and correct response schema field names.
"""
import sys, os, time, json
sys.path.insert(0, '.')
from dotenv import load_dotenv; load_dotenv(override=True)
from backend.app.services.bust_service import BustPredictionService
import numpy as np

BustPredictionService._instance = None
svc = BustPredictionService()

LOCATIONS = [
    ("Pune",      "Asia/India",         18.52,  73.86),
    ("Tokyo",     "Asia",               35.68, 139.69),
    ("London",    "Europe",             51.51,  -0.13),
    ("Cairo",     "Africa",             30.06,  31.24),
    ("New York",  "North America",      40.71, -74.01),
    ("Sao Paulo", "South America",     -23.55, -46.63),
    ("Sydney",    "Oceania",           -33.87, 151.21),
]

VARIABLES = ["precipitation", "temperature", "wind"]
LEAD_TIMES = [24, 72, 120, 168]

VARIABLE_PARAMS = {
    "precipitation": {"forecast_val": 8.5, "forecast_precip": 8.5, "forecast_temp": 27.0,
                      "forecast_wind": 12.0, "forecast_press": 1005.0, "ensemble_spread": 2.5},
    "temperature":   {"forecast_val": 34.0, "forecast_precip": 0.1, "forecast_temp": 34.0,
                      "forecast_wind": 10.0, "forecast_press": 1012.0, "ensemble_spread": 1.8},
    "wind":          {"forecast_val": 22.0, "forecast_precip": 0.5, "forecast_temp": 25.0,
                      "forecast_wind": 22.0, "forecast_press": 1008.0, "ensemble_spread": 4.0},
}

results = []
latencies = []
failures = []

print("=== SECTION 2: API SMOKE TESTS ===")
print(f"Testing {len(LOCATIONS)} locations x {len(VARIABLES)} variables x {len(LEAD_TIMES)} lead times = {len(LOCATIONS)*len(VARIABLES)*len(LEAD_TIMES)} total")
print()

for name, region, lat, lon in LOCATIONS:
    for variable in VARIABLES:
        vp = VARIABLE_PARAMS[variable]
        for lead in LEAD_TIMES:
            t0 = time.perf_counter()
            try:
                result = svc.predict_risk(
                    latitude=lat,
                    longitude=lon,
                    lead_hours=lead,
                    variable=variable,
                    forecast_val=vp["forecast_val"],
                    forecast_precip=vp["forecast_precip"],
                    forecast_temp=vp["forecast_temp"],
                    forecast_wind=vp["forecast_wind"],
                    forecast_press=vp["forecast_press"],
                    ensemble_spread=vp["ensemble_spread"],
                    run_revision=0.5,
                    include_explanation=True,
                )
                elapsed_ms = (time.perf_counter() - t0) * 1000
                latencies.append(elapsed_ms)

                bp   = result.get("bust_probability")
                rel  = result.get("reliability_score")   # correct field name
                pct  = result.get("reliability_percentage")
                mv   = result.get("model_version", "unknown")
                demo = result.get("is_demo_model")       # True for SYNTHETIC provenance — expected
                expl = result.get("explanation")
                has_shap = isinstance(expl, dict) and len(expl) > 0

                checks = {
                    "bp_present":         bp is not None,
                    "bp_in_range":        bp is not None and 0.0 <= float(bp) <= 1.0,
                    "not_nan":            bp is not None and not np.isnan(float(bp)),
                    "not_inf":            bp is not None and not np.isinf(float(bp)),
                    "rel_present":        rel is not None,
                    "rel_in_range":       rel is not None and 0.0 <= float(rel) <= 1.0,
                    "rel_consistent":     (rel is not None and bp is not None
                                          and abs(float(rel) - (1.0 - float(bp))) < 0.02),
                    "model_global_v001":  mv == "global_v001",
                    # is_demo_model=True is CORRECT for SYNTHETIC-provenance model — not an error
                    "no_live_fallback":   not result.get("fallback", False),
                    "no_app_demo_mode":   not result.get("demo_mode", False),
                    "explanation_ok":     has_shap,
                }

                all_pass = all(checks.values())
                status = "PASS" if all_pass else "FAIL"
                if not all_pass:
                    failures.append({
                        "location": name, "variable": variable, "lead": lead,
                        "checks": {k: v for k, v in checks.items() if not v},
                        "bp": bp, "rel": rel, "model_v": mv
                    })

                results.append({
                    "location": name, "region": region, "variable": variable, "lead_h": lead,
                    "status": status,
                    "bust_probability": round(float(bp), 6) if bp is not None else None,
                    "reliability_score": round(float(rel), 6) if rel is not None else None,
                    "reliability_percentage": pct,
                    "model_version": mv,
                    "is_demo_model_flag": demo,  # synthetic provenance — expected True
                    "has_explanation": has_shap,
                    "latency_ms": round(elapsed_ms, 2),
                })
                bp_s = f"{float(bp):.4f}" if bp is not None else "None"
                rel_s = f"{float(rel):.4f}" if rel is not None else "None"
                print(f"  [{status}] {name:12s} | {variable:15s} | {lead:3d}h | "
                      f"bp={bp_s} rel={rel_s} | {elapsed_ms:.1f}ms | shap={has_shap} | {mv}")

            except Exception as e:
                elapsed_ms = (time.perf_counter() - t0) * 1000
                failures.append({"location": name, "variable": variable, "lead": lead, "error": str(e)})
                results.append({
                    "location": name, "region": region, "variable": variable, "lead_h": lead,
                    "status": "ERROR", "error": str(e), "latency_ms": round(elapsed_ms, 2)
                })
                print(f"  [ERROR] {name:12s} | {variable:15s} | {lead:3d}h | {str(e)[:90]}")

# Deterministic repeat test
print()
print("=== DETERMINISTIC REPEAT TEST ===")
t0 = time.perf_counter()
r1 = svc.predict_risk(latitude=18.52, longitude=73.86, lead_hours=72, variable="precipitation",
    forecast_val=8.5, forecast_precip=8.5, forecast_temp=27.0, forecast_wind=12.0,
    forecast_press=1005.0, ensemble_spread=2.5, run_revision=0.5, include_explanation=False)
r2 = svc.predict_risk(latitude=18.52, longitude=73.86, lead_hours=72, variable="precipitation",
    forecast_val=8.5, forecast_precip=8.5, forecast_temp=27.0, forecast_wind=12.0,
    forecast_press=1005.0, ensemble_spread=2.5, run_revision=0.5, include_explanation=False)
det_ms = (time.perf_counter() - t0) * 1000
bp1, bp2 = r1.get("bust_probability"), r2.get("bust_probability")
print(f"  Run 1: {bp1}, Run 2: {bp2}")
print(f"  Deterministic: {bp1 == bp2}")

print()
print("=== SECTION 4: PERFORMANCE SUMMARY ===")
arr = np.array(latencies) if latencies else np.array([0])
print(f"  n       = {len(latencies)}")
print(f"  mean    = {arr.mean():.2f} ms")
print(f"  p50     = {np.percentile(arr, 50):.2f} ms")
print(f"  p95     = {np.percentile(arr, 95):.2f} ms")
print(f"  p99     = {np.percentile(arr, 99):.2f} ms")
print(f"  min     = {arr.min():.2f} ms")
print(f"  max     = {arr.max():.2f} ms")

total  = len(results)
passed = sum(1 for r in results if r["status"] == "PASS")
failed = sum(1 for r in results if r["status"] in ("FAIL", "ERROR"))
print()
print(f"  Total: {total}  PASS: {passed}  FAIL/ERROR: {failed}")
print(f"  Error rate: {failed/total*100:.2f}%")

if failures:
    print()
    print("=== FAILURES ===")
    for f in failures:
        print(f"  {f}")

stats = {
    "n":             int(len(latencies)),
    "mean_ms":       float(arr.mean()),
    "p50_ms":        float(np.percentile(arr, 50)),
    "p95_ms":        float(np.percentile(arr, 95)),
    "p99_ms":        float(np.percentile(arr, 99)),
    "min_ms":        float(arr.min()),
    "max_ms":        float(arr.max()),
    "error_rate_pct": float(failed / total * 100) if total else 0,
    "pass_count":    passed,
    "fail_count":    failed,
    "total":         total,
}
with open("scratch/smoke_test_results.json", "w") as f:
    json.dump({
        "results": results, "failures": failures, "latency_stats": stats,
        "deterministic_test": {"run1": bp1, "run2": bp2, "pass": bp1 == bp2}
    }, f, indent=2)
print()
print("Saved: scratch/smoke_test_results.json")
