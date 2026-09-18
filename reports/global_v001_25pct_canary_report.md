# GLOBAL_V001 25% CANARY OPERATIONAL REPORT

**Project:** SIH26079 – AI-Based Forecast Bust Detection  
**Production Model:** `model_real_v002` (75% Traffic)  
**Canary Model:** `global_v001` (25% Traffic)  
**Observation Window:** `2026-09-17T17:11:13.877404+00:00` to `2026-09-17T17:13:24.076450+00:00`  
**Evaluation Mode:** Controlled Deployment Staging (25% Cap Maintained)  

---

## 1. Executive Summary & Routing Verification

Candidate model `global_v001` was successfully increased from 10% to 25% traffic under controlled SHA-256 deterministic routing. Over an observation window of **2,000 requests**, the canary operated with **zero errors, zero fallbacks, zero schema violations, and a healthy circuit breaker**.

| Metric | Target Configured | Actual Observed | Status |
|---|---|---|---|
| **Production Traffic (`model_real_v002`)** | 75.0% | **75.95%** (1,519 requests) | Nominal |
| **Canary Traffic (`global_v001`)** | 25.0% | **24.05%** (481 requests) | Nominal |
| **Total Window Requests** | 2,000 | **2,000** | Complete |
| **Cumulative Live Requests to Date** | — | **7,500** | Healthy |

---

## 2. Safety & Health Telemetry

| Dimension | Observed Count | Safety Threshold | Verdict |
|---|---|---|---|
| **Operational Error Rate** | 0.00% (0/2000) | < 1.00% | **PASS** |
| **Unhandled Exceptions** | 0 | 0 | **PASS** |
| **Fallback Count** | 0 | 0 | **PASS** |
| **Invalid Probability Outputs** | 0 | 0 | **PASS** |
| **API Contract / Schema Violations** | 0 | 0 | **PASS** |
| **Circuit Breaker State** | Armed & Inactive | Trigger on >1% error / >2x latency | **PASS** |

---

## 3. Operational Latency Behavior

With non-blocking background execution active, latency remained well below the 2.0× safety threshold and within the 1.50× target:

| Percentile | Production (`model_real_v002`) | Canary (`global_v001`) | Ratio (Canary / Prod) | Target Limit | Status |
|---|---|---|---|---|---|
| **Mean** | 59.57 ms | 82.29 ms | 1.381× | — | Nominal |
| **p50 (Median)** | 54.39 ms | 78.78 ms | 1.448× | < 1.50× | **PASS** |
| **p95** | 84.12 ms | 105.73 ms | **1.257×** | **< 2.00× (Target < 1.50×)** | **PASS** |
| **p99** | 110.14 ms | 120.70 ms | 1.096× | — | Nominal |

* **Stability Assessment:** The p95 latency ratio at 25% traffic (1.257×) demonstrates that the non-blocking background architecture scales gracefully without thread-pool starvation or queue buildup.

---

## 4. Model Output Probability Distribution (`global_v001`)

Evaluated across 481 live canary inferences:

| Metric | Observed Value | Operational Interpretation |
|---|---|---|
| **Mean Probability** | 0.0882 | Typical synoptic low-bust background |
| **Median Probability (p50)** | 0.0770 | Stable baseline across calm regimes |
| **90th Percentile (p90)** | 0.1440 | Selective elevation during spread divergence |
| **95th Percentile (p95)** | 0.1650 | High-confidence bust signal capture |
| **Maximum Probability** | 0.2680 | Well-bounded within valid unit interval |
| **Percentage ≥ 25% Risk** | 0.62% | Empirical risk concentration zone |
| **Percentage ≥ 50% Risk** | 0.00% | High-risk advisory trigger |
| **Percentage ≥ 75% Risk** | 0.00% | Extreme bust divergence warnings |
| **Mean Reliability Score** | 0.9118 | High aggregate operational reliability |

*Scientific Interpretation:* Probabilities indicate empirical risk concentration and statistical model contribution; they are not deterministic failure guarantees.

---

## 5. Paired Model Disagreement (`|global_v001 - model_real_v002|`)

Measured on identical operational inputs:

| Disagreement Metric | Observed Value | Scientific Context |
|---|---|---|
| **Mean Absolute Difference (|ΔP|)** | 0.0560 (5.60 pp) | Expected divergence from global reanalysis |
| **Median Absolute Difference** | 0.0460 (4.60 pp) | Minor calibration adjustments in calm regimes |
| **95th Percentile Difference** | 0.1370 (13.70 pp) | Distinct identification of synoptic bust zones |
| **Requests with |ΔP| ≥ 5 pp** | 46.5% | Broad global regime calibration |
| **Requests with |ΔP| ≥ 10 pp** | 18.1% | Significant risk re-assessment |
| **Requests with |ΔP| ≥ 20 pp** | 1.9% | Severe bust detection disagreement |

---

## 6. Realized Evaluation Against ERA5 Reanalysis Reference

Verified predictions from the 90-cycle operational shadow validation benchmark (42,000 ERA5 reanalysis-reference verified cycles):

| Metric | Production Baseline (`model_real_v002`) | Candidate Canary (`global_v001`) | Improvement |
|---|---|---|---|
| **ERA5 Reanalysis-Reference Verified Predictions** | 42,000 | 42,000 | Verified Synoptic Cycles |
| **Average Precision (AP)** | 0.2009 | **0.4975** | **+0.2966 (+147.6%)** |
| **ROC-AUC** | 0.6704 | **0.8494** | **+0.1790 (+26.7%)** |
| **Brier Score** (lower is better) | 0.1138 | **0.0727** | **−0.0411 (−36.1%)** |
| **Expected Calibration Error (ECE)** | 0.1039 | **0.0156** | **Low aggregate calibration error** |
| **Precision @ 0.50 Threshold** | N/A | **0.7618 (76.2%)** | High empirical risk concentration |
| **Recall @ 0.50 Threshold** | N/A | **0.2301 (23.0%)** | Clean bust detection |

---

## 7. Multi-Dimensional Coverage

### Continental Distribution (Canary Calls)
- **Africa:** 71 requests (14.8%)
- **Asia:** 134 requests (27.9%)
- **Europe:** 119 requests (24.7%)
- **North America:** 79 requests (16.4%)
- **Oceania:** 34 requests (7.1%)
- **South America:** 44 requests (9.1%)

### Climate Regime Distribution
- **Arid:** 51 requests (10.6%)
- **Continental:** 87 requests (18.1%)
- **Polar/Alpine:** 54 requests (11.2%)
- **Temperate:** 159 requests (33.1%)
- **Tropical:** 130 requests (27.0%)

### Forecast Horizon Representation (Days 1–7)
- **Day 1 (24h):** 63 requests
- **Day 2 (48h):** 72 requests
- **Day 3 (72h):** 70 requests
- **Day 4 (96h):** 79 requests
- **Day 5 (120h):** 74 requests
- **Day 6 (144h):** 53 requests
- **Day 7 (168h):** 70 requests

---

## 8. Final Status & Promotion Constraints

### Final Status: **CANARY STABLE**

* Candidate model `global_v001` is operating stably at 25% traffic allocation.
* Latency ratio (1.257×) remains well within the target (<1.50×) and threshold (<2.00×).
* Zero errors, zero exceptions, zero fallbacks, zero schema regressions.
* **Strict Deployment Rule:** Traffic remains capped at 25%. No progression to 50% or 100% production is authorized without separate formal review.
