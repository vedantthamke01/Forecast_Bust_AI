# AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts

**Problem Statement ID**: SIH26079  
**Organization**: Ministry of Earth Sciences (MoES), Government of India  
**Department**: National Centre for Medium Range Weather Forecasting (NCMRWF)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 1. Executive Summary & Objective

Numerical Weather Prediction (NWP) models (e.g. NCMRWF NCUM, ECMWF IFS, NCEP GFS) provide operational weather forecasts across India and globally up to Day 10 (240 hours). However, atmospheric chaos, rapid mesoscale convection, orography, and parameterization uncertainties can trigger severe **forecast busts**—rare but catastrophic forecast failures where the error is extreme and high-consequence.

**This platform is NOT a replacement weather forecast model.**  
It is an **AI-powered forecast reliability and forecast-bust prediction layer** that sits directly on top of operational weather forecasts. Given an NWP forecast initialized at time $T$ for valid time $T + \tau$ ($\tau \in [24, 240]$ hours), it computes:
1. **Calibrated Bust Probability $P(\text{Bust} = 1 \mid X)$** (0% to 100%)
2. **Operational Reliability Score ($1 - P(\text{Bust})$)**
3. **Risk Category** (🟢 Low, 🟡 Moderate, 🟠 High, 🔴 Very High)
4. **SHAP Feature Attributions** (identifying physical and atmospheric drivers: ensemble spread, run-to-run jumpiness, baroclinic pressure gradients, regional historical errors)
5. **Spatial Risk Maps & Historical Verification Curves**

---

## 2. Scientific Disclaimer

> **IMPORTANT SCIENTIFIC NOTICE**:  
> *This system estimates the likelihood that a weather forecast may experience a significant forecast error. It does not replace operational numerical weather prediction, meteorological agencies, or official warnings issued by the India Meteorological Department (IMD) or National Centre for Medium Range Weather Forecasting (NCMRWF).*

---

## 3. Technology Stack

- **Backend**: Python 3.10+, FastAPI, Pydantic v2, SQLAlchemy (Async)
- **Database**: Dual Engine — PostgreSQL + PostGIS (Production/Docker) with automatic Async SQLite fallback for instant zero-dependency local development.
- **ML / AI Engine**: Scikit-Learn, LightGBM, Isotonic / Platt Probability Calibration, SHAP (TreeExplainer).
- **Data Engineering**: Automated pipeline with incremental updates, spatio-temporal alignment, multi-strategy bust labeling, and automated data leakage gate.
- **Web Meteorological Dashboard**: Responsive scientific dashboard with Leaflet GIS mapping, Chart.js / SVG visualizations, dynamic lead-time sliders, and Admin ML Studio.
- **Mobile Application**: Cross-platform Flutter / Dart application with Riverpod, Dio, GoRouter, fl_chart, flutter_map, and Material 3 design.

---

## 4. Quickstart Guide

### Option A: Local Quickstart (Zero External Dependencies)
```bash
# Clone the repository
git clone <repo-url>
cd SIH

# Run automated setup (creates .env, installs dependencies, seeds verified benchmark data)
./setup.sh        # On Linux/macOS
# OR on Windows PowerShell:
.\setup.ps1

# Start the FastAPI Backend & Web Meteorological Dashboard
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```
Open your browser at `http://localhost:8000` to interact with the meteorological dashboard and API documentation at `http://localhost:8000/docs`.

### Real NWP & ERA5 Training & Verification Pipeline
```bash
# 1. Ingest 37,800 genuine NWP forecast-reference pairs (Days 1–7)
python -m data_pipeline.prepare_real_v002

# 2. Chronologically train & calibrate production champion model (model_real_v002)
python -m ml_pipeline.train --dataset datasets/training/dataset_real_v002.csv --version model_real_v002 --dataset-version dataset_real_v002

# 3. Run independent 12-check pipeline integrity audit
python scripts/verify_real_pipeline.py

# 4. Run complete unit and integration test suite (24 tests)
python -m pytest
```

### Option B: Docker Compose
```bash
docker compose up --build
```

---

## 5. Repository Structure
```text
├── apps/
│   ├── admin_dashboard/         # Meteorological Web Dashboard & Admin ML Studio
│   └── flutter_app/             # Cross-Platform Flutter Mobile & Desktop App
├── backend/                     # FastAPI application, database models, services
├── data_pipeline/               # Downloader, incremental updater, alignment, QC, labeling
├── ml_pipeline/                 # Training, evaluation, calibration, auto-retraining
├── datasets/                    # Versioned datasets (raw, processed, training, metadata)
├── models/                      # Model registry (model_v001, model_v002...)
├── docs/                        # Scientific, architecture, and deployment documentation
├── tests/                       # Automated backend, data pipeline, and ML tests
└── Makefile                     # Developer CLI shortcuts
```
