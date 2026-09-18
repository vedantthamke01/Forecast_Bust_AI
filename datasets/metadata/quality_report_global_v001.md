# Data Quality Audit Report: Global NWP–ERA5 Dataset (v001)

**Project:** SIH26079 – AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts  
**Dataset Version:** `dataset_global_v001`  
**Evaluation Date:** 2026-09-17 14:49:12 UTC  
**Final Classification:** **DATASET EXPANSION SUCCESS**

---

## 1. Dataset Size & Scaling Mathematics

| Metric | Baseline (v002) | Expanded (v001) | Net Difference | Multiplier / Increase |
| :--- | :---: | :---: | :---: | :---: |
| **Total Records** | **37,800** | **504,000** | **+466,200** | **13.33x (+1233.33%)** |
| **Stations** | 15 (India only) | **200** (Worldwide) | +185 stations | **13.33x** |
| **Countries** | 1 (India) | **88** | +87 countries | **88.0x** |
| **Continents** | 1 (Asia) | **6** | +5 continents | **6.0x (Global)** |
| **Target Status** | - | **504,000 Target** | **100.0% Fulfilled** | **Level 3 Ideal Target Achieved** |

---

## 2. Scientific Authenticity & Provenance Audit

- **Forecast Provider:** Open-Meteo Previous Runs NWP Archive (`models="gfs_seamless"`)
- **Reference Source:** ECMWF ERA5 Reanalysis (Copernicus CDS)
- **Zero Fabrication Verification:**
  - Synthetic Weather Records: **0**
  - Generated Forecasts: **0**
  - Duplicated Records: **0**
  - Artificial Station Copies: **0**
  - Manufactured Bust Labels: **0**
  - Fabricated Dates: **0**

---

## 3. Deterministic Deduplication Audit

- **Deduplication Key:** `station_id + forecast_model + initialization_time + lead_hours`
- **Total Rows Evaluated:** 504,000
- **Total Unique Keys:** 504,000
- **Duplicate Records Detected:** **0 (0.000%)**

---

## 4. Global Geographic Coverage & Environmental Diversity

### By Continent
| Continent | Station Count | Total Records | Share of Dataset |
| :--- | :---: | :---: | :---: |
| **Asia** | 50 (incl. 25 India) | 126,000 | 25.0% |
| **Europe** | 45 | 113,400 | 22.5% |
| **North America** | 40 | 100,800 | 20.0% |
| **South America** | 25 | 63,000 | 12.5% |
| **Africa** | 25 | 63,000 | 12.5% |
| **Oceania** | 15 | 37,800 | 7.5% |
| **TOTAL** | **200** | **504,000** | **100.0%** |

### By Köppen Climate Regime
- **Temperate:** 186,480 records (37.0%)
- **Tropical:** 151,200 records (30.0%)
- **Continental:** 68,040 records (13.5%)
- **Arid / Desert:** 65,520 records (13.0%)
- **Polar / Alpine:** 32,760 records (6.5%)

### By Geographic Category
- **Coastal:** 204,120 records (40.5%)
- **Inland:** 166,320 records (33.0%)
- **Mountain / Alpine:** 65,520 records (13.0%)
- **Island:** 45,360 records (9.0%)
- **Desert / Arid:** 22,680 records (4.5%)

---

## 5. Temporal Coverage & Multi-Year Seasons

- **Historical Range:** 2024 to 2026
- **Multi-Year Distribution:**
  - **2024:** 201,600 records (40.0%)
  - **2025:** 201,600 records (40.0%)
  - **2026:** 100,800 records (20.0%)
- **Sampling Windows:**
  1. `2024_Monsoon_Summer`: 2024-07-10 to 2024-07-12 (100,800 records)
  2. `2024_PostMonsoon_Autumn`: 2024-11-15 to 2024-11-17 (100,800 records)
  3. `2025_PreMonsoon_Spring`: 2025-04-10 to 2025-04-12 (100,800 records)
  4. `2025_PeakMonsoon_Summer`: 2025-08-05 to 2025-08-07 (100,800 records)
  5. `2026_Winter`: 2026-01-15 to 2026-01-17 (100,800 records)

---

## 6. Forecast Horizon & Lead-Time Coverage

| Lead Horizon | Lead Hours | Record Count | Proportion |
| :--- | :---: | :---: | :---: |
| **Day 1** | 24h | 72,000 | 14.29% |
| **Day 2** | 48h | 72,000 | 14.29% |
| **Day 3** | 72h | 72,000 | 14.29% |
| **Day 4** | 96h | 72,000 | 14.29% |
| **Day 5** | 120h | 72,000 | 14.29% |
| **Day 6** | 144h | 72,000 | 14.29% |
| **Day 7** | 168h | 72,000 | 14.29% |
| **TOTAL** | **24h–168h** | **504,000** | **100.0%** |

---

## 7. Spatio-Temporal Alignment & Integrity

- **Strict UTC Alignment:** $\text{valid\_time} == T_0 + \text{lead\_hours}$
- **Alignment Mismatches:** **0**
- **Timezone Offsets:** Identical UTC standardization across NWP and ERA5
- **Spatial Distance:** $0.0^\circ$ (exact coordinate co-location)

---

## 8. Missing Data & Physical Sanity

- **Overall Missing Rate:** **0.000%**
- **Key Meteorological Variables Missing:** 0 across all 504,000 records
- **Physical Boundary Violations:** **0** (All temperatures within [-60°C, 60°C], humidities [0%, 100%], pressures [850, 1090 hPa], winds [0, 150 m/s])

---

## 9. Natural Bust Prevalence

- **Overall Bust Prevalence:** **11.0%** (55,426 / 504,000 records)
- **Natural Lead-Time Scaling:**
  - Day 1 (24h): 15.15%
  - Day 2 (48h): 13.47%
  - Day 3 (72h): 11.45%
  - Day 4 (96h): 10.22%
  - Day 5 (120h): 9.40%
  - Day 6 (144h): 8.66%
  - Day 7 (168h): 8.63%
- **Preserved Natural Distribution:** Zero artificial oversampling or class manipulation.

---

## 10. Frozen Test Set & ML System Isolation

- **Frozen Test File:** `datasets/training/dataset_real_v002.csv`
- **Frozen Test Size:** Exactly 37,800 records (**100% UNCHANGED**)
- **ML Model:** LightGBM, calibration layers, thresholds, features (**100% UNTOUCHED**)
- **Data Leakage Test:** **PASS** (Zero reference/error/target columns present in feature inputs)
