# Final Project Readiness Report
## SIH26079 — AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts

| Field | Value |
|---|---|
| **Organization** | NCMRWF / MoES |
| **Team** | The Centinels |
| **Production Model** | `global_v001` |
| **Rollback Model** | `model_real_v002` |
| **Canary Enabled** | `false` (100% production) |
| **Git SHA** | `32ae6b1` |
| **Report Date** | 2026-09-18 |

---

## ✅ Verdict: READY FOR SIH DEMONSTRATION

---

## 1. Test Suite

| Metric | Result |
|---|---|
| Passed | **96** |
| Skipped | 1 (documented — extended-range horizon) |
| Failed | **0** |
| Exit Code | `0` |

```
96 passed, 1 skipped, 0 failed in 35.19s
```

---

## 2. Production Model — global_v001

### Frozen Test Metrics (scientifically validated, Days 1–7)

| Metric | Value |
|---|---|
| ROC-AUC | **0.8847** |
| Brier Score | **0.1124** |
| Calibration ECE | **0.0312** |
| Geographic Holdout AUC | **0.8712** |

### Architecture

- **Algorithm**: LightGBM + Isotonic Calibration
- **Features**: 21 production features
- **Dataset**: `dataset_global_v001` (200-station global synthetic)
- **Validated Lead Days**: Days 1–7 (ERA5 reanalysis reference)
- **Extended Range**: Days 8–30 labeled `UNVALIDATED_EXTENDED_RANGE`

---

## 3. Canary / Production Promotion Evidence

| Metric | Value |
|---|---|
| Total cumulative requests | 12,500 |
| Canary requests served | 3,537 |
| Errors | **0** |
| Fallbacks | **0** |
| Schema violations | **0** |
| Invalid outputs | **0** |
| Canary p95 latency | 123.59 ms |
| Production p95 latency | 103.12 ms |
| Latency ratio | **1.198×** (within SLA) |

Rollout stages completed: **25% → 50% → 100%**

---

## 4. Configuration State

```
PRODUCTION_MODEL   = global_v001
ROLLBACK_MODEL     = model_real_v002
CANARY_ENABLED     = false
CANARY_PERCENTAGE  = 0
CIRCUIT_BREAKER    = ARMED
CIRCUIT_BROKEN     = false
```

---

## 5. API Endpoints

| Endpoint | URL |
|---|---|
| Production API | `https://forecast-bust-api.onrender.com` |
| Health | `GET /health` |
| Predict | `POST /api/predict` |
| Risk (location) | `GET /api/risk/location` |
| Risk (map) | `GET /api/risk/map` |
| Canary status | `GET /api/canary/status` |
| Current model | `GET /api/models/current` |

---

## 6. Security

| Check | Status |
|---|---|
| CDS API key redacted in all tracked files | ✅ |
| No plaintext secrets in committed code | ✅ |
| Credential rotation advised (key transiently in git history) | ⚠️ |
| Production URL migrated to `forecast-bust-api.onrender.com` | ✅ |

---

## 7. Known Limitations

- **Day 8–30 outputs are `UNVALIDATED_EXTENDED_RANGE`.** They must never be presented as scientifically validated forecasts.
- ERA5 is used as a **reanalysis reference**, not ground truth.
- `global_v001` trained on synthetic global station data; real NCMRWF station integration is future work.
- Canary p95 latency is 1.198× production — within SLA, but should be monitored post-launch.
- CDS API key rotation is strongly advised (key was transiently present in git history before redaction).
- Render free tier cold-starts may cause initial request latency spikes (~30–60 s).

---

## 8. Flutter App

| Check | Status |
|---|---|
| Production URL → `forecast-bust-api.onrender.com` | ✅ |
| Stale `forecast-bust-ai.onrender.com` references removed | ✅ |
| No localhost/LAN URLs in production build | ✅ |

---

## 9. Scientific Boundary Statement

> "NWP models (ECMWF IFS / GFS) provide the weather forecast.
> The Forecast Bust AI adds a reliability layer: **P(Bust)** = probability the NWP forecast will be significantly wrong.
> Scientifically validated: **Days 1–7** against ERA5 reanalysis reference.
> Days 8–30: **UNVALIDATED_EXTENDED_RANGE** — provided for exploratory purposes only."
