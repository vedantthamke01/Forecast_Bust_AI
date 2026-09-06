# ₹0 Budget & Data Sources Architecture Audit

**Project**: SIH26079 — AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts  
**Organization**: Ministry of Earth Sciences (MoES) / NCMRWF  
**Budget Policy**: **Strict ₹0 (Zero INR) Operational & Development Budget**

---

## 1. System Cost Audit Matrix

| System Component | Technology / Data Source | Operational Cost | License / Access Terms | Required? |
| :--- | :--- | :---: | :--- | :---: |
| **Mobile & Web UI** | Flutter & Dart SDK | **₹0** | BSD-3-Clause Open Source | **Yes** |
| **Meteorological Dashboard** | HTML5 / CSS3 / Vanilla JS | **₹0** | Open Source (Leaflet / Chart.js) | **Yes** |
| **Backend REST Engine** | FastAPI / Uvicorn / Pydantic | **₹0** | MIT License Open Source | **Yes** |
| **Local Database Engine** | Async SQLite (Local) / PostgreSQL + PostGIS (Docker) | **₹0** | Public Domain / PostgreSQL Open Source | **Yes** |
| **Spatial Maps & Tiles** | OpenStreetMap (OSM) Tiles | **₹0** | ODbL (Open Database License) | **Yes** |
| **Geocoding Service** | OSM Nominatim + Embedded Indian Cities DB | **₹0** | Public ODbL + Custom In-Memory DB | **Yes** |
| **Machine Learning** | LightGBM / Scikit-Learn | **₹0** | MIT / BSD Open Source | **Yes** |
| **Model Calibration** | Isotonic Regression / Platt Scaling | **₹0** | BSD Open Source | **Yes** |
| **Model Explainability** | SHAP (TreeExplainer) | **₹0** | MIT Open Source | **Yes** |
| **Live NWP Forecasts** | Open-Meteo Free API (ECMWF IFS / GFS Ensemble) | **₹0** | Free Non-Commercial / Open-Meteo Fair Use | **Yes** |
| **Reference / Reanalysis**| ERA5 Reanalysis via Copernicus CDS / Open-Meteo Archive | **₹0** | Copernicus Free Open Access Terms | **Yes** |
| **Historical Forecast Archive**| ECMWF Open Data / Verified Indian Benchmark Dataset | **₹0** | Creative Commons / NCMRWF Open Benchmark | **Yes** |
| **Google Weather API** | Google Weather Forecast API | Optional | Paid API Key (Free tier only if enabled) | **NO (Optional)**|
| **Paid Cloud / LLM APIs** | OpenAI / Cloudflare / AWS / Azure / GCP Vertex | **₹0** | None Used in Production Runtime | **NO (Prohibited)**|

---

## 2. Scientific Data Source Clarification (ERA5 vs Historical Forecasts)

In accordance with scientific meteorological integrity, this platform strictly distinguishes between data roles:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        METEOROLOGICAL DATA TAXONOMY                    │
├────────────────────────────┬───────────────────────────────────────────┤
│ DATA ROLE                  │ SOURCE & DEFINITION                       │
├────────────────────────────┼───────────────────────────────────────────┤
│ 1. Historical Forecasts    │ Open-Meteo Previous Runs / ECMWF Open Data│
│    "What was predicted?"   │ Real archived forecasts initialized at T  │
│                            │ for valid time T + tau (Days 1-7, 24-168h)│
│                            │ (Free endpoint stores up to Day 7).       │
├────────────────────────────┼───────────────────────────────────────────┤
│ 2. Reference / Reanalysis  │ ERA5 Reanalysis (ECMWF / Copernicus)      │
│    "What occurred?"        │ Physical data assimilation combining past │
│                            │ observations with numerical models into   │
│                            │ a unified global gridded field.           │
│                            │ NOTE: ERA5 is a reanalysis reference, NOT │
│                            │ a raw station observation or forecast.    │
├────────────────────────────┼───────────────────────────────────────────┤
│ 3. Station Observations    │ IMD Synoptic Station Network              │
│    "Ground Truth"          │ Physical surface sensors at Indian        │
│                            │ observatories (rain gauges, anemometers). │
├────────────────────────────┼───────────────────────────────────────────┤
│ 4. Live Operational NWP    │ Open-Meteo Global Ensemble (10-Day)       │
│    "Current Guidance"      │ Multi-model operational forecast horizon  │
│                            │ supporting full Days 1-10 (24h to 240h).  │
└────────────────────────────┴───────────────────────────────────────────┘
```

---

## 3. Upstream Provider Failure & Fault-Tolerance Behavior

In accordance with strict scientific meteorological integrity, the platform never invents synthetic weather values or falsely attributes fabricated guidance to ECMWF when an upstream provider request fails:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   OPERATIONAL PROVIDER FAILURE HANDLING                │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Upstream Provider Available:                                        │
│    Live ECMWF IFS forecast returned -> feature extraction -> inference  │
│                                                                        │
│ 2. Upstream Provider Unavailable / Network Timeout:                     │
│    Explicit HTTP 503 (Service Unavailable) status returned with        │
│    descriptive diagnostic message. No weather values are invented.     │
│                                                                        │
│ 3. Forecaster Scenario / What-If Mode:                                 │
│    Forecasters can supply explicit scenario overrides (e.g. 42mm,      │
│    3.8σ spread) for sensitivity and stress evaluation.                 │
└────────────────────────────────────────────────────────────────────────┘
```

No external network interruption can cause silent data corruption or false attribution.

