# REST API Reference Documentation

**Base URL**: `http://127.0.0.1:8000`  
**Interactive Swagger UI**: `http://127.0.0.1:8000/docs`  
**Alternative ReDoc**: `http://127.0.0.1:8000/redoc`

All endpoints follow standard REST principles, return JSON payloads, and provide explicit HTTP status codes.

---

## 1. System Health & Probes

### `GET /health`
Returns operational service health, application fallback modes, active model provenance, and statutory scientific disclaimers.

- **Status Codes**: `200 OK`
- **Sample Request**:
  ```bash
  curl -s http://127.0.0.1:8000/health
  ```
- **Response Schema**:
  ```json
  {
    "status": "healthy",
    "service": "forecast-bust-detection",
    "organization": "NCMRWF / MoES",
    "environment": "development",
    "demo_mode": false,
    "demo_mode_description": "Application weather provider fallback mode. ML model provenance is tracked separately by 'data_type' and 'is_demo_model'.",
    "model_version": "model_real_v002",
    "dataset_version": "dataset_real_v002",
    "data_type": "REAL",
    "is_demo_model": false,
    "scientific_disclaimer": "This system provides forecast reliability estimation and does not replace official NWP or meteorological advisories."
  }
  ```

### `GET /ready`
Readiness probe for orchestrators and container health checks.

- **Status Codes**: `200 OK` (Ready), `503 Service Unavailable` (Not ready)
- **Response Schema**:
  ```json
  {
    "status": "ready",
    "database": "connected",
    "model_loaded": true,
    "model_version": "model_real_v002",
    "data_type": "REAL",
    "is_demo_model": false
  }
  ```

---

## 2. Weather & Synoptic Guidance

### `GET /api/weather/forecast`
Fetches medium-range Numerical Weather Prediction guidance across multi-day forecast horizons (Days 1–10).

- **Query Parameters**:
  - `lat` (float, required): Latitude between 6.0 and 38.0°N.
  - `lon` (float, required): Longitude between 68.0 and 98.0°E.
  - `days` (int, optional): Forecast horizon days (default: 10, max: 10).
- **Status Codes**:
  - `200 OK`: Successful retrieval of ECMWF IFS forecast guidance.
  - `422 Unprocessable Entity`: Invalid coordinates or day range.
  - `503 Service Unavailable`: Upstream provider unreachable.

### `GET /api/locations/search`
Forward geocoding search for Indian cities, districts, and observatories.

- **Query Parameters**: `q` (string, required): City or station name (e.g. `Pune`, `Kolkata`).
- **Status Codes**: `200 OK`

---

## 3. Forecast Bust Risk & Explainability

### `GET /api/risk/location`
Computes calibrated forecast-bust probability, reliability index, operational risk badge, and TreeSHAP feature attributions at forecast issuance time $T_0$.

- **Query Parameters**:
  - `lat` (float, required): Latitude coordinate (6.0°N to 38.0°N).
  - `lon` (float, required): Longitude coordinate (68.0°E to 98.0°E).
  - `lead_hours` (int, required): Forecast lead horizon in hours (24, 48, 72, 96, 120, 144, 168, 192, 216, 240).
  - `variable` (string, required): Target meteorological variable (`precipitation`, `temperature`, `wind`, `pressure`, `humidity`).
  - `forecast_value` (float, optional): Scenario override for the forecast value. If omitted, live ECMWF IFS forecast is fetched automatically.
  - `ensemble_spread` (float, optional): Scenario override for ensemble dispersion ($\sigma$).
- **Status Codes**:
  - `200 OK`: Successful inference.
  - `422 Unprocessable Entity`: Unsupported variable or values violating physical plausibility bounds.
  - `503 Service Unavailable`: Upstream operational NWP provider failure.
- **Sample Request**:
  ```bash
  curl -s "http://127.0.0.1:8000/api/risk/location?lat=18.5204&lon=73.8567&lead_hours=96&variable=precipitation"
  ```
- **Sample Response**:
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
        { "feature": "cos_day_of_year", "description": "Climatological Solar Position", "shap_value": 0.045, "impact": "AMPLIFIER" }
      ],
      "top_mitigators": [
        { "feature": "forecast_wind", "description": "Forecasted 10m Wind Speed (8.9 m/s)", "shap_value": -0.21, "impact": "MITIGATOR" }
      ],
      "summary_text": "Overall bust risk is LOW (0.1%). The forecast is currently assessed as highly reliable."
    },
    "disclaimer": "This system provides forecast reliability estimation and does not replace official NWP or meteorological advisories."
  }
  ```

### `GET /api/risk/map`
Returns a model-generated spatial visualization grid of estimated forecast-bust risk and reliability across 25 Indian synoptic stations under the selected scenario.

- **Query Parameters**:
  - `lead_hours` (int, required): Forecast horizon (24 to 240 hours).
  - `variable` (string, required): Selected meteorological variable.
  - `forecast_value` (float, optional): Scenario value applied to the grid.
  - `ensemble_spread` (float, optional): Ensemble spread applied to the grid.
- **Status Codes**: `200 OK`, `422 Unprocessable Entity`

### `GET /api/risk/history`
Returns verified historical forecast vs realized ERA5 reference records with absolute errors and bust determinations.

- **Query Parameters**:
  - `lat` (float, optional): Filter by latitude coordinate.
  - `lon` (float, optional): Filter by longitude coordinate.
  - `limit` (int, optional): Max records to return (default: 20, max: 100).
- **Status Codes**: `200 OK`

### `GET /forecast/{id}/comparison`
Retrieves a single verified historical record comparing forecast against realized ERA5 reference data.

- **Path Parameters**: `id` (string, required): Record identifier (e.g. `fc_pune_day4` or row index `0`).
- **Status Codes**:
  - `200 OK`: Record found and returned with full verification metrics.
  - `404 Not Found`: Nonexistent ID. Strictly never fabricates fake verification records.

---

## 4. Model Registry & Quality Endpoints

### `GET /api/models/current`
Returns metadata, feature lists, and training parameters for the active production model.

- **Status Codes**: `200 OK`

### `GET /api/models/evaluate`
Returns uninflated test metrics evaluated on the chronologically isolated test set (PR-AUC, ROC-AUC, Brier score, Expected Calibration Error).

- **Status Codes**: `200 OK`

### `POST /api/models/rollback`
Rolls back the active model to a specified previous validated version in the registry.

- **Body**: `{"target_version": "model_real_v001"}`
- **Status Codes**: `200 OK`, `400 Bad Request`

### `GET /api/datasets/status`
Returns dataset record counts, provenance (`REAL`), horizon depth, and update status.

- **Status Codes**: `200 OK`

### `GET /api/datasets/quality`
Returns automated data quality checks (missingness, thermodynamic anomalies, coordinate bounds).

- **Status Codes**: `200 OK`

---

## 5. Administrative Automation & Diagnostics

### `GET /api/admin/drift/status`
Executes a two-sample Kolmogorov-Smirnov statistical test across operational predictors against baseline training distributions to detect distribution drift.

- **Status Codes**: `200 OK`
- **Sample Response**:
  ```json
  {
    "status": "STABLE",
    "p_value_threshold": 0.01,
    "drift_detected_features": [],
    "summary": "Kolmogorov-Smirnov two-sample testing confirmed zero significant feature drift across operational predictors."
  }
  ```

### `POST /api/admin/train`
Queues a candidate model retraining job when newly verified forecast/reference pairs become available.

- **Query Parameters**: `force` (bool, default: false).
- **Status Codes**: `202 Accepted`
