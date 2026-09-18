# GLOBAL_V001 CONTROLLED CANARY READINESS REPORT

**Project:** SIH26079 – AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts  
**Report Date:** 2026-09-17T16:19:43 UTC  
**Prepared by:** Antigravity Automated Canary Validation System  

---

## Executive Summary

Candidate model `global_v001` has completed the controlled canary deployment readiness
validation and staging benchmark. All six validation phases passed.

> [!IMPORTANT]
> **Production model `model_real_v002` remains unchanged.** `models/registry.json` was not
> modified. `global_v001` is deployed in a **10% canary configuration only**, behind a
> configuration flag that defaults to `CANARY_ENABLED=false`.

---

## A. Routing Configuration

| Parameter | Value |
|-----------|-------|
| Routing mechanism | Deterministic SHA-256 hash over (lat, lon, lead\_hours, variable) |
| Canary percentage | 10% |
| Production percentage | 90% |
| Enabled by default | **No** (`CANARY_ENABLED=false`) |
| Configuration key | `CANARY_ENABLED`, `CANARY_PERCENTAGE`, `CANARY_MODEL`, `PRODUCTION_MODEL` |
| Reversible | Yes – configuration-only, no retraining required |
| Isolated from artifacts | Yes – model weights not modified |

Determinism guarantee: the same request context (`lat`, `lon`, `lead_hours`, `variable`)
always maps to the same model. Random coin-flipping is not used.

---

## B. Model Versions

| Role | Model Version | Dataset |
|------|--------------|---------|
| Production | `model_real_v002` | `dataset_real_v002` (37,800 records, 15 Indian stations) |
| Canary | `global_v001` | `dataset_global_v001` (504,000 records, 200 stations, 6 continents) |

`models/registry.json` → `production_model` remains `"model_real_v002"`. **Not modified.**

---

## C. Traffic Split

| Metric | Value |
|--------|-------|
| Total requests simulated | 1,000 |
| Production requests | 911 (91.10%) |
| Canary requests | 89 (8.90%) |
| Target percentage | 10.0% |
| Tolerance | ±4 percentage points |
| **Result** | **PASS** |

---

## D. Request Count

| Measurement | Count |
|-------------|-------|
| Traffic split simulation | 1,000 |
| Latency benchmark samples | 100 |
| Shadow disagreement samples | 60 (20 stations × 3 lead times) |

---

## E. Success Rate

| Model | Validity Errors | Success Rate |
|-------|----------------|--------------|
| `model_real_v002` (production) | 0 | 100% |
| `global_v001` (canary) | 0 | 100% |

---

## F. Error Rate

| Metric | Value |
|--------|-------|
| Canary validity errors | 0 |
| Canary error rate (staging) | 0.00% |
| Circuit-breaker threshold | 1.0% |
| **Status** | **Well below threshold** |

---

## G. Latency

| Percentile | Production (`model_real_v002`) | Canary (`global_v001`) | Delta |
|------------|-------------------------------|------------------------|-------|
| Mean | 48.71 ms | 49.55 ms | +0.84 ms |
| p50 | 48.22 ms | 48.18 ms | −0.04 ms |
| p95 | 53.82 ms | 58.02 ms | +4.20 ms |
| p99 | 59.33 ms | 69.80 ms | +10.47 ms |

Canary p95 (58.02 ms) is within the 2× production baseline (107.64 ms threshold).

**Latency Result: PASS**

---

## H. Probability Validity

| Metric | Value |
|--------|-------|
| Global stations checked | 20 (all 6 continents) |
| Outputs with NaN/Inf | 0 |
| Outputs outside [0.0, 1.0] | 0 |
| **Result** | **PASS** |

All canary probabilities are finite, positive, and within the valid probability interval.

---

## I. API Compatibility

| Schema Key | Present in Production | Present in Canary |
|------------|-----------------------|-------------------|
| `bust_probability` | ✓ | ✓ |
| `bust_probability_percentage` | ✓ | ✓ |
| `reliability_score` | ✓ | ✓ |
| `reliability_percentage` | ✓ | ✓ |
| `risk_level` | ✓ | ✓ |
| `risk_badge` | ✓ | ✓ |
| `model_version` | ✓ | ✓ |
| `dataset_version` | ✓ | ✓ |
| `data_type` | ✓ | ✓ |
| `explanation` | ✓ | ✓ |
| `scientific_governance` | ✓ | ✓ |
| `disclaimer` | ✓ | ✓ |
| `location` | ✓ | ✓ |
| `forecast_horizon_hours` | ✓ | ✓ |
| `lead_time_group` | ✓ | ✓ |
| `initialization_time` | ✓ | ✓ |
| `valid_time` | ✓ | ✓ |

Schema errors: **0**. Flutter / client consumers will receive identical response structure.

**API Compatibility Result: PASS**

---

## J. Rollback Test

| Test | Result |
|------|--------|
| Circuit breaker triggered at >1% simulated error rate | YES |
| Rollback mechanism | Configuration-only (`CANARY_ENABLED=false`) |
| Rollback latency | **70.0 ms** (zero retraining) |
| Model artifacts preserved | YES |
| Shadow logs preserved | YES |
| Evidence preserved | YES |

**Rollback Result: PASS**

---

## K. Regression Tests

| Suite | Passed | Failed | Duration |
|-------|--------|--------|----------|
| Pre-canary baseline | 85 | 0 | 31.25s |
| + Canary deployment tests (12 new) | **97** | **0** | **31.81s** |

New canary test coverage:
- `test_canary_disabled_by_default` — 100% routes production when disabled
- `test_canary_deterministic_routing` — same context always maps same model
- `test_canary_traffic_split_distribution` — ~10%/90% split across 2,000 samples
- `test_canary_response_schema_invariance` — key-for-key schema equivalence
- `test_canary_probability_validity` — 100 random global coordinates, all valid
- `test_canary_failsafe_fallback_on_exception` — crash in canary → production fallback
- `test_canary_circuit_breaker_error_rate` — >1% error rate trips breaker
- `test_canary_circuit_breaker_latency_degradation` — 3 consecutive latency breaches trip breaker
- `test_canary_shadow_delta_calculation` — |ΔP| metrics recorded correctly
- `test_canary_sanitized_logging` — zero secrets/tokens/PII in audit log
- `test_canary_telemetry_structure` — all telemetry sections present
- `test_canary_instant_rollback` — disable routes 100% to production immediately

**Regression Result: 97/97 PASS**

---

## L. Model Disagreement (Shadow Comparison)

Computed across 60 paired requests (20 global stations × 3 lead times: 48h, 96h, 144h):

| Metric | Value |
|--------|-------|
| Sample size | 60 |
| Mean \|ΔP\| | 0.0632 (6.32 pp) |
| p50 \|ΔP\| | 0.0525 (5.25 pp) |
| p95 \|ΔP\| | 0.1602 (16.02 pp) |
| p99 \|ΔP\| | 0.2087 (20.87 pp) |
| Requests with \|ΔP\| ≥ 5pp | 51.67% |
| Requests with \|ΔP\| ≥ 10pp | 23.33% |
| Requests with \|ΔP\| ≥ 20pp | 5.00% |

> [!NOTE]
> Disagreement is **expected** and scientifically explained: `global_v001` was trained on
> 504,000 records across 200 stations on 6 continents, while `model_real_v002` was trained on
> 15 Indian stations. The models have fundamentally different calibration regimes for
> non-Indian geographies. Disagreement is **NOT** a rollback trigger. Previous shadow
> validation established `global_v001` superiority on 42,000 operational cases (AP +0.30,
> AUC +0.18, ECE −0.088).

---

## M. Geographic Distribution

| Continent | Sample Stations |
|-----------|----------------|
| Asia | Pune, Delhi, Chennai, Tokyo, Singapore |
| Europe | London, Paris, Berlin |
| Africa | Cairo, Nairobi |
| North America | Denver, New York, Phoenix |
| South America | São Paulo, Buenos Aires |
| Oceania | Sydney, Melbourne |
| High-latitude | Oslo, Reykjavik, Antarctic station |

**Continents covered: 6 / 6**

---

## N. Anomalies

**None detected.**

No unexpected probability spikes, no schema violations, no encoding errors in canary output,
no crash or exception during staged benchmark.

---

## O. Final Canary Status

```
================================================================
  GLOBAL_V001 CONTROLLED CANARY

  Production:          model_real_v002
  Canary:              global_v001
  Traffic:             90% / 10%
  Canary Enabled:      NO (CANARY_ENABLED=false, requires explicit activation)

  Routing:             PASS
  API Compatibility:   PASS
  Probability Valid:   PASS
  Latency:             Prod p95=53.82ms  Canary p95=58.02ms
  Error Rate:          0.00% (threshold: 1.0%)
  Rollback:            PASS (70.0ms, config-only)
  Regression:          97/97 PASS
  Automatic Safety:    PASS

  FINAL STATUS:        CANARY READY
================================================================
```

---

## Automatic Safety Systems

| System | Trigger Condition | Status |
|--------|------------------|--------|
| Circuit breaker – error rate | Canary error rate > 1.0% | ARMED |
| Circuit breaker – exceptions | >= 3 consecutive exceptions | ARMED |
| Circuit breaker – latency | p95 > 2× production for 3 consecutive windows | ARMED |
| Fail-safe fallback | Any output validation failure | ARMED |
| NaN/Inf guard | Non-finite probability → fallback + log | ARMED |
| Schema guard | Missing required response key → fallback + CB | ARMED |
| Probability bound guard | Probability outside [0.0, 1.0] → fallback | ARMED |

All automatic safety systems are operational. They activate and route 100% to
`model_real_v002` in < 100ms without any manual intervention, retraining, or artifact
modification.

---

## Next Action

Set `CANARY_ENABLED=true` in the environment configuration (`.env` or deployment config)
to begin the controlled 10% canary. The existing circuit-breaker and fail-safe systems
will autonomously protect production traffic.

Do **not** increase canary percentage beyond 10% without a separate explicit deployment
decision backed by additional operational evidence.
