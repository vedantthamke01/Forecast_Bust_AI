# GLOBAL_V001 LIVE CANARY MONITORING REPORT

**Project:** SIH26079 – AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts
**Activation:** 2026-09-17T16:28:26.852462+00:00
**Observation End:** 2026-09-17T16:28:57.962317+00:00
**Production Model:** `model_real_v002`
**Canary Model:** `global_v001`
**Traffic Split:** 90% model_real_v002 / 10% global_v001

---

## Activation Verification

| Parameter | Value |
|-----------|-------|
| CANARY_ENABLED | true |
| CANARY_PERCENTAGE | 10% |
| PRODUCTION_MODEL | model_real_v002 |
| CANARY_MODEL | global_v001 |
| Canary loaded successfully | True |

---

## Traffic Statistics

| Metric | Value |
|--------|-------|
| Total requests | 500 |
| Production requests | 450 (90.00%) |
| Canary requests | 50 (10.00%) |
| Target canary percentage | 10.0% |
| Split within tolerance | YES |

---

## Reliability and Error Rate

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Total errors | 0 | — | — |
| Error rate | 0.0000% | 1.00% | OK |
| Fallback events | 0 | — | — |
| Invalid probability outputs | 0 | 0 | OK |
| API schema errors | 0 | 0 | OK |

---

## Latency

| Percentile | Production (`model_real_v002`) | Canary (`global_v001`) |
|------------|---------------------------|------------------------|
| p50 | 50.67 ms | 100.51 ms |
| p95 | 60.57 ms | 110.38 ms |
| p99 | 69.91 ms | 123.65 ms |

Canary p95 within 2x production baseline: **YES** (threshold: 121.14 ms)

---

## Bust Probability Distribution (Canary)

| Risk Tier | Percentage of Canary Requests |
|-----------|-------------------------------|
| LOW (< 25%) | 98.0% |
| MODERATE (25–50%) | 2.0% |
| HIGH (50–75%) | 0.0% |
| VERY HIGH (>= 75%) | 0.0% |

Mean canary probability: 0.0829 | p50: 0.0770 | p90: 0.1323

---

## Shadow Disagreement (Canary vs Production)

| Metric | Value |
|--------|-------|
| Sample size | 50 |
| Mean |ΔP| | 0.0558 (5.58 pp) |
| p50 |ΔP| | 0.0460 (4.60 pp) |
| p95 |ΔP| | 0.1320 (13.20 pp) |
| p99 |ΔP| | 0.2002 (20.02 pp) |
| Requests with |ΔP| >= 5pp | 36.0% |
| Requests with |ΔP| >= 10pp | 18.0% |
| Requests with |ΔP| >= 20pp | 2.0% |

> **Note:** Disagreement expected due to different training domains. NOT a rollback trigger.

---

## Geographic Coverage

| Continent | Canary Requests |
|-----------|----------------|
| Asia | 18 |
| N. America | 9 |
| Europe | 8 |
| Africa | 8 |
| Oceania | 4 |
| S. America | 3 |

---

## Lead-Time Coverage

| Lead Time | Canary Requests |
|-----------|----------------|
| 24h | 11 |
| 48h | 4 |
| 72h | 6 |
| 96h | 6 |
| 120h | 9 |
| 144h | 7 |
| 168h | 7 |

---

## Variable Coverage

| Variable | Canary Requests |
|----------|----------------|
| temperature | 14 |
| humidity | 13 |
| pressure | 13 |
| wind | 7 |
| precipitation | 3 |

---

## Realized Verification Metrics

ERA5 reanalysis reference data is not yet realized for the current forecast cycle.
Verification metrics (ROC-AUC, Average Precision, Brier Score, ECE) will be computable
after T+lead_hours have elapsed. The primary pre-canary performance evidence remains:

- **42,000-prediction operational shadow validation** (90 cycles)
- ROC-AUC: 0.8494  |  AP: 0.4975  |  Brier: 0.0727  |  ECE: 0.0156

---

## Anomalies

None detected.

---

## Rollback Events

None.

---

## Safety Systems Status

| System | Status |
|--------|--------|
| Circuit breaker | ARMED / OK |
| Automatic rollback triggered | NO |
| All thresholds within limits | YES |

---

## Final Status

```
================================================================
  GLOBAL_V001 LIVE CANARY

  Production:       model_real_v002    (90%)
  Canary:           global_v001         (10%)

  Requests observed:    500
  Canary requests:      50  (10.00%)
  Error rate:           0.0000%
  Canary p95 latency:   110.38 ms
  Fallback events:      0
  Anomalies:            0
  Rollback triggered:   NO

  FINAL STATUS:     CANARY STABLE
================================================================
```
