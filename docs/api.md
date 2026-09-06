# REST API Reference Documentation

**Base URL**: `http://localhost:8000`  
**Interactive Swagger UI**: `http://localhost:8000/docs`  
**Alternative ReDoc**: `http://localhost:8000/redoc`

---

## 1. System Health & Probes

### `GET /health`
Returns service operational health and the statutory scientific disclaimer.
```json
{
  "status": "healthy",
  "service": "forecast-bust-detection",
  "organization": "NCMRWF / MoES",
  "environment": "development",
  "demo_mode": true,
  "scientific_disclaimer": "This system provides forecast reliability estimation and does not replace official NWP or meteorological advisories."
}
```

### `GET /ready`
Readiness probe for container orchestrators.
```json
{
  "status": "ready",
  "database": "connected",
  "model_loaded": true
}
```

---

## 2. Weather & Locations

### `GET /api/locations/search?q={query}`
Forward geocoding search for Indian cities, districts, and observatories.
- Query parameters: `q` (string, required)

### `GET /api/locations/reverse?lat={lat}&lon={lon}`
Reverse geocoding to nearest synoptic station.

### `GET /api/weather/current?lat={lat}&lon={lon}`
Returns active surface parameters (temperature, precipitation, wind, pressure, humidity).

### `GET /api/weather/forecast?lat={lat}&lon={lon}&days=10`
Returns medium-range Numerical Weather Prediction forecast series up to Day 10 (240 hours).

---

## 3. Forecast Bust Risk & Explainability

### `GET /api/risk/location?lat={lat}&lon={lon}&lead_hours={lead_hours}&variable={variable}`
Calculates calibrated bust probability, reliability index, risk badge, and SHAP feature attributions.

**Example Response**:
```json
{
  "location": { "latitude": 18.5204, "longitude": 73.8567 },
  "forecast_horizon_hours": 96,
  "forecast_day": 4,
  "variable": "precipitation",
  "forecast_value": 42.0,
  "bust_probability": 0.78,
  "bust_probability_percentage": 78.0,
  "reliability_score": 0.22,
  "reliability_percentage": 22.0,
  "risk_level": "HIGH",
  "risk_badge": "🟠 HIGH",
  "model_version": "model_v001",
  "explanation": {
    "top_amplifiers": [
      { "description": "Extended Forecast Horizon (Day 4)", "shap_value": 0.32, "impact": "AMPLIFIER" },
      { "description": "NWP Ensemble Spread (3.80σ)", "shap_value": 0.28, "impact": "AMPLIFIER" }
    ],
    "top_mitigators": [
      { "description": "Mean Sea Level Pressure within standard bounds", "shap_value": -0.09, "impact": "MITIGATOR" }
    ],
    "summary_text": "Elevated bust risk primarily driven by Extended Forecast Horizon (Day 4) and NWP Ensemble Spread."
  }
}
```

### `GET /api/risk/map?lead_hours={lead_hours}&variable={variable}`
Returns spatial grid of bust risk and reliability for map visualization across India.

### `GET /api/risk/history?lat={lat}&lon={lon}&limit=10`
Returns verified historical forecast vs realized reference records with error deltas.

---

## 4. Model Registry & Quality

### `GET /api/models/current`
Returns active production model metadata, feature lists, and calibration metrics.

### `GET /api/models/evaluate`
Returns diagnostic metrics (PR-AUC, ROC-AUC, Brier score, Expected Calibration Error).

### `POST /api/models/rollback`
Rolls back production model to a target previous validated version.

### `GET /api/datasets/status`
Returns dataset version, record count, coverage, and update status.

### `GET /api/datasets/quality`
Returns the automated data quality report card (missing %, duplicate count, coordinate bounds, thermodynamic anomalies).

---

## 5. Administrative Automation

### `POST /api/admin/dataset/update`
Triggers background incremental dataset update.

### `POST /api/admin/train`
Submits candidate model retraining job to execution queue.

### `GET /api/admin/drift/status`
Calculates feature distribution drift using Kolmogorov-Smirnov test.
