"""
In-depth Latency & Profiling Investigation Suite.
Measures:
A. Request parsing
B. Feature construction
C. Model loading
D. global_v001 inference
E. model_real_v002 comparison/shadow inference
F. SHAP generation
G. Serialization
H. Logging/telemetry
I. Routing
J. Memory usage and leaks
"""
import os
import sys
import time
import json
import tracemalloc
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.services.canary_service import CanaryRoutingService
from backend.app.services.bust_service import BustPredictionService
from ml_pipeline.features import extract_features, FEATURE_COLUMNS, GLOBAL_FEATURE_COLUMNS

def profile_breakdown():
    print("=" * 65)
    print("  LATENCY COMPONENT BREAKDOWN BENCHMARK")
    print("=" * 65)

    router = CanaryRoutingService()
    svc_prod = router.prod_service
    svc_canary = router.canary_service

    lat, lon, lead, var = 18.52, 73.86, 96, "precipitation"

    # Warmup
    for _ in range(5):
        svc_prod.predict_risk(lat, lon, lead, var, include_explanation=True)
        svc_canary.predict_risk(lat, lon, lead, var, include_explanation=True)

    N = 100
    times = {
        "routing": [],
        "feature_extraction_prod": [],
        "feature_extraction_canary": [],
        "inference_prod_only": [],
        "inference_canary_only": [],
        "shap_prod": [],
        "shap_canary": [],
        "shadow_prod_call": [],
        "audit_logging": [],
        "canary_path_total": [],
        "prod_path_total": []
    }

    # Dummy dataframe for feature extraction test
    row_dict = {
        "initialization_time": "2026-09-17T12:00:00Z",
        "lead_hours": lead,
        "latitude": lat,
        "longitude": lon,
        "forecast_temperature": 28.0,
        "forecast_precipitation": 5.0,
        "forecast_wind": 6.0,
        "forecast_pressure": 1010.0,
        "forecast_humidity": 75.0,
        "forecast_cloud_cover": 50.0,
        "ensemble_spread": 1.2,
        "run_revision": 0.5
    }
    df_inst = pd.DataFrame([row_dict])

    X_prod, _ = extract_features(df_inst, is_training=False, feature_columns=svc_prod.model_bundle.get("features", FEATURE_COLUMNS))
    X_canary, _ = extract_features(df_inst, is_training=False, feature_columns=svc_canary.model_bundle.get("features", GLOBAL_FEATURE_COLUMNS))

    calibrator_prod = svc_prod.model_bundle["calibrated_model"]
    calibrator_canary = svc_canary.model_bundle["calibrated_model"]

    for i in range(N):
        # 1. Routing
        t0 = time.perf_counter()
        r = router.route_request(lat, lon, lead, var, request_id=f"prof_{i}")
        times["routing"].append((time.perf_counter() - t0) * 1000)

        # 2. Feature Extraction
        t0 = time.perf_counter()
        extract_features(df_inst, is_training=False, feature_columns=svc_prod.model_bundle.get("features", FEATURE_COLUMNS))
        times["feature_extraction_prod"].append((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        extract_features(df_inst, is_training=False, feature_columns=svc_canary.model_bundle.get("features", GLOBAL_FEATURE_COLUMNS))
        times["feature_extraction_canary"].append((time.perf_counter() - t0) * 1000)

        # 3. Model Inference alone
        t0 = time.perf_counter()
        calibrator_prod.predict_proba(X_prod)
        times["inference_prod_only"].append((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        calibrator_canary.predict_proba(X_canary)
        times["inference_canary_only"].append((time.perf_counter() - t0) * 1000)

        # 4. SHAP alone
        t0 = time.perf_counter()
        svc_prod.explainer.explain_instance(X_prod, top_k=4, risk_level="LOW", bust_prob=0.08)
        times["shap_prod"].append((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        svc_canary.explainer.explain_instance(X_canary, top_k=4, risk_level="LOW", bust_prob=0.08)
        times["shap_canary"].append((time.perf_counter() - t0) * 1000)

        # 5. Shadow Prod Call
        t0 = time.perf_counter()
        svc_prod.predict_risk(latitude=lat, longitude=lon, lead_hours=lead, variable=var, include_explanation=False)
        times["shadow_prod_call"].append((time.perf_counter() - t0) * 1000)

        # 6. Audit Logging
        t0 = time.perf_counter()
        router._log_audit_record(
            request_id=f"prof_{i}",
            model_version="global_v001",
            latitude=lat,
            longitude=lon,
            lead_hours=lead,
            variable=var,
            bust_probability=0.08,
            latency_ms=50.0,
            success=True,
            prod_probability=0.05,
            delta_p=0.03,
            abs_delta_p=0.03
        )
        times["audit_logging"].append((time.perf_counter() - t0) * 1000)

        # Full Canary call via router vs Prod call via router
        t0 = time.perf_counter()
        svc_canary.predict_risk(latitude=lat, longitude=lon, lead_hours=lead, variable=var, include_explanation=False)
        times["canary_path_total"].append((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        svc_prod.predict_risk(latitude=lat, longitude=lon, lead_hours=lead, variable=var, include_explanation=False)
        times["prod_path_total"].append((time.perf_counter() - t0) * 1000)

    print("\n--- Latency Component Breakdown (Mean, p50, p95, p99 in ms) ---")
    for k, v in times.items():
        print(f"{k:28s}: mean={np.mean(v):6.2f}  p50={np.percentile(v, 50):6.2f}  p95={np.percentile(v, 95):6.2f}  p99={np.percentile(v, 99):6.2f}")

    # Fair Comparison Suite
    print("\n--- Fair Comparison Execution Paths (N=100) ---")
    paths = {
        "1. model_real_v002 alone (no SHAP)": [],
        "2. global_v001 alone (no SHAP)": [],
        "3. model_real_v002 alone (with SHAP)": [],
        "4. global_v001 alone (with SHAP)": [],
        "5. global_v001 + shadow prod (no SHAP)": [],
        "6. global_v001 + shadow prod + telemetry (Current Canary Path)": [],
    }

    for _ in range(N):
        # 1.
        t0 = time.perf_counter()
        svc_prod.predict_risk(lat, lon, lead, var, include_explanation=False)
        paths["1. model_real_v002 alone (no SHAP)"].append((time.perf_counter() - t0) * 1000)

        # 2.
        t0 = time.perf_counter()
        svc_canary.predict_risk(lat, lon, lead, var, include_explanation=False)
        paths["2. global_v001 alone (no SHAP)"].append((time.perf_counter() - t0) * 1000)

        # 3.
        t0 = time.perf_counter()
        svc_prod.predict_risk(lat, lon, lead, var, include_explanation=True)
        paths["3. model_real_v002 alone (with SHAP)"].append((time.perf_counter() - t0) * 1000)

        # 4.
        t0 = time.perf_counter()
        svc_canary.predict_risk(lat, lon, lead, var, include_explanation=True)
        paths["4. global_v001 alone (with SHAP)"].append((time.perf_counter() - t0) * 1000)

        # 5.
        t0 = time.perf_counter()
        svc_canary.predict_risk(lat, lon, lead, var, include_explanation=False)
        svc_prod.predict_risk(lat, lon, lead, var, include_explanation=False)
        paths["5. global_v001 + shadow prod (no SHAP)"].append((time.perf_counter() - t0) * 1000)

        # 6.
        t0 = time.perf_counter()
        c_res = svc_canary.predict_risk(lat, lon, lead, var, include_explanation=False)
        p_res = svc_prod.predict_risk(lat, lon, lead, var, include_explanation=False)
        router._log_audit_record(
            request_id="test", model_version="global_v001", latitude=lat, longitude=lon,
            lead_hours=lead, variable=var, bust_probability=c_res["bust_probability"],
            latency_ms=100.0, success=True
        )
        paths["6. global_v001 + shadow prod + telemetry (Current Canary Path)"].append((time.perf_counter() - t0) * 1000)

    for k, v in paths.items():
        print(f"{k:60s}: mean={np.mean(v):6.2f}  p50={np.percentile(v, 50):6.2f}  p95={np.percentile(v, 95):6.2f}  p99={np.percentile(v, 99):6.2f}")

    # Memory profiling
    print("\n--- Memory Profiling & Growth (500 iterations) ---")
    tracemalloc.start()
    snap_before = tracemalloc.take_snapshot()

    for i in range(500):
        svc_canary.predict_risk(lat, lon, lead, var, include_explanation=False)

    snap_after = tracemalloc.take_snapshot()
    top_stats = snap_after.compare_to(snap_before, 'lineno')
    total_diff_kb = sum(stat.size_diff for stat in top_stats) / 1024.0
    print(f"Total memory growth over 500 requests: {total_diff_kb:.2f} KB (Avg: {total_diff_kb/500.0:.3f} KB/req)")
    tracemalloc.stop()

if __name__ == "__main__":
    profile_breakdown()
