# global_v001 Canary Latency Investigation & Optimization Report

**Project:** SIH26079 – AI-Based Forecast Bust Detection  
**Date:** 2026-09-17  
**Canary:** global_v001 @ 10% traffic  
**Production:** model_real_v002 @ 90% traffic

---

## FINAL VERDICT: LATENCY ACCEPTABLE

Router canary p95 ratio: **1.295x** (threshold: 2.0x, target: 1.5x)  
Reduction: 114.84ms → 64.3ms (−44%)  
Regression tests: **96/97 passing**  
Model outputs: **unchanged and deterministic**

---

## Root Causes Identified

### Cause 1: Synchronous shadow comparison in CanaryRoutingService.predict_risk
File: backend/app/services/canary_service.py (lines 320-335 pre-fix)

Every canary request called `self.prod_service.predict_risk()` synchronously (~50ms)
before returning the canary result. Labeled "parallel non-blocking" in a comment
but was in fact fully blocking.

### Cause 2: Synchronous shadow inference in BustPredictionService.predict_risk
File: backend/app/services/bust_service.py (lines 157-167 pre-fix)

`ShadowInferenceService.record_shadow_prediction()` performed a full
`extract_features + predict_proba` on global_v001 synchronously on every call
to any BustPredictionService instance (including svc_canary). Canary requests
paid this ~50ms cost twice per request.

---

## Fixes Applied

### Fix 1 — Async shadow comparison (canary_service.py)
- Added module-level `_SHADOW_EXECUTOR = ThreadPoolExecutor(max_workers=4)`
- Shadow comparison and audit log write submitted via `_SHADOW_EXECUTOR.submit()`
- Canary result returned immediately after output validation
- Shadow deltas backfilled into health_monitor by background task

### Fix 2 — Async shadow inference (bust_service.py)
- `ShadowInferenceService.record_shadow_prediction()` submitted to `_SHADOW_EXECUTOR`
- Shadow JSONL log content unchanged, written with brief background delay

### Fix 3 — Test synchronization utility (canary_service.py)
- `flush_shadow_executor()` added for unit test synchronization only
- Never called on hot path

---

## Latency Results (Isolated Single-Call Benchmark, N=50)

| Path                              | p50 (ms) | p95 (ms) | Ratio |
|-----------------------------------|----------|----------|-------|
| Production (model_real_v002)      |  40.7    |  49.6    | 1.000x |
| Canary direct (global_v001)       |  36.3    |  51.0    | 1.027x |
| Router canary path (post-fix)     |  49.0    |  64.3    | 1.295x |

Pre-fix router canary p95: 114.84ms (1.95x)
Post-fix router canary p95: 64.3ms (1.295x)
Improvement: -44% p95 latency, 14x more headroom before circuit-break

---

## Regression Tests
96 passed, 1 skipped, 0 failed

---

## Constraints Preserved
- No model retraining
- No recalibration
- No weight changes
- No hyperparameter changes
- Canary remains at 10%
- 2.0x threshold unchanged
- Shadow comparison data preserved (async)
- Audit log preserved (async)
- Output determinism verified
