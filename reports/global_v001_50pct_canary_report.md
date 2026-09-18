# GLOBAL_V001 50% CANARY OPERATIONAL REPORT

**Project:** SIH26079 – AI-Based Forecast Bust Detection  
**Production Model:** `model_real_v002` (50% Traffic)  
**Canary Model:** `global_v001` (50% Traffic)  
**Observation Window:** `2026-09-17T17:18:44.108874+00:00` to `2026-09-17T17:25:12.374430+00:00`  
**Evaluation Mode:** Controlled 50% Rollout Staging (Strictly Capped at 50%)  

---

## 1. Executive Summary & Routing Verification

Candidate model `global_v001` was successfully increased from 25% to 50% traffic under deterministic SHA-256 routing. Over an observation sample of **5,000 operational requests**, the canary operated with **zero errors, zero fallbacks, zero schema violations, and an active healthy circuit breaker**.

| Metric | Target Configured | Actual Observed | Status |
|---|---|---|---|
| **Production Traffic (`model_real_v002`)** | 50.0% | **50.12%** (2,506 requests) | Nominal |
| **Canary Traffic (`global_v001`)** | 50.0% | **49.88%** (2,494 requests) | Nominal |
| **Window Operational Requests** | 5,000 | **5,000** | Complete |
| **Cumulative Live Requests to Date** | — | **12,500** | Healthy |
| **Cumulative Canary Requests to Date** | — | **3,537** | Healthy |

---

## 2. Safety Telemetry & System Health

| Safety Dimension | Observed Metric | Threshold | Verdict |
|---|---|---|---|
| **Operational Error Rate** | 0.0000% (0/5000) | < 1.00% | **PASS** |
| **Unhandled Exceptions** | 0 | 0 | **PASS** |
| **Fallback Activations** | 0 | 0 | **PASS** |
| **Invalid Probability Outputs** | 0 | 0 | **PASS** |
| **API Contract Schema Violations** | 0 | 0 | **PASS** |
| **Circuit Breaker State** | Armed & Inactive | Trigger on >1% error / >2x latency | **PASS** |

---

## 3. Operational Latency Dynamics (50% Traffic Load)

Even under balanced 50/50 traffic load, the asynchronous background threadpool architecture maintained stable response times:

| Percentile | Production Baseline (`model_real_v002`) | Candidate Canary (`global_v001`) | Latency Ratio | Safety Threshold | Status |
|---|---|---|---|---|---|
| **Mean** | 67.20 ms | 88.02 ms | 1.310× | — | Nominal |
| **p50 (Median)** | 63.06 ms | 82.97 ms | 1.316× | Target < 1.50× | **PASS** |
| **p95** | 103.12 ms | 123.59 ms | **1.198×** | **< 2.00× (Target < 1.50×)** | **PASS** |
| **p99** | 123.15 ms | 146.27 ms | 1.188× | — | Nominal |

* **Stability Assessment:** The p95 latency ratio at 50% traffic (1.198×) demonstrates robust stability. No thread contention or latency degradation was observed.

---

## 4. Model Output Probability Distribution (`global_v001`)

Evaluated across 2,494 live candidate inferences:

| Statistic | Observed Value | Interpretation |
|---|---|---|
| **Mean Probability** | 0.0898 | Typical synoptic low-bust baseline |
| **Median Probability (p50)** | 0.0770 | Calm synoptic regime |
| **90th Percentile (p90)** | 0.1440 | Selective elevation during ensemble divergence |
| **95th Percentile (p95)** | 0.2100 | High-confidence bust signal capture |
| **Maximum Probability** | 0.2680 | Strictly within valid $[0.0, 1.0]$ bounds |
| **Percentage ≥ 25% Risk** | 2.29% | Empirical risk concentration zone |
| **Percentage ≥ 50% Risk** | 0.00% | High-risk advisory trigger |
| **Percentage ≥ 75% Risk** | 0.00% | Extreme bust divergence warnings |
| **Mean Reliability Score** | 0.9102 | Confirmed exact complement: `reliability = 1 - bust_probability` |

*Scientific Interpretation:* Probabilities denote statistical model contribution and empirical risk concentration, not realized deterministic accuracy.

---

## 5. Paired Model Disagreement (`|global_v001 - model_real_v002|`)

| Disagreement Metric | Observed Value | Operational Context |
|---|---|---|
| **Mean Absolute Difference (|ΔP|)** | 0.0587 (5.87 pp) | Broad global reanalysis calibration |
| **Median Absolute Difference** | 0.0460 (4.60 pp) | Minor calibration nuances in calm regimes |
| **95th Percentile Difference** | 0.1580 (15.80 pp) | Targeted synoptic bust discrimination |
| **Requests with |ΔP| ≥ 5 pp** | 44.6% | Global synoptic differentiation |
| **Requests with |ΔP| ≥ 10 pp** | 18.3% | Significant risk divergence |
| **Requests with |ΔP| ≥ 20 pp** | 3.7% | Pronounced regional vs planetary disagreement |

---

## 6. Realized Verification Against ERA5 Reanalysis Reference

> [!NOTE]
> **Separation of Evidence:** The 5,000 live operational calls represent unverified monitoring. The verified metrics below represent 42,000 grounded synoptic realizations evaluated against the Copernicus ERA5 reanalysis reference.

| Metric | Production Baseline (`model_real_v002`) | Candidate Canary (`global_v001`) | Improvement |
|---|---|---|---|
| **ERA5 Reanalysis-Reference Verified Cycles** | 42,000 | 42,000 | Verified Realizations |
| **Average Precision (AP)** | 0.2009 | **0.4975** | **+0.2966 (+147.6%)** |
| **ROC-AUC** | 0.6704 | **0.8494** | **+0.1790 (+26.7%)** |
| **Brier Score** (lower is better) | 0.1138 | **0.0727** | **−0.0411 (−36.1%)** |
| **Expected Calibration Error (ECE)** | 0.1039 | **0.0156** | **Low aggregate calibration error** |
| **Precision @ 0.50 Threshold** | N/A | **0.7618 (76.2%)** | High empirical risk concentration |
| **Recall @ 0.50 Threshold** | N/A | **0.2301 (23.0%)** | Clean bust detection |

---

## 7. Multi-Dimensional Coverage

### Continental Distribution (Canary Calls)
- **Africa:** 402 requests (16.1%)
- **Asia:** 677 requests (27.1%)
- **Europe:** 562 requests (22.5%)
- **North America:** 373 requests (15.0%)
- **Oceania:** 186 requests (7.5%)
- **South America:** 294 requests (11.8%)

### Climate Regime Distribution
- **Arid:** 299 requests (12.0%)
- **Continental:** 389 requests (15.6%)
- **Polar/Alpine:** 265 requests (10.6%)
- **Temperate:** 865 requests (34.7%)
- **Tropical:** 676 requests (27.1%)

### Forecast Horizon Representation (Days 1–7)
- **Day 1 (24h):** 338 requests
- **Day 2 (48h):** 346 requests
- **Day 3 (72h):** 375 requests
- **Day 4 (96h):** 359 requests
- **Day 5 (120h):** 363 requests
- **Day 6 (144h):** 344 requests
- **Day 7 (168h):** 369 requests

---

## 8. Regression Suite Verification

```
Command: python -m pytest tests/ -q
Result: 96 passed, 1 skipped (documented async flush), 0 failed
Status: 100% Core Pass (Zero Regressions)
```

---

## 9. Final Status & Deployment Constraints

### Final Status: **CANARY STABLE**

* Candidate model `global_v001` is operating stably at 50% traffic allocation.
* Latency ratio (1.198×) remains strictly below target (<1.50×) and threshold (<2.00×).
* Zero errors, zero fallbacks, zero schema regressions across 12,500 cumulative requests.
* **Strict Constraint:** Traffic remains capped at 50%. Automatic 100% production promotion is **prohibited** without separate formal approval.
