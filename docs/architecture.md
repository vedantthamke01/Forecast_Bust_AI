# System Architecture

**Problem Statement**: SIH26079 — AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts  
**Organization**: Ministry of Earth Sciences (MoES) / NCMRWF  
**Budget Standard**: Strict ₹0 (100% Free, Open-Source, Publicly Accessible)

---

## 1. High-Level Architectural Flow

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   1. FREE & OPEN DATA INGESTION                        │
│   • Open-Meteo Global NWP Ensembles (ECMWF IFS / GFS) [Free]          │
│   • ERA5 Reanalysis Reference Dataset (Copernicus CDS Free Tier)       │
│   • NCMRWF / IMD Verified Indian Synoptic Observatories [Demo Archive] │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 2. DATA ENGINEERING & QUALITY CONTROL                  │
│   • python -m data_pipeline.download (India bounds, size check)        │
│   • python -m data_pipeline.update (Incremental missing data updater)  │
│   • python -m data_pipeline.quality (Thermodynamic bounds, missing %)  │
│   • Spatio-Temporal Aligner (Valid time T + N hours, nearest-neighbor) │
│   • Configurable Bust Labeler (Dynamic Lead Scaling, Percentile, Abs)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                3. MACHINE LEARNING & CALIBRATION ENGINE                │
│   • Strict Automated Anti-Leakage Gate (Excludes future actuals)       │
│   • Temporal Train/Val/Test Split (Train: 2023-24, Val: 2025, Test: 26)│
│   • Baseline: Calibrated Logistic Regression                           │
│   • Primary: Tuned LightGBM Gradient Boosted Trees                     │
│   • Probability Calibration: Isotonic Regression / Platt Scaling       │
│   • Explainability: TreeSHAP additive physical factor attributions     │
│   • Model Registry & Promotion Acceptance Gate                         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                4. FASTAPI REST BACKEND & DUAL DATABASE                 │
│   • Dual Engine: Async SQLite (Local quickstart) / PostgreSQL (Docker) │
│   • Endpoints: /health, /weather, /risk/location, /risk/map, /models   │
│   • Distribution Drift Detection (Kolmogorov-Smirnov 2-sample test)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
         ┌──────────────────────────┴──────────────────────────┐
         ▼                                                     ▼
┌──────────────────────────────────┐  ┌──────────────────────────────────┐
│ 5. WEB METEOROLOGICAL DASHBOARD  │  │ 6. FLUTTER MOBILE APPLICATION    │
│ • Leaflet OpenStreetMap GIS Map  │  │ • Riverpod State Management      │
│ • Interactive Horizon Slider     │  │ • flutter_map + OSM Tiles (₹0)   │
│ • Real-time SHAP Visualizer      │  │ • fl_chart 10-Day Horizon Curve  │
│ • Forecast vs Reference Table    │  │ • Material 3 Dark UI             │
│ • Admin ML Studio & Telemetry    │  │ • Offline Caching Support        │
└──────────────────────────────────┘  └──────────────────────────────────┘
```

---

## 2. Component Directory Layout

- `backend/app/`: FastAPI application, CORS, and endpoint routers.
- `data_pipeline/`: Downloader, incremental updater, alignment engine, quality checks, and labeling.
- `ml_pipeline/`: Feature engineering, leakage detector, training pipeline, calibration, and drift detector.
- `datasets/`: Versioned data (`raw`, `processed`, `training`, `metadata`).
- `models/`: Registered models (`model_v001`, `model_v002`) and catalog `registry.json`.
- `apps/admin_dashboard/`: Web Meteorological Dashboard and Admin ML Studio.
- `apps/flutter_app/`: Cross-platform Flutter mobile and desktop application.
- `tests/`: 17 automated tests covering backend, ML, leakage, and data pipeline.
