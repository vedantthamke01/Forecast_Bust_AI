# Roadmap & Future Work

**Project**: SIH26079 — AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts  
**Organization**: Ministry of Earth Sciences (MoES) / National Centre for Medium Range Weather Forecasting (NCMRWF)  

This roadmap outlines realistic, technically grounded next steps for transitioning the verified prototype into an operational institutional capability at NCMRWF.

---

## 1. Institutional Data Archive Integration

### 1.1 Authentic Days 8–10 Historical Training
- **Current State**: Historical training covers Days 1–7 (24h–168h) based on publicly accessible NWP archives. Operational inference supports Day 10 (240h).
- **Roadmap**: Connect to NCMRWF's internal MARS tape archive to extract archived NCUM global runs for lead times of 192h, 216h, and 240h across the past 10 years, eliminating the historical training boundary.

### 1.2 Direct Integration with Internal HPC Model Streams
- **Current State**: Operational inference uses open REST APIs (ECMWF IFS via Open-Meteo).
- **Roadmap**: Integrate directly with NCMRWF's high-performance computing (HPC) output queues, ingesting native GRIB2 / NetCDF4 model output files directly from the operational supercomputer cluster (Mihir / Pratyush).

---

## 2. Advanced Meteorological Feature Engineering

### 2.1 Raw 51-Member Ensemble Distribution Features
- **Current State**: The model consumes scalar ensemble spread ($\sigma$) and run revision deltas.
- **Roadmap**: Ingest raw 51-member ensemble grids from NCUM-EPS / ECMWF-EPS to compute higher-order distributional moments:
  - **Ensemble Kurtosis & Skewness**: Quantifying heavy-tailed or bimodal regime splits.
  - **Ensemble Clustering Distance**: Measuring divergence between dominant cluster centroids.

### 2.2 Upper-Air & Dynamic Instability Indices
- **Current State**: Uses surface parameters (2m temp, 10m wind, MSLP, 24h rain) and baroclinic anomalies.
- **Roadmap**: Ingest 3D isobaric levels to derive classical thermodynamic indices:
  - Convective Available Potential Energy (CAPE) and Convective Inhibition (CIN).
  - 850 hPa Relative Vorticity and Moisture Flux Convergence.
  - 500 hPa Geopotential Height Anomalies and Rossby Wave Breaking signatures.

### 2.3 Richer Static Geospatial Baselines
- **Current State**: Coordinates (latitude, longitude) and station elevation.
- **Roadmap**: Integrate high-resolution topographic slope, aspect, distance-to-coastline gradients, and satellite soil moisture (SMOS/SMAP) to improve localized orographic bust detection in the Western Ghats and Himalayan foothills.

---

## 3. Advanced Calibration & Uncertainty Quantification

### 3.1 Conformal Prediction Sets
- **Current State**: Isotonic regression probability calibration producing point probabilities $P(\text{Bust})$.
- **Roadmap**: Implement Split Conformal Prediction to provide mathematically guaranteed finite-sample coverage bands (e.g., guaranteed 90% confidence intervals for absolute forecast error).

### 3.2 Sub-Division Specific Climatological Calibration
- **Current State**: National-level calibration across 25 Indian synoptic stations.
- **Roadmap**: Segment calibration curves across IMD's 36 meteorological sub-divisions to account for distinct variance profiles between hyper-arid zones (West Rajasthan) and hyper-humid regimes (Konkan & Goa).

---

## 4. Operational Ingestion of Surface Sensor Networks

### 4.1 Ingestion of IMD Automatic Weather Stations (AWS)
- **Current State**: Historical and post-event verification uses Copernicus ERA5 reanalysis.
- **Roadmap**: Connect the post-event verification engine to IMD's real-time Global Telecommunication System (GTS) and AWS network (~800 surface stations, Doppler Weather Radars), enabling dual verification against both gridded reanalysis and in-situ rain gauges.

---

## 5. Human-in-the-Loop Forecaster Studio

### 5.1 Multi-Season Operational Shadow Trial
- Conduct a 12-month shadow trial alongside NCMRWF operational duty forecasters during the Southwest and Northeast Monsoon seasons.
- Implement structured feedback logging where meteorologists can flag false alarms or annotate localized mesoscale phenomena, feeding the automated retraining controller (`ml_pipeline/auto_retrain.py`).
