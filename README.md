# AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts

**Smart India Hackathon 2024 / Problem Statement ID**: SIH26079  
**Organization**: Ministry of Earth Sciences (MoES), Government of India  
**Department**: National Centre for Medium Range Weather Forecasting (NCMRWF)  

> **One-Line Definition**: An AI-based forecast reliability layer that estimates the probability that a medium-range Numerical Weather Prediction (NWP) forecast will experience an anomalous, high-consequence forecast failure (forecast bust).

---

## 1. Problem Statement & Motivation

Modern Numerical Weather Prediction (NWP) systems—such as NCMRWF's NCUM, ECMWF's IFS, and NCEP's GFS—provide the statutory foundation for medium-range weather forecasting across India. However, atmospheric dynamics are non-linear and chaotic. Small initialization discrepancies, complex topography (such as the Western Ghats and Himalayan ranges), and parameterization uncertainties can occasionally cause an NWP forecast to "bust"—failing significantly despite appearing standard in deterministic outputs.

```text
NWP Model Initialization (T₀)
            ↓
Expected Atmospheric State (Rainfall, Temp, Wind, Pressure)
            ↓
Forecast Reliability Varies by Synoptic Regime & Horizon
            ↓
Vulnerability to Anomalous Failure (Forecast Bust)
            ↓
Critical Need: Operational Probability of Forecast Bust P(Bust)
```

### Core Distinction: Weather Forecasting vs. Forecast Reliability Layer

| Dimension | Upstream NWP Models | SIH26079 Forecast Reliability Layer |
| :--- | :--- | :--- |
| **Primary Output** | Physical weather state (mm of rain, °C temperature, m/s wind) | Calibrated probability of forecast failure $P(\text{Bust} = 1)$ |
| **Underlying Mechanism** | Forward dynamical numerical integration (Navier-Stokes, thermodynamics) | Machine learning feature evaluation on forecast consistency and dynamics |
| **Operational Role** | The primary forecast guidance | An auxiliary confidence and risk layer evaluating forecast stability |
| **Target Question** | *"What will the weather be at Day 4?"* | *"How likely is the Day 4 forecast to suffer a major failure?"* |

---

## 2. What This System Does

1. **Ingests Operational Forecasts at $T_0$**: Ingests multi-parameter medium-range NWP guidance (precipitation, temperature, wind, pressure, humidity, cloud cover, ensemble dispersion).
2. **Extracts Forecast-Time Features**: Derives synoptic proxies, baroclinic pressure anomalies, seasonal solar positions, and run revision signals strictly from data available at initialization time $T_0$.
3. **Applies Anti-Leakage Gating**: The implemented leakage gate and temporal validation tests are designed to prevent future reference/error information from entering T0 inference. All implemented leakage checks and adversarial leakage tests passed.
4. **Estimates Calibrated Bust Probability**: Uses a LightGBM model calibrated with Isotonic Regression to predict $P(\text{Bust} \in [0, 1])$.
5. **Assigns Standardized Risk Badges**: Maps probabilities to four operational tiers: 🟢 LOW ($<25\%$), 🟡 MODERATE ($25\text{–}50\%$), 🟠 HIGH ($50\text{–}75\%$), and 🔴 VERY HIGH ($\ge 75\%$).
6. **Explains Local Decision via TreeSHAP**: Decomposes the prediction into additive feature attributions, isolating the top model amplifiers and mitigators.
7. **Renders Spatial Risk Contours**: Visualizes estimated forecast-bust risk across a 25-station synoptic grid covering India.
8. **Decoupled Historical Verification**: Retains historical forecasts and later ingests realized reference data (Copernicus ERA5 reanalysis) to compute absolute error $|NWP - ERA5|$ and verify forecast outcomes.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                    OPERATIONAL INFERENCE LIFECYCLE (T₀)                     │
└─────────────────────────────────────────────────────────────────────────────┘
  Operational NWP Forecast (ECMWF IFS)
                 ↓
  Forecast-Time Feature Extraction (17 Predictors)
                 ↓
  Strict Anti-Leakage Gate (Blocks future information)
                 ↓
  Champion ML Model (`model_real_v002` + Isotonic Calibration)
                 ↓
  Calibrated Bust Probability P(Bust) & Reliability Index
                 ↓
  TreeSHAP Local Model Feature Attribution (Amplifiers / Mitigators)
                 ↓
  Interactive Dashboard & Spatial GIS Risk Grid (25 Synoptic Stations)

┌─────────────────────────────────────────────────────────────────────────────┐
│                 POST-EVENT HISTORICAL VERIFICATION (T₀ + τ)                 │
└─────────────────────────────────────────────────────────────────────────────┘
  Valid Time T₀ + τ Arrives
                 ↓
  Reference Data Ingestion (Copernicus ERA5 Reanalysis)
                 ↓
  Absolute Error Calculation: |NWP - ERA5|
                 ↓
  Lead-Scaled Dynamic Thresholding: Threshold(τ)
                 ↓
  Empirical Bust Verification & Telemetry Log
```

---

## 3. What This System Does NOT Do

To preserve scientific rigor and institutional defensibility, this platform adheres to strict operational boundaries:

- **Does NOT generate substitute weather forecasts**: It does not predict future rainfall amounts or temperatures independently of NWP.
- **Does NOT replace dynamical NWP models**: It requires NWP model initializations to function and operates as an auxiliary reliability layer.
- **Does NOT replace statutory advisories**: Official meteorological alerts, warnings, and bulletins are issued exclusively by the India Meteorological Department (IMD) and NCMRWF.
- **Does NOT claim physical outcome certainty**: An individual probability is a model estimate; it is not physical proof of atmospheric stability.
- **Does NOT use future reference data for $T_0$ predictions**: Future reference observations and error terms are isolated until valid time $T_0 + \tau$.
- **Does NOT claim historical training coverage for Days 8–10**: Historical training covers Days 1–7 (24h–168h); operational inference supports Days 3–10 (72h–240h).
- **Does NOT claim operational deployment**: Developed as an advanced scientific prototype for SIH26079.

---

## 4. End-to-End System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. HISTORICAL TRAINING & VERIFICATION PIPELINE                                          │
│                                                                                         │
│   Historical NWP Runs (Days 1–7)          ERA5 Reanalysis Reference                     │
│   (open-meteo-previous-runs)              (Copernicus CDS Free Archive)                 │
│              │                                          │                               │
│              └───────────────────┬──────────────────────┘                               │
│                                  ▼                                                      │
│                     Spatio-Temporal Aligner (37,800 pairs)                              │
│                                  │                                                      │
│                                  ▼                                                      │
│                     Absolute Error Calculation                                          │
│                     |NWP_precip - ERA5_precip|                                          │
│                                  │                                                      │
│                                  ▼                                                      │
│                     Lead-Scaled Dynamic Bust Labeler                                    │
│                     Threshold(τ) = Base · [1 + 0.12 · (τ - 24)/24]                      │
│                                  │                                                      │
│                                  ▼                                                      │
│                     Anti-Leakage Feature Pipeline (17 Features)                         │
│                                  │                                                      │
│                                  ▼                                                      │
│                     Chronological Data Split                                            │
│                     Train: ≤2025-08-05 | Val: 08-06..07 | Test: 2026-01-15..17          │
│                                  │                                                      │
│                                  ▼                                                      │
│                     LightGBM Classifier + Isotonic Calibration                          │
│                     PR-AUC: 0.2682 | ROC-AUC: 0.8756 | Brier: 0.0450                    │
│                                  │                                                      │
│                                  ▼                                                      │
│                     Model Registry (`model_real_v002`)                                  │
└──────────────────────────────────┬──────────────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────┴──────────────────────────────────────────────────────┐
│ 2. PRODUCTION RUNTIME & INFERENCE ENGINE                                                │
│                                                                                         │
│   Live ECMWF IFS Forecast (T₀) ────────► Forecast-Time Feature Extraction               │
│                                                     │                                   │
│                                                     ▼                                   │
│                                          Anti-Leakage Gating Check                      │
│                                                     │                                   │
│                                                     ▼                                   │
│                                          Calibrated LightGBM Model                      │
│                                                     │                                   │
│                                                     ▼                                   │
│                                          Calibrated P(Bust) & Reliability               │
│                                                     │                                   │
│                                                     ▼                                   │
│                                          TreeSHAP Factor Attribution                    │
│                                                     │                                   │
│                                                     ▼                                   │
│                                          FastAPI REST Service (Port 8000)               │
└──────────────────────────────────┬──────────────────────────────────────────────────────┘
                                   │
        ┌──────────────────────────┴──────────────────────────┐
        ▼                                                     ▼
┌──────────────────────────────────────┐    ┌──────────────────────────────────────┐
│ 3. METEOROLOGICAL WEB DASHBOARD      │    │ 4. FLUTTER CROSS-PLATFORM CLIENT     │
│ • Step A–E Guided Judge Workflow     │    │ • Material 3 Dark Architecture       │
│ • Leaflet 25-Station GIS Risk Map    │    │ • Riverpod Reactive State Management │
│ • Interactive 10-Day Horizon Curve   │    │ • Offline Caching & Sync             │
│ • TreeSHAP Visual Factor Decomposition│   │ • Cross-Platform (Mobile & Desktop)  │
│ • Historical Verification Studio     │    │ • fl_chart 10-Day Trajectory         │
└──────────────────────────────────────┘    └──────────────────────────────────────┘
```

---

## 5. Data Sources, Provenance, and Taxonomy

The system strictly distinguishes between three operational data roles:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                METEOROLOGICAL DATA TAXONOMY                            │
├──────────────────────┬─────────────────────────────────────────────────────────────────┤
│ Role                 │ Definition, Source & Access Mechanism                           │
├──────────────────────┼─────────────────────────────────────────────────────────────────┤
│ 1. Historical        │ Archived numerical forecast runs initialized at T₀ for valid    │
│    Forecasts         │ time T₀ + τ. Ingested from Open-Meteo Previous Runs archive     │
│                      │ (ECMWF IFS / GFS seamless runs). Covers Days 1–7 (24h–168h).    │
├──────────────────────┼─────────────────────────────────────────────────────────────────┤
│ 2. Historical        │ Copernicus ERA5 global atmospheric reanalysis (0.25° grid).     │
│    Reference         │ Ingested via Copernicus Climate Data Store (CDS API).           │
│    (ERA5)            │ Used as post-event reference to calculate forecast error.       │
│                      │ NOTE: ERA5 is a reanalysis product, NOT a real-time observation.│
├──────────────────────┼─────────────────────────────────────────────────────────────────┤
│ 3. Operational Live  │ Live ECMWF IFS global forecast guidance ingested at runtime     │
│    Forecast          │ initialization T₀. Supports medium-range horizons Days 3–10.    │
└──────────────────────┴─────────────────────────────────────────────────────────────────┘
```

---

## 6. Historical vs. Operational Horizon Boundaries

A central tenet of this system is **scientific transparency regarding forecast horizons**:

| System Capability | Days 3–7 (72h–168h) | Days 8–10 (192h–240h) |
| :--- | :---: | :---: |
| **Historical NWP Archive Training Data** | **Available & Validated** (37,800 pairs) | **Unavailable in Public Free Archive** |
| **Model Development & Offline Benchmark** | **Covered** (`model_real_v002`) | **Not Covered in Historical Training** |
| **Live Operational NWP Inference** | **Supported** (ECMWF IFS) | **Supported** (ECMWF IFS 10-day) |
| **Scientific Boundary Documentation** | Full empirical verification | Honest boundary; Days 8–10 data not fabricated |

> **Operational Horizon Policy**: The system supports operational bust-risk estimation through Day 10, while the current public historical archive used for model development extends through Day 7. Historical training coverage for Days 8–10 requires access to a deeper institutional NWP archive (e.g., NCMRWF / ECMWF MARS tape archive).

---

## 7. Forecast Bust Definition & Labeling Strategy

A forecast bust is defined as an event where the absolute forecast error between the NWP prediction and the matching valid-time reference exceeds an operational threshold.

### 1. Lead-Dependent Threshold Scaling Formula
Because forecast uncertainty naturally increases with lead horizon $\tau \in [24, 240]$ hours, project thresholds scale above Day 1 (24 hours):

$$\text{Threshold}(\tau) = \text{Base\_Threshold} \times \left(1.0 + 0.12 \times \max\left(0, \frac{\tau - 24}{24}\right)\right)$$

### 2. Operational Thresholds Across Horizons
| Lead Horizon ($\tau$) | Forecast Day | Precipitation Threshold | Temperature Threshold | Wind Speed Threshold |
| :---: | :---: | :---: | :---: | :---: |
| **24h** | Day 1 | 25.00 mm | 4.00°C | 8.50 m/s |
| **48h** | Day 2 | 28.00 mm | 4.48°C | 9.52 m/s |
| **72h** | Day 3 | 31.00 mm | 4.96°C | 10.54 m/s |
| **96h** | Day 4 | 34.00 mm | 5.44°C | 11.56 m/s |
| **120h** | Day 5 | 37.00 mm | 5.92°C | 12.58 m/s |
| **144h** | Day 6 | 40.00 mm | 6.40°C | 13.60 m/s |
| **168h** | Day 7 | 43.00 mm | 6.88°C | 14.62 m/s |

*Note: These thresholds represent the project's empirical labeling methodology and are not universal physical constants.*

### 3. Severity Classification
Severity is determined by the maximum error-to-threshold ratio:
$$\text{Ratio}_{\max} = \max\left(\frac{|P_{\text{nwp}} - P_{\text{era5}}|}{\text{Threshold}_{\text{precip}}(\tau)}, \frac{|T_{\text{nwp}} - T_{\text{era5}}|}{\text{Threshold}_{\text{temp}}(\tau)}, \frac{|W_{\text{nwp}} - W_{\text{era5}}|}{\text{Threshold}_{\text{wind}}(\tau)}\right)$$
- **`NONE`**: $\text{is\_bust} = 0$ ($\text{Ratio}_{\max} < 1.0$)
- **`MODERATE`**: $\text{is\_bust} = 1$ ($1.0 \le \text{Ratio}_{\max} < 1.5$)
- **`SEVERE`**: $\text{is\_bust} = 1$ ($1.5 \le \text{Ratio}_{\max} < 2.0$)
- **`EXTREME`**: $\text{is\_bust} = 1$ ($\text{Ratio}_{\max} \ge 2.0$)

---

## 8. Feature Engineering & Strict Anti-Leakage Gating

### Production Feature Set (17 Predictor Features)
Every prediction uses strictly the following 17 feature columns available at initialization time $T_0$:
- **Horizon & Coordinates (3)**: `lead_hours`, `latitude`, `longitude`
- **NWP Forecast Guidance (6)**: `forecast_temperature`, `forecast_precipitation`, `forecast_wind`, `forecast_pressure`, `forecast_humidity`, `forecast_cloud_cover`
- **Dynamical & Dispersion Proxies (3)**: `ensemble_spread`, `run_revision`, `pressure_anomaly`
- **Climatological & Seasonal Proxies (5)**: `sin_day_of_year`, `cos_day_of_year`, `month`, `is_monsoon_season`, `temp_dew_depression_proxy`

### Anti-Leakage Safeguard
The automated leakage scanner inspects every input feature vector against 9 forbidden patterns:
```python
FORBIDDEN_LEAKAGE_SUBSTRINGS = [
    "actual", "reference", "observed", "error", 
    "ground_truth", "target", "label", "future", "verification"
]
```
If any column contains a forbidden substring, feature extraction aborts with a `ValueError` / `DataLeakageException`. All 13 simulated adversarial leakage injection tests were intercepted by the gate.

---

## 9. Machine Learning, Calibration, and Explainability

### LightGBM Model Architecture
- **Algorithm**: LightGBM Gradient Boosted Decision Trees (`objective="binary"`, `metric="binary_logloss"`, `learning_rate=0.03`, `num_leaves=31`, `n_estimators=150`).
- **Target Variable**: `is_bust` ($\in \{0, 1\}$).
- **Class Balance**: Evaluated with precision-recall optimization to handle rare bust events (11.87% historical prevalence).

### Probability Calibration
Raw tree leaf logits are mapped to calibrated probabilities via Isotonic Regression:
$$\hat{p} = \text{Calibrator}(f_{\text{raw}}(x))$$
A calibrated probability is intended to correspond to observed event frequency over sufficiently large groups of predictions with similar predicted probabilities.

### TreeSHAP Factor Attribution
Local explainability is generated via TreeSHAP, computing game-theoretic additive feature attributions:
$$f(x) = \phi_0 + \sum_{i=1}^{M} \phi_i(x)$$
- Features with $\phi_i > 0$ are classified as **Amplifiers** (factors increasing estimated bust risk).
- Features with $\phi_i < 0$ are classified as **Mitigators** (factors reducing estimated bust risk).
- *Scientific Clarification*: TreeSHAP explains the *model prediction*, not the physical atmosphere itself.

---

## 10. Verified Evaluation Metrics

All metrics were evaluated on the chronologically isolated test partition (2026-01-15 to 2026-01-17; 7,560 records; test bust prevalence: 5.38%):

| Metric | Baseline (`model_real_v001`) | Production Champion (`model_real_v002`) | Improvement Delta |
| :--- | :---: | :---: | :---: |
| **PR-AUC (Precision-Recall)** | `0.0950` | `0.2682` | **+0.1732** (2.82× baseline) |
| **ROC-AUC (Discriminative)** | `0.8510` | `0.8756` | **+0.0246** |
| **Brier Calibration Score** | `0.0520` | `0.0450` | **-0.0070** (Better calibration) |
| **Expected Calibration Error (ECE)**| `0.0310` | `0.0257` | **-0.0053** (Tighter alignment) |
| **Accuracy** | `94.10%` | `94.62%` | **+0.52%** |
| **Test Records** | 7,560 | 7,560 | Held-out future split |
| **Confusion Matrix ($TN / FP / FN / TP$)**| — | `7152 / 1 / 406 / 1` | Confusion Matrix (TN / FP / FN / TP) |

---

## 11. Chronological Train / Validation / Test Splitting

To eliminate future-information leakage across time, temporal splitting is enforced:
- **Training Period**: Inceptions through 2025-08-05 23:00:00 (29,484 records)
- **Validation Period**: 2025-08-06 00:00:00 to 2025-08-07 23:00:00 (756 records)
- **Test Period**: 2026-01-15 00:00:00 to 2026-01-17 23:00:00 (7,560 records)

```text
[----------------- TRAINING: 29,484 records -----------------] [VAL: 756] ... [TEST: 7,560]
2024-07-10                                       2025-08-05   2025-08-07      2026-01-15..17
```

---

## 12. Interactive Meteorological Web Dashboard

The web dashboard implements a 5-step judge workflow:

```text
[STEP A] Choose Target Synoptic Observatory (e.g. Pune, 18.52°N, 73.86°E)
   ↓
[STEP B] Select Forecast Horizon (Day 3 through Day 10 buttons)
   ↓
[STEP C] Select Meteorological Variable (Precipitation, Temperature, Wind, Pressure)
   ↓
[STEP D] Inspect Operational NWP Guidance (ECMWF IFS guidance fetched live at T₀)
   ↓
[STEP E] Review AI Forecast Bust Risk, Reliability Score, and TreeSHAP Decomposition
   ↓
[SPATIAL MAP] Inspect Spatial Risk Map across 25 Indian Synoptic Observatories
   ↓
[VERIFICATION] Audit Decoupled Historical Forecast vs ERA5 Reference Outcome
```

---

## 13. REST API Reference

The backend exposes FastAPI endpoints on port 8000:

| Method | Route | Description | Expected Status Codes |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Service health, configuration flags, model provenance, statutory disclaimer | `200` |
| `GET` | `/ready` | Container readiness probe (DB connection, model loaded) | `200` |
| `GET` | `/api/risk/location` | Predicts calibrated bust probability, reliability, risk badge, and SHAP factors | `200`, `422`, `503` |
| `GET` | `/api/risk/map` | Computes 25-station spatial risk grid across India under selected scenario | `200`, `422` |
| `GET` | `/api/risk/history` | Fetches verified historical forecast vs realized ERA5 reference records | `200` |
| `GET` | `/forecast/{id}/comparison` | Returns post-event verification record; strictly returns 404 for nonexistent IDs | `200`, `404` |
| `GET` | `/api/weather/forecast` | Returns live medium-range NWP guidance through Day 10 | `200`, `503` |
| `GET` | `/api/models/current` | Active champion model metadata, feature list, and training dates | `200` |
| `GET` | `/api/models/evaluate` | Diagnostic evaluation metrics (PR-AUC, ROC-AUC, Brier, ECE) | `200` |
| `GET` | `/api/admin/drift/status` | Kolmogorov-Smirnov distribution drift diagnostics | `200` |

### Sample Response: `GET /api/risk/location`
```json
{
  "location": { "latitude": 18.5204, "longitude": 73.8567 },
  "forecast_horizon_hours": 96,
  "forecast_day": 4,
  "variable": "precipitation",
  "forecast_value": 0.0,
  "bust_probability": 0.001,
  "bust_probability_percentage": 0.1,
  "reliability_score": 0.999,
  "reliability_percentage": 99.9,
  "risk_level": "LOW",
  "risk_badge": "🟢 LOW",
  "model_version": "model_real_v002",
  "dataset_version": "dataset_real_v002",
  "data_type": "REAL",
  "is_demo_model": false,
  "forecast_source": "ECMWF IFS (Operational NWP)",
  "reference_source": "era5-reanalysis",
  "explanation": {
    "top_amplifiers": [
      { "description": "Climatological Solar Position", "shap_value": 0.045, "impact": "AMPLIFIER" }
    ],
    "top_mitigators": [
      { "description": "Forecasted 10m Wind Speed (8.9 m/s)", "shap_value": -0.21, "impact": "MITIGATOR" }
    ],
    "summary_text": "Overall bust risk is LOW (0.1%). The forecast is currently assessed as highly reliable."
  },
  "disclaimer": "This system provides forecast reliability estimation and does not replace official NWP or meteorological advisories."
}
```

---

## 14. Error Handling & Provider Failure Behavior

In accordance with strict scientific integrity, the project never fabricates meteorological values when an external provider fails:
- **Upstream Provider Available**: Live ECMWF IFS forecast returned $\to$ feature extraction $\to$ calibrated inference.
- **Upstream Provider Unavailable / Timeout**: The API returns an explicit `HTTP 503 (Service Unavailable)` with a diagnostic message. It **never** invents synthetic weather values and **never** falsely attributes fallback data to ECMWF.
- **Non-Existent Comparison IDs**: The endpoint `/forecast/{id}/comparison` returns an explicit `HTTP 404 (Not Found)`. It never generates fake reference data or false verification outcomes.
- **Physical Boundary Violations**: Out-of-bounds or non-finite inputs return `HTTP 422 (Unprocessable Entity)`:
  - Precipitation: $[0, 2000\text{ mm}]$
  - Temperature: $[-100, 75^{\circ}\text{C}]$
  - Wind Speed: $[0, 150\text{ m/s}]$
  - Pressure: $[800, 1100\text{ hPa}]$
  - Ensemble Spread: $[0, 50]$

---

## 15. Security and Data Protection

The repository enforces essential security controls:
- Zero committed secrets or credentials; `.env` and local credentials are strictly ignored in `.gitignore`.
- Explicit path traversal protections in model loading and dataset export utilities.
- Input bounds sanitization rejecting non-finite (`NaN`, `Inf`) inputs.
- Read-only historical verification lookups preventing SQL/query injection.

---

## 16. Measured Performance Benchmarks

*Measured during project stress testing under the documented local test environment:*
- **Prediction Latency**: 3–8 ms per inference (CPU LightGBM bundle)
- **SHAP Computation**: 40–60 ms (TreeSHAP CPU)
- **Spatial Map Generation**: 60–80 ms (25 synoptic stations)
- **Throughput under Concurrency**: ~20 ms average response under 25 concurrent requests
- **Cold-Start Model Initialization**: ~1.2 seconds

---

## 17. Setup & Installation Guide

### Prerequisites
- Python 3.10, 3.11, or 3.12
- Git
- Modern web browser (Chrome, Firefox, Edge)

### 1. Clone the Repository
```bash
git clone https://github.com/beastboy069/SIH.git
cd SIH
```

### 2. Set Up Virtual Environment & Dependencies
```bash
# Windows PowerShell:
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Linux / macOS:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Copernicus CDS API (Optional for Historical Downloading)
Create `~/.cdsapirc` with your free credentials:
```text
url: https://cds.climate.copernicus.eu/api
key: <YOUR-PERSONAL-CDS-API-KEY>
```

### 4. Run Automated Test Suites
```bash
# Run 49 automated pytest tests:
python -m pytest -q

# Run 12-point scientific integrity audit:
python scripts/verify_real_pipeline.py

# Run live end-to-end operational tests:
python scripts/e2e_demo_test.py

# Run 12-step judge demonstration workflow:
python scripts/verify_judge_demo.py
```

---

## 18. Running the Application

### Start the Backend Server
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### Access URLs
- **Web Meteorological Dashboard**: [http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/)
- **Interactive Swagger REST API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Endpoint**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Readiness Probe**: [http://127.0.0.1:8000/ready](http://127.0.0.1:8000/ready)

---

## 19. Reproducing the Real Dataset and Model

To reproduce the authentic pipeline from scratch:
```bash
# 1. Download & align historical NWP and ERA5 records across 25 stations
python -m data_pipeline.prepare_real_v002

# 2. Train and calibrate champion model model_real_v002
python -m ml_pipeline.train --dataset datasets/training/dataset_real_v002.csv --version model_real_v002 --dataset-version dataset_real_v002

# 3. Verify that model registry matches reported metrics
python scripts/verify_real_pipeline.py
```

---

## 20. Known Scientific Limitations & Future Work

1. **Historical Training Horizon (168h / Day 7)**: Historical NWP model runs for Days 8–10 were not available in public free archives. Live operational inference supports Days 3–10. Expanding training to Days 8–10 requires access to institutional MARS tape archives.
2. **ERA5 Reanalysis Reference**: ERA5 is a gridded numerical reanalysis product (0.25° resolution). It can smooth localized orographic cloudbursts compared to direct surface rain gauges.
3. **Probabilistic Nature**: Model outputs are calibrated likelihood estimates, not physical guarantees.
4. **Geographic Coverage**: Calibrated across 25 representative synoptic stations in the Indian domain. Generalization to remote microclimates requires additional local sensor data.
5. **Operational Integration**: Full operational deployment at NCMRWF would require integration with internal HPC job dispatchers and real-time radar data assimilation feeds.
