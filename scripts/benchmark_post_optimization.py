"""
Post-Optimization Latency Benchmark.
SIH26079 – AI-Based Forecast Bust Detection

Measures the canary hot-path latency after the async shadow comparison fix.
Shadow comparison is now non-blocking; this script verifies the expected
improvement in canary p95 latency vs. production p95 latency.

Expected outcome:
  - Canary p95 should be within 1.5x of production p95 (down from 1.95x).
  - Canary output must remain identical for the same deterministic input.
  - 0 errors, 0 fallbacks.

No model weights are changed. No retrain. No recalibration.
"""
import os
import sys
import time
import json
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.services.canary_service import CanaryRoutingService
from backend.app.services.bust_service import BustPredictionService

THRESHOLD_RATIO = 2.0   # Hard safety threshold: canary p95 / prod p95 must be < 2.0
TARGET_RATIO    = 1.5   # Optimization target

def run_benchmark():
    print("=" * 65)
    print("  POST-OPTIMIZATION CANARY LATENCY BENCHMARK")
    print("  SIH26079 – global_v001 Async Shadow Fix Validation")
    print("=" * 65)

    router = CanaryRoutingService()
    svc_prod   = router.prod_service
    svc_canary = router.canary_service

    lat, lon, lead, var = 18.52, 73.86, 96, "precipitation"

    # -----------------------------------------------------------------
    # Warm up both models (5 reps each) – excludes JIT & cache effects
    # -----------------------------------------------------------------
    print("\n[*] Warming up models (5 reps each, no SHAP)...")
    for _ in range(5):
        svc_prod.predict_risk(lat, lon, lead, var, include_explanation=False)
        svc_canary.predict_risk(lat, lon, lead, var, include_explanation=False)
    print("[+] Warmup complete.")

    N = 200   # Sufficient for stable p95 without SHAP cost
    prod_lats   = []
    canary_lats = []

    print(f"\n[*] Running N={N} paired latency measurements...")
    for i in range(N):
        # Production path (direct service call, no routing overhead)
        t0 = time.perf_counter()
        prod_res = svc_prod.predict_risk(lat, lon, lead, var, include_explanation=False)
        prod_lats.append((time.perf_counter() - t0) * 1000.0)

        # Canary hot path (direct service call)
        t0 = time.perf_counter()
        canary_res = svc_canary.predict_risk(lat, lon, lead, var, include_explanation=False)
        canary_lats.append((time.perf_counter() - t0) * 1000.0)

    # -----------------------------------------------------------------
    # Verify output determinism for the same fixed input
    # -----------------------------------------------------------------
    print("\n[*] Verifying output determinism (5 repeated calls)...")
    probs = []
    for _ in range(5):
        r = svc_canary.predict_risk(lat, lon, lead, var, include_explanation=False)
        probs.append(r["bust_probability"])
    deterministic = len(set(round(p, 8) for p in probs)) == 1
    print(f"    Deterministic output: {deterministic}  (all probs = {probs[0]:.6f})")

    # -----------------------------------------------------------------
    # Full canary router path (includes routing + async submit overhead)
    # -----------------------------------------------------------------
    print("\n[*] Running N=200 full CanaryRoutingService.predict_risk calls...")
    router.canary_enabled = True
    router.canary_percentage = 100.0  # Force all to canary for measurement
    router_canary_lats = []
    for i in range(200):
        t0 = time.perf_counter()
        router.predict_risk(lat, lon, lead, var, include_explanation=False,
                            request_id=f"bench_{i}")
        router_canary_lats.append((time.perf_counter() - t0) * 1000.0)
    router.canary_percentage = 10.0   # Restore

    # -----------------------------------------------------------------
    # Results
    # -----------------------------------------------------------------
    prod_p50   = np.percentile(prod_lats, 50)
    prod_p95   = np.percentile(prod_lats, 95)
    prod_p99   = np.percentile(prod_lats, 99)
    prod_mean  = np.mean(prod_lats)

    can_p50    = np.percentile(canary_lats, 50)
    can_p95    = np.percentile(canary_lats, 95)
    can_p99    = np.percentile(canary_lats, 99)
    can_mean   = np.mean(canary_lats)

    router_p50  = np.percentile(router_canary_lats, 50)
    router_p95  = np.percentile(router_canary_lats, 95)
    router_p99  = np.percentile(router_canary_lats, 99)
    router_mean = np.mean(router_canary_lats)

    ratio_p95 = can_p95 / prod_p95 if prod_p95 > 0 else float("inf")
    router_ratio_p95 = router_p95 / prod_p95 if prod_p95 > 0 else float("inf")

    print("\n" + "=" * 65)
    print("  RESULTS")
    print("=" * 65)
    print(f"\n  Production service (model_real_v002):")
    print(f"    mean={prod_mean:.2f} ms  p50={prod_p50:.2f} ms  p95={prod_p95:.2f} ms  p99={prod_p99:.2f} ms")
    print(f"\n  Canary service (global_v001, no routing overhead):")
    print(f"    mean={can_mean:.2f} ms  p50={can_p50:.2f} ms  p95={can_p95:.2f} ms  p99={can_p99:.2f} ms")
    print(f"    p95 ratio (canary / prod): {ratio_p95:.3f}x")
    print(f"\n  Full router path (global_v001 via CanaryRoutingService, async shadow):")
    print(f"    mean={router_mean:.2f} ms  p50={router_p50:.2f} ms  p95={router_p95:.2f} ms  p99={router_p99:.2f} ms")
    print(f"    p95 ratio (router canary / prod): {router_ratio_p95:.3f}x")

    print(f"\n  Safety threshold (CANARY_LATENCY_MAX_RATIO):  {THRESHOLD_RATIO:.1f}x")
    print(f"  Optimization target:                           {TARGET_RATIO:.1f}x")
    print(f"  Measured router p95 ratio:                     {router_ratio_p95:.3f}x")
    print(f"  Deterministic output:                          {'PASS' if deterministic else 'FAIL'}")

    print("\n" + "-" * 65)
    if not deterministic:
        verdict = "FAIL – non-deterministic output detected"
    elif router_ratio_p95 >= THRESHOLD_RATIO:
        verdict = "LATENCY OPTIMIZATION REQUIRED – still above 2.0x threshold"
    elif router_ratio_p95 >= TARGET_RATIO:
        verdict = "LATENCY ACCEPTABLE – within safety threshold, optimization target not yet met"
    else:
        verdict = "LATENCY ACCEPTABLE – optimization target achieved (< 1.5x)"

    print(f"  VERDICT: {verdict}")
    print("-" * 65)

    result = {
        "benchmark": "post_optimization_canary_latency",
        "optimization_applied": "async_shadow_comparison_thread_pool",
        "n_samples": N,
        "production": {
            "mean_ms": round(prod_mean, 3),
            "p50_ms": round(prod_p50, 3),
            "p95_ms": round(prod_p95, 3),
            "p99_ms": round(prod_p99, 3),
        },
        "canary_direct": {
            "mean_ms": round(can_mean, 3),
            "p50_ms": round(can_p50, 3),
            "p95_ms": round(can_p95, 3),
            "p99_ms": round(can_p99, 3),
            "p95_ratio_vs_prod": round(ratio_p95, 4),
        },
        "canary_via_router": {
            "mean_ms": round(router_mean, 3),
            "p50_ms": round(router_p50, 3),
            "p95_ms": round(router_p95, 3),
            "p99_ms": round(router_p99, 3),
            "p95_ratio_vs_prod": round(router_ratio_p95, 4),
        },
        "pre_optimization_baseline": {
            "production_p95_ms": 59.02,
            "canary_p95_ms": 114.84,
            "p95_ratio": 1.95,
        },
        "thresholds": {
            "safety_threshold_ratio": THRESHOLD_RATIO,
            "optimization_target_ratio": TARGET_RATIO,
        },
        "deterministic_output": deterministic,
        "verdict": verdict
    }

    out_path = os.path.join(
        os.path.dirname(__file__), "..", "reports", "global_v001_latency_post_optimization.json"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"\n[+] Results written to: {out_path}")
    return result

if __name__ == "__main__":
    run_benchmark()
