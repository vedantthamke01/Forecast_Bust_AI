# Scientific Disclaimer & Operational Scope

**System**: AI-Based Forecast Bust Detection Platform  
**Target Organization**: Ministry of Earth Sciences (MoES) / National Centre for Medium Range Weather Forecasting (NCMRWF)

---

## 1. Operational Mandate & Scope

This software system is designed exclusively as an **auxiliary forecast reliability evaluation layer**. 

- It operates downstream of Numerical Weather Prediction (NWP) systems (including global models such as NCUM, ECMWF IFS, GFS, and regional models).
- It analyzes forecast parameters, ensemble dispersion, model jumpiness, and atmospheric dynamics proxies to estimate the **risk of an anomalous forecast failure**.
- **Under NO circumstances does this system generate substitute meteorological forecasts or overwrite official weather advisories.**

## 2. Official Authority

Official weather forecasts, severe weather alerts, cyclone tracks, heavy rainfall red/orange alerts, and heatwave warnings across the Republic of India are under the statutory mandate of:
- **India Meteorological Department (IMD)**
- **National Centre for Medium Range Weather Forecasting (NCMRWF)**

Meteorologists, forecasters, disaster management authorities (NDMA/SDMA), and the public must refer to official bulletins issued by IMD and MoES for operational decisions and life-safety actions.

## 3. Probabilistic Interpretation

- The **Bust Probability $P(\text{Bust} = 1)$** represents the empirical, calibrated likelihood that a forecast's absolute error will exceed pre-configured physical or climatological threshold percentiles.
- A high bust probability does **not** indicate which alternative direction the weather will deviate toward (e.g. higher vs lower precipitation), but indicates that the operational NWP solution has low confidence and elevated vulnerability to significant error.
