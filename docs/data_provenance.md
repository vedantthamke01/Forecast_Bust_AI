# Data Provenance, Taxonomy, and Curation Architecture

**Project**: SIH26079 — AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts  
**Organization**: Ministry of Earth Sciences (MoES) / National Centre for Medium Range Weather Forecasting (NCMRWF)  
**Standard**: Scientific Authenticity, Verifiable Provenance, and Zero Data Fabrication.

---

## 1. Data Pipeline Lifecycle & Provenance Flow

The software pipeline and documented processing methodology are reproducible with access to the required source data and archives. Historical Days 3–7 data are available from the documented archive workflow; historical Days 8–10 training data were not available from the public archive, and institutional archive access is required to extend historical training through Day 10. The training and validation dataset (`dataset_real_v002.csv`) is produced through an automated ingestion and spatio-temporal alignment pipeline:

```text
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│ Historical NWP Forecast Archive │       │ Copernicus ERA5 Global Ref      │
│ Provider: open-meteo-previous   │       │ Provider: era5-reanalysis (CDS) │
│ Model: ECMWF IFS / GFS Seamless │       │ European Atmospheric Reanalysis │
│ Initialized at T₀ for T₀ + τ    │       │ Hourly 0.25° Gridded Fields     │
└────────────────┬────────────────┘       └────────────────┬────────────────┘
                 │                                         │
                 └────────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │ Spatio-Temporal Aligner (aligner.py)   │
                  │ Match Criterion: Valid Time T₀ + τ     │
                  │ Spatial Proximity: Δd ≤ 0.25°          │
                  │ Verified Output: 37,800 Aligned Pairs  │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │ Error Computation Engine               │
                  │ |NWP - ERA5| across physical variables │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │ Lead-Scaled Dynamic Bust Labeler       │
                  │ Threshold(τ) = Base · [1 + 0.12(τ-24)] │
                  │ Target Assigned: is_bust ∈ {0, 1}      │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │ Verified Champion Dataset              │
                  │ datasets/training/dataset_real_v002.csv │
                  │ Provenance: REAL (Non-Synthetic)       │
                  └────────────────────────────────────────┘
```

---

## 2. Distinction of Three Operational Data Roles

To prevent confusion among judges and meteorological reviewers, the system enforces a strict taxonomy:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               METEOROLOGICAL DATA TAXONOMY                             │
├──────────────────────┬─────────────────────────────────────────────────────────────────┤
│ Data Role            │ Source, Definition & Access Protocol                            │
├──────────────────────┼─────────────────────────────────────────────────────────────────┤
│ 1. Historical        │ Archived numerical weather prediction runs initialized at T₀    │
│    Forecasts         │ for valid time T₀ + τ. Ingested from the Open-Meteo Previous    │
│                      │ Runs archive. Reflects what the numerical model predicted.      │
├──────────────────────┼─────────────────────────────────────────────────────────────────┤
│ 2. Historical        │ Copernicus ERA5 global atmospheric reanalysis (0.25° grid).     │
│    Reference         │ Produced via 4D-Var data assimilation combining past surface,   │
│    (ERA5)            │ radiosonde, and satellite observations with model physics.      │
│                      │ Ingested via Copernicus Climate Data Store (CDS API).           │
│                      │ CRITICAL: ERA5 is a historical reanalysis reference dataset.   │
│                      │ It is NOT an instantaneous real-time station observation.       │
├──────────────────────┼─────────────────────────────────────────────────────────────────┤
│ 3. Operational Live  │ Live ECMWF IFS operational forecast guidance ingested at        │
│    Forecast          │ initialization time T₀. Supports horizons Days 3–10 (72–240h). │
└──────────────────────┴─────────────────────────────────────────────────────────────────┘
```

---

## 3. Champion Dataset Specifications (`dataset_real_v002.csv`)

| Attribute | Verified Value | Inspection / Audit Note |
| :--- | :--- | :--- |
| **Filename** | `datasets/training/dataset_real_v002.csv` | File size: 10,431,467 bytes (10.4 MB) |
| **Data Provenance** | `REAL` | Non-synthetic, authentic NWP and ERA5 records |
| **Total Record Count** | **37,800 records** | Exactly 1,512 records per station across 25 stations |
| **Geographic Coverage** | **25 Indian Synoptic Observatories** | Multi-regime representation across India |
| **Coordinate Bounds** | Latitude: 8.52°N to 34.08°N, Longitude: 72.36°E to 91.89°E | Domain: 6°N–38°N, 68°E–98°E |
| **Historical Range** | 2024-07-10 00:00:00 to 2026-01-17 23:00:00 | Continuous multi-season span |
| **Forecast Lead Times** | 24, 48, 72, 96, 120, 144, 168 hours | Horizons Days 1 through 7 |
| **Overall Bust Prevalence** | **11.87%** (4,488 busts / 37,800 records) | Rare-event realistic distribution |
| **Valid Time Identity** | 100% matched ($t_{\text{valid}} - t_{\text{init}} \equiv \tau$) | Exactly 0 mismatches across 37,800 rows |
| **Duplicate Spatio-Temporal Keys** | **0 duplicates** | Clean unique key constraint $(s_i, T_0, \tau)$ |

---

## 4. Geographic Distribution: 25 Synoptic Observatories

The dataset spans all major synoptic and climatological zones of the Indian subcontinent:

```text
┌────────────────────┬───────────┬───────────┬──────────────┬───────────────────────────────┐
│ Station Name       │ Latitude  │ Longitude │ Elevation(m) │ Climatological Zone           │
├────────────────────┼───────────┼───────────┼──────────────┼───────────────────────────────┤
│ Pune               │ 18.5204°N │ 73.8567°E │ 560 m        │ Western Ghats Rain Shadow     │
│ New Delhi (Safd.)  │ 28.6139°N │ 77.2090°E │ 216 m        │ Indo-Gangetic Plains          │
│ Mumbai (Santacruz) │ 19.0760°N │ 72.8777°E │ 14 m         │ West Coastal Maritime         │
│ Chennai (Meenam.)  │ 13.0827°N │ 80.2707°E │ 16 m         │ East Coastal / NE Monsoon     │
│ Kolkata (Alipore)  │ 22.5726°N │ 88.3639°E │ 9 m          │ Gangetic Delta / Bay of Bengal│
│ Bengaluru          │ 12.9716°N │ 77.5946°E │ 920 m        │ South Deccan Plateau          │
│ Hyderabad          │ 17.3850°N │ 78.4867°E │ 542 m        │ Central Deccan Semi-Arid      │
│ Ahmedabad          │ 23.0225°N │ 72.5714°E │ 53 m         │ Western Semi-Arid             │
│ Jaipur             │ 26.9124°N │ 75.7873°E │ 431 m        │ Sub-Tropical / Aravalli Ridge │
│ Shimla             │ 31.1048°N │ 77.1734°E │ 2,206 m      │ Western Himalayan Montane     │
│ Srinagar           │ 34.0837°N │ 74.7973°E │ 1,585 m      │ Kashmir Valley Alpine         │
│ Guwahati           │ 26.1445°N │ 91.7362°E │ 55 m         │ Brahmaputra River Basin       │
│ Shillong           │ 25.5788°N │ 91.8933°E │ 1,525 m      │ Meghalaya Plateau (High Rain) │
│ Thiruvananthapuram │ 8.5241°N  │ 76.9366°E │ 64 m         │ Southwest Monsoon Gateway     │
│ Bhubaneswar        │ 20.2961°N │ 85.8245°E │ 45 m         │ East Coastal Cyclone Track    │
│ Bhopal             │ 23.2599°N │ 77.4126°E │ 527 m        │ Central India Plateau         │
│ Visakhapatnam      │ 17.6868°N │ 83.2185°E │ 45 m         │ Eastern Ghats Maritime        │
│ Patna              │ 25.5941°N │ 85.1376°E │ 53 m         │ Middle Ganga Plain            │
│ Lucknow            │ 26.8467°N │ 80.9462°E │ 123 m        │ Upper Ganga Plain             │
│ Nagpur             │ 21.1458°N │ 79.0882°E │ 310 m        │ Vidarbha Central Region       │
│ Dehradun           │ 30.3165°N │ 78.0322°E │ 682 m        │ Shivalik Foothills            │
│ Ranchi             │ 23.3441°N │ 85.3096°E │ 651 m        │ Chota Nagpur Plateau          │
│ Chandigarh         │ 30.7333°N │ 76.7794°E │ 321 m        │ Northern Plain Sub-Himalayan  │
│ Panaji (Goa)       │ 15.4909°N │ 73.8278°E │ 10 m         │ Konkan Coast Maritime         │
│ Noida              │ 28.5355°N │ 77.3910°E │ 200 m        │ National Capital Region       │
└────────────────────┴───────────┴───────────┴──────────────┴───────────────────────────────┘
```

---

## 5. Forecast Horizon Boundaries: Days 1–7 vs Days 8–10

A fundamental scientific integrity policy governs this project:

- **Why Days 8–10 are not in historical training**: Public open NWP endpoints (such as Open-Meteo Previous Runs) archive model initializations through Day 7 (168 hours). Days 8, 9, and 10 are not retained in public free archives.
- **Strict Anti-Fabrication Rule**: Rather than generating synthetic data for Days 8–10, the team chose to document this archive limit honestly.
- **Operational Inference**: Live ECMWF IFS operational feeds provide full 10-day forecasts ($240\text{h}$), enabling operational bust prediction across Days 3–10.
- **Path to Full Coverage**: Institutional integration with NCMRWF or ECMWF MARS tape archives will supply authentic historical runs through Day 10.

---

## 6. Deprecation of Synthetic Demo Dataset

In earlier rapid prototyping phases, a synthetic dataset (`dataset_v001.csv`, 250 rows) was used to validate UI wireframes. 

**Status**: `dataset_v001.csv` is strictly deprecated and archived. All reported production metrics, models, calibration curves, and dashboard endpoints operate exclusively on `dataset_real_v002.csv` (37,800 authentic records).
