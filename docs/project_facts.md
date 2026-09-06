# SIH26079 Canonical Project Facts (Single Source of Truth)

**Problem ID**: SIH26079  
**Project Title**: AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts  
**Target Organization**: Ministry of Earth Sciences (MoES) / National Centre for Medium Range Weather Forecasting (NCMRWF)  
**Document Status**: Authoritative Source of Truth across all repository documentation, presentations, and submissions.  
**Validation Standard**: Scientific Correctness > Reproducibility > Defensibility > Clarity > Presentation Polish.

---

## 1. Project Identity & Positioning

- **Core Objective**: Provide an auxiliary forecast-reliability evaluation layer alongside operational Numerical Weather Prediction (NWP), estimating the calibrated probability that a medium-range forecast may experience a significant forecast error (forecast bust).
- **Fundamental Positioning**:
  - **What It Is**: An AI reliability layer evaluating forecast vulnerability to anomalous failure using forecast-time dynamical, spatial, and consistency indicators.
  - **What It Is NOT**:
    - Does NOT generate substitute meteorological forecasts.
    - Does NOT replace NWP dynamical models (NCUM, ECMWF IFS, GFS).
    - Does NOT replace statutory weather warnings or bulletins issued by IMD / NCMRWF.
    - Does NOT claim atmospheric outcome certainty.
    - Does NOT predict weather independently of NWP.
- **Intended Users**: Meteorological forecast analysts, forecast operations teams, researchers, disaster-management decision-support systems (NDMA/SDMA), and downstream weather-sensitive sectors requiring forecast reliability metrics.
- **Adoption Status**: Academic prototype developed for SIH26079. No claim of operational deployment or institutional adoption by IMD or NCMRWF.

---

## 2. Machine Learning Architecture & Models

- **Champion Model Version**: `model_real_v002`
- **Model Provenance**: `REAL` (`is_demo_model = false`, `DEMO_MODE = false`)
- **Algorithm**: Tuned LightGBM (Light Gradient Boosted Machine) Decision Trees
  - Why LightGBM: Captures non-linear feature interactions and threshold effects in tabular meteorological data; computationally efficient (~5 ms CPU inference); compatible with TreeSHAP exact attribution.
- **Probability Calibration**: Isotonic Regression (and Platt scaling fallback)
  - Purpose: Aligns raw tree leaf output scores with empirical event frequencies.
  - Meaning: Calibrated probability corresponds to observed bust frequencies across sufficiently large prediction groups; it is not an individual certainty guarantee.
- **Explainability**: TreeSHAP (Tree-based SHapley Additive exPlanations)
  - Meaning: Additive feature attribution measuring each feature's contribution to the ML model's prediction relative to a baseline expectation.
  - Constraint: Explains the *model prediction*, not physical atmospheric causality.
- **Target Variable**: `is_bust` ($\in \{0, 1\}$)
- **Production Feature Vector (17 features)**:
  1. `lead_hours`: Forecast horizon (24 to 240 hours)
  2. `latitude`: Synoptic station latitude (decimal degrees N)
  3. `longitude`: Synoptic station longitude (decimal degrees E)
  4. `forecast_temperature`: 2m air temperature (°C)
  5. `forecast_precipitation`: 24h accumulated precipitation (mm)
  6. `forecast_wind`: 10m wind speed (m/s)
  7. `forecast_pressure`: Mean sea level pressure (hPa)
  8. `forecast_humidity`: Surface relative humidity (%)
  9. `forecast_cloud_cover`: Total cloud cover fraction (%)
  10. `ensemble_spread`: NWP ensemble dispersion proxy ($\sigma$)
  11. `run_revision`: Forecast instability/consistency signal across consecutive runs
  12. `sin_day_of_year`: Seasonal solar phase ($\sin(2\pi \cdot \text{day} / 365.25)$)
  13. `cos_day_of_year`: Seasonal solar phase ($\cos(2\pi \cdot \text{day} / 365.25)$)
  14. `month`: Calendar month (1–12)
  15. `is_monsoon_season`: Binary flag for SW Monsoon window (June–September)
  16. `pressure_anomaly`: MSLP deviation from standard sea level (1013.25 hPa)
  17. `temp_dew_depression_proxy`: Atmospheric saturation proxy derived from RH and temperature

---

## 3. Dataset & Provenance

- **Champion Dataset**: `dataset_real_v002.csv`
- **Data Provenance**: `REAL` (100% authentic; non-synthetic)
- **Total Record Count**: 37,800 spatio-temporally aligned records
- **Geographic Scope**: 25 Indian synoptic observatories representing diverse climatological regimes (Western Ghats, Indo-Gangetic Plains, Deccan Plateau, Thar Desert, Himalayas, Eastern/Western Coasts; domain: 6°N–38°N, 68°E–98°E).
- **Historical Temporal Coverage**: 2024-07-10 00:00:00 to 2026-01-17 23:00:00
- **Data Role Separation**:
  1. **Historical Forecast Provider**: `open-meteo-previous-runs` (archived historical ECMWF IFS runs initialized at $T_0$).
  2. **Historical Reference Provider**: `era5-reanalysis` (Copernicus Climate Data Store / CDS; 0.25° European Reanalysis).
     - *Crucial Distinction*: ERA5 is a historical and post-event gridded reanalysis product. It is NOT real-time observational station data or instantaneous ground truth.
  3. **Live Operational Provider**: `open-meteo-operational` (Live ECMWF IFS global model at inference time $T_0$).
- **Overall Dataset Bust Rate**: 11.87% (4,488 busts / 37,800 records)

---

## 4. Horizon Coverage: Historical Training vs Operational Inference

| Capability | Days 3–7 (72h–168h) | Days 8–10 (192h–240h) |
| :--- | :---: | :---: |
| **Historical NWP Training Data** | **Yes** (37,800 records) | **No** (Public archive limitation) |
| **Model Development Coverage** | **Yes** | **No** |
| **Live Operational NWP Inference** | **Yes** (ECMWF IFS) | **Yes** (ECMWF IFS 10-day) |
| **Scientific Boundary** | Validated against the project's automated scientific, integration, end-to-end, and judge-demo verification suites | Legitimate archive limitation; data NOT fabricated |

*Scientific Policy Statement*: The system supports operational bust-risk estimation through Day 10, while the current public historical archive used for model development extends through Day 7. Historical training coverage for Days 8–10 requires access to a deeper institutional NWP archive (e.g., NCMRWF / ECMWF MARS tape archive).

---

## 5. Chronological Split & Evaluation Metrics

To prevent future-information leakage, data splitting is performed chronologically:
- **Training Set**: Initializations through 2025-08-05 23:00:00 (29,484 records)
- **Validation Set**: 2025-08-06 00:00:00 to 2025-08-07 23:00:00 (756 records)
- **Test Set**: 2026-01-15 00:00:00 to 2026-01-17 23:00:00 (7,560 records; test bust prevalence: 5.38%)

### Verified Test Set Performance

| Metric | Baseline (`model_real_v001`) | Production Champion (`model_real_v002`) | Improvement Delta |
| :--- | :---: | :---: | :---: |
| **PR-AUC (Precision-Recall AUC)** | `0.0950` | `0.2682` | **+0.1732** (2.82× baseline) |
| **ROC-AUC (Receiver Operating Characteristic)** | `0.8510` | `0.8756` | **+0.0246** |
| **Brier Calibration Score** | `0.0520` | `0.0450` | **-0.0070** (Better calibration) |
| **Expected Calibration Error (ECE)** | `0.0310` | `0.0257` | **-0.0053** (Tighter alignment) |
| **Accuracy** | `94.10%` | `94.62%` | **+0.52%** |
| **Test Sample Size** | 7,560 records | 7,560 records | Held-out future period |
| **Confusion Matrix ($TN / FP / FN / TP$)** | — | `7152 / 1 / 406 / 1` | Confusion Matrix (TN / FP / FN / TP) |

---

## 6. Bust Definition, Labeling Logic, and Severities

### Verification Lifecycle Chain
$$\text{Forecast Initialized at } T_0 \xrightarrow{\text{Lead } \tau} \text{Reference at } T_0 + \tau \xrightarrow{} \text{Absolute Error } |NWP - \text{Ref}| \xrightarrow{\text{Threshold}(\tau)} \text{Bust Label}$$

### Implemented Dynamic Lead-Scaling Formula
$$\text{Threshold}(\tau) = \text{Base\_Threshold} \times \left(1.0 + 0.12 \times \max\left(0, \frac{\tau - 24}{24}\right)\right)$$

### Applied Thresholds Across Horizons
| Lead Horizon ($\tau$) | Forecast Day | Precipitation | Temperature | Wind Speed |
| :---: | :---: | :---: | :---: | :---: |
| **24h** | Day 1 | 25.00 mm | 4.00°C | 8.50 m/s |
| **48h** | Day 2 | 28.00 mm | 4.48°C | 9.52 m/s |
| **72h** | Day 3 | 31.00 mm | 4.96°C | 10.54 m/s |
| **96h** | Day 4 | 34.00 mm | 5.44°C | 11.56 m/s |
| **120h** | Day 5 | 37.00 mm | 5.92°C | 12.58 m/s |
| **144h** | Day 6 | 40.00 mm | 6.40°C | 13.60 m/s |
| **168h** | Day 7 | 43.00 mm | 6.88°C | 14.62 m/s |

### Severity Ratio & Bands
$$\text{Ratio}_{\max} = \max\left(\frac{\text{Error}_{\text{precip}}}{\text{Threshold}_{\text{precip}}(\tau)}, \frac{\text{Error}_{\text{temp}}}{\text{Threshold}_{\text{temp}}(\tau)}, \frac{\text{Error}_{\text{wind}}}{\text{Threshold}_{\text{wind}}(\tau)}\right)$$
- **`NONE`**: $\text{is\_bust} = 0$ ($\text{Ratio}_{\max} < 1.0$)
- **`MODERATE`**: $\text{is\_bust} = 1$ and $1.0 \le \text{Ratio}_{\max} < 1.5$
- **`SEVERE`**: $\text{is\_bust} = 1$ and $1.5 \le \text{Ratio}_{\max} < 2.0$
- **`EXTREME`**: $\text{is\_bust} = 1$ and $\text{Ratio}_{\max} \ge 2.0$

*Compound Bust Rule*: Labeled as bust if $\text{Bust}_{\text{precip}} = 1$ OR ($\text{Bust}_{\text{temp}} = 1 \land \text{Bust}_{\text{wind}} = 1$).

---

## 7. Anti-Leakage Controls & Verification Decoupling

- **Temporal Decoupling**: At forecast initialization time $T_0$, future reference data and forecast errors do not exist.
- **Implemented Leakage Gate**: Automatically scans feature column vectors for 9 forbidden substrings: `actual`, `reference`, `observed`, `error`, `ground_truth`, `target`, `label`, `future`, `verification`.
- **Adversarial Verification**: 13 simulated future-leakage injection attacks were all successfully intercepted and rejected with `DataLeakageException` / `ValueError`.

---

## 8. Operational System & API Contracts

- **Server**: FastAPI REST service hosted on Uvicorn (`http://127.0.0.1:8000`)
- **Key Verified Endpoints**:
  - `GET /health`: Service health, configuration flags, model provenance, statutory disclaimer.
  - `GET /ready`: Readiness probe for orchestrators.
  - `GET /api/risk/location`: Calibrated bust probability, reliability score, risk level badge, and SHAP factor attribution for specific coordinates and lead horizons.
  - `GET /api/risk/map`: 25-station spatial grid of model-estimated bust risk across India under selected scenarios.
  - `GET /api/risk/history`: Verified historical forecast vs realized ERA5 reference records.
  - `GET /forecast/{id}/comparison`: Post-event historical verification detail; returns explicit HTTP 404 for nonexistent IDs.
  - `GET /api/weather/forecast`: Medium-range NWP guidance through Day 10.
  - `GET /api/models/evaluate`: Active model evaluation metrics (PR-AUC, ROC-AUC, Brier, ECE).
  - `GET /api/admin/drift/status`: Distribution drift monitor using Kolmogorov-Smirnov 2-sample testing.
- **Failure Semantics**:
  - Upstream provider unreachable: Explicit HTTP 503 (Service Unavailable) returned. Zero fabricated weather values; zero false ECMWF attribution.
  - Non-finite or out-of-range inputs: HTTP 422 rejected.
  - Input validation bounds: Precipitation [0, 2000 mm], Temperature [-100, 75°C], Wind [0, 150 m/s], Pressure [800, 1100 hPa], Spread [0, 50].

---

## 9. Measured System Performance

*Measured during project stress-test audit under local test environment:*
- **Prediction Latency**: 3–8 ms per inference
- **SHAP Computation**: 40–60 ms (TreeSHAP CPU)
- **Spatial Map Generation**: 60–80 ms (25 synoptic stations)
- **Throughput under Concurrency**: ~20 ms average response under 25 concurrent requests
- **Cold-Start Model Initialization**: ~1.2 seconds
