# System Architecture & Technical Design

**Project**: SIH26079 — AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts  
**Organization**: Ministry of Earth Sciences (MoES) / National Centre for Medium Range Weather Forecasting (NCMRWF)  
**Budget Policy**: Strict ₹0 Operational Footprint (100% Free, Open-Source, and Publicly Auditable Stack)

---

## 1. High-Level System Architecture

The SIH26079 platform is structured into decoupled, modular tiers ensuring strict separation between offline scientific development, operational real-time inference, and post-event verification:

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. DATA SOURCES & INGESTION LAYER (₹0 OPEN ACCESS)                                      │
│                                                                                         │
│   ┌───────────────────────────┐  ┌───────────────────────────┐  ┌─────────────────────┐ │
│   │ Historical NWP Archive    │  │ ERA5 Reanalysis Reference │  │ Live ECMWF IFS NWP  │ │
│   │ (Open-Meteo Previous Runs)│  │ (Copernicus CDS Free Tier)│  │ (Operational API)   │ │
│   │ Days 1–7 (24h–168h)       │  │ Hourly 0.25° Gridded Ref  │  │ Days 3–10 (72–240h) │ │
│   └─────────────┬─────────────┘  └─────────────┬─────────────┘  └──────────┬──────────┘ │
└─────────────────┼──────────────────────────────┼───────────────────────────┼────────────┘
                  │                              │                           │
                  ▼                              ▼                           │
┌──────────────────────────────────────────────────────────────┐             │
│ 2. DATA ENGINEERING & VERIFICATION PIPELINE                  │             │
│                                                              │             │
│   • Spatial & Temporal Aligner (Valid Time Identity τ)       │             │
│   • Absolute Error Computer: |NWP - ERA5|                    │             │
│   • Dynamic Lead-Scaled Labeler: Threshold(τ)                │             │
│   • Quality Control & Thermodynamic Anomaly Filter           │             │
│   • 37,800 Labeled Indian Benchmark Pairs (`dataset_real_v002`)│             │
└──────────────────────────────┬───────────────────────────────┘             │
                               │                                             │
                               ▼                                             │
┌──────────────────────────────────────────────────────────────┐             │
│ 3. ML TRAINING, CALIBRATION & REGISTRY ENGINE                │             │
│                                                              │             │
│   • Chronological Data Split (Train ≤2025-08-05 | Test 2026) │             │
│   • Anti-Leakage Feature Gate (17 Clean Predictors)          │             │
│   • Tuned LightGBM Classifier (Binary Objective)             │             │
│   • Isotonic Probability Calibrator (PR-AUC 0.2682, BS 0.045)│             │
│   • TreeSHAP Explainability Explainer                        │             │
│   • Model Registry Catalog (`models/registry.json`)          │             │
└──────────────────────────────┬───────────────────────────────┘             │
                               │ Model Artifact (`model_real_v002`)          │
                               ▼                                             │
┌────────────────────────────────────────────────────────────────────────────┴────────────┐
│ 4. FASTAPI OPERATIONAL BACKEND SERVICE (PORT 8000)                                      │
│                                                                                         │
│   ┌────────────────────────┐  ┌────────────────────────┐  ┌────────────────────────┐   │
│   │ Live NWP Fetcher       │  │ Anti-Leakage Gate      │  │ Risk Inference Engine  │   │
│   │ (Open-Meteo / Fallback)│──► (9 Forbidden Patterns) │──► (Calibrated LightGBM)  │   │
│   └────────────────────────┘  └────────────────────────┘  └───────────┬────────────┘   │
│                                                                       │                │
│   ┌────────────────────────┐  ┌────────────────────────┐              │                │
│   │ REST API Endpoints     │  │ Distribution Drift     │              ▼                │
│   │ (/health, /risk, /map) │◄─│ Monitor (2-sample KS)  │◄── TreeSHAP Explainer         │
│   └────────────────────────┘  └────────────────────────┘                               │
└──────────────────────────────┬──────────────────────────────────────────────────────────┘
                               │
        ┌──────────────────────┴──────────────────────┐
        ▼                                             ▼
┌─────────────────────────────────────────┐ ┌─────────────────────────────────────────┐
│ 5. METEOROLOGICAL WEB DASHBOARD         │ │ 6. CROSS-PLATFORM FLUTTER APPLICATION   │
│ • Responsive Vanilla HTML5/CSS3/JS UI   │ │ • Flutter & Dart 3 Mobile / Desktop App │
│ • Leaflet 25-Station GIS Risk Map       │ │ • Riverpod Reactive State Architecture  │
│ • Step A–E Guided Judge Workflow        │ │ • Offline Caching & Sync Storage        │
│ • TreeSHAP Visual Decomposition Chart   │ │ • fl_chart Interactive 10-Day Curves    │
│ • Historical Verification Decoupled Tab │ │ • flutter_map + OSM Open Tiles (₹0)     │
└─────────────────────────────────────────┘ └─────────────────────────────────────────┘
```

---

## 2. Decoupled Data Flow & Lifecycles

### Flow A: Offline Training & Model Governance
1. **Raw NWP Ingestion**: Downloads historical NWP forecast runs across 25 stations for horizons 24h to 168h.
2. **ERA5 Alignment**: Ingests ERA5 gridded reanalysis for matching valid timestamps ($T_{\text{valid}} = T_0 + \tau$).
3. **Error Calculation & Labeling**: Computes $|NWP - ERA5|$ and tags records with `is_bust` using dynamic lead scaling.
4. **Leakage Audit**: Verifies feature matrix contains zero references, observations, or error metrics.
5. **Model Promotion**: Candidate model evaluated on chronological test set. If Brier score and PR-AUC beat baseline, candidate is promoted in `models/registry.json`.

### Flow B: Live Operational Runtime Inference ($T_0$)
```text
Client Request: GET /api/risk/location?lat=18.52&lon=73.86&lead_hours=96&variable=precipitation
       ↓
Input Bounds Sanitization (Lat/Lon/Lead/Physical ranges)
       ↓
Fetch Live ECMWF IFS Operational Guidance (if scenario not supplied)
       ↓
Extract 17 Forecast-Time Predictors (Coordinates, NWP state, solar phase, spread, revision)
       ↓
Automated Leakage Gate (Scans vector for 9 forbidden keywords)
       ↓
`model_real_v002` Execution + Isotonic Probability Calibration
       ↓
TreeSHAP Decomposition (Computes local Shapley values $\phi_i$)
       ↓
Format Natural-Language Summary & Assign Operational Risk Badge
       ↓
Return JSON Payload to Client (Mean Response: 3–8 ms)
```

### Flow C: Post-Event Historical Verification ($T_0 + \tau$)
```text
Client Request: GET /forecast/{id}/comparison
       ↓
Lookup Forecast Record in Verified Historical Archive (`dataset_real_v002.csv`)
       ↓
If Found: Return NWP Forecast, Realized ERA5 Reference, Absolute Error, Threshold, Outcome
If Not Found: Return HTTP 404 (Not Found). Strictly NO synthetic weather fabricated.
```

---

## 3. Subsystem Breakdown

### 1. Backend Service Layer (`backend/app/`)
- **Framework**: FastAPI with asynchronous endpoints on Python 3.10+.
- **Data Models**: Pydantic v2 schemas providing strict type validation, coordinate boundary filters, and NaN/Inf rejection.
- **Service Decoupling**:
  - `bust_service.py`: Encapsulates model inference, probability calibration, risk classification, and SHAP explanation generation.
  - `prediction.py`: Manages REST routes, query parameter parsing, and explicit HTTP error mapping.
  - `weather_service.py`: Coordinates live operational NWP fetching via Open-Meteo with 5-second timeout and 503 fallback semantics.

### 2. Machine Learning Engine (`ml_pipeline/`)
- **Feature Engineering (`features.py`)**: Assembles 17 physical and seasonal features. Enforces anti-leakage checking on every DataFrame prior to model ingestion.
- **Training Pipeline (`train.py`)**: Manages chronological train/val/test splits, LightGBM fitting, and isotonic calibration.
- **Explainability (`explainability.py`)**: Uses `shap.TreeExplainer` on decision paths, returning top 2 risk amplifiers and top 2 mitigators.
- **Auto-Retrain Controller (`auto_retrain.py`)**: Triggers batch evaluation and model promotion when newly verified data accumulates.
- **Drift Detector (`drift_detector.py`)**: Runs two-sample Kolmogorov-Smirnov statistical tests comparing operational feature distributions against training reference baselines.

### 3. Data Engineering Subsystem (`data_pipeline/`)
- **Downloader (`download.py`)**: Ingests raw data from Copernicus CDS and Open-Meteo archives.
- **Spatio-Temporal Aligner (`aligner.py`)**: Matches forecast initializations with valid-time ERA5 reanalysis across 25 Indian synoptic stations.
- **Bust Labeler (`labeler.py`)**: Implements dynamic lead-scaling thresholding and compound multi-variable bust determination.
- **Quality Assurance (`quality.py`)**: Audits thermodynamic limits, missing value ratios, and spatio-temporal coordinate integrity.

---

## 4. Error Handling & Degraded State Architecture

The system implements explicit fail-safe behavior:

```text
┌────────────────────────────┬────────────────────────────────────────────────────────┐
│ Scenario                   │ System Behavior & Response                             │
├────────────────────────────┼────────────────────────────────────────────────────────┤
│ Live NWP Provider Offline  │ Returns HTTP 503 (Service Unavailable) with clear      │
│                            │ error message. Never fabricates weather values.        │
├────────────────────────────┼────────────────────────────────────────────────────────┤
│ Non-Existent Record Lookup │ Returns HTTP 404 (Not Found). Never invents synthetic  │
│                            │ reference data or false verification outcomes.         │
├────────────────────────────┼────────────────────────────────────────────────────────┤
│ Out-of-Bounds Physical Val │ Returns HTTP 422 (Unprocessable Entity). Blocks values │
│                            │ outside conservative bounds (e.g. rain > 2000 mm).    │
├────────────────────────────┼────────────────────────────────────────────────────────┤
│ Future Information Injected│ Feature pipeline raises ValueError / DataLeakageException│
│                            │ blocking model inference immediately.                  │
└────────────────────────────┴────────────────────────────────────────────────────────┘
```

---

## 5. Security & Governance Design

- **Zero Hardcoded Secrets**: Secrets and API keys are strictly excluded from git tracking. `.env` and CDS credentials reside in local configuration files.
- **Path Traversal Protection**: Model and dataset loading routines sanitize file paths against directory traversal attacks.
- **Input Sanitization**: Query inputs are cast to strictly numeric types; non-finite (`NaN`, `Infinity`) values are rejected.
- **Model Registry Governance**: Production models are tracked in `models/registry.json` with artifact checksums, training dates, and uninflated evaluation metrics. Rollback to prior validated models is supported via `/api/models/rollback`.

---

## 6. Infrastructure Budget: Strict ₹0 Footprint

Every component was deliberately chosen to ensure 100% free open-source operation:
- **Compute**: Runs efficiently on standard commercial hardware (2–4 CPU cores, 4 GB RAM); zero GPU dependencies.
- **Tiles & Mapping**: OpenStreetMap raster tiles via Leaflet.js (ODbL open license).
- **Data APIs**: Free non-commercial tiers of Open-Meteo and Copernicus Climate Data Store.
- **Software Licenses**: MIT, BSD-3-Clause, and Apache-2.0 open-source components.
