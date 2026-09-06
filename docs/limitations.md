# Operational Limitations and Scientific Considerations

**SIH26079**: AI-Based Forecast Bust Detection Platform  
**Organization**: Ministry of Earth Sciences (MoES) / NCMRWF

---

## 1. Operational Scope & Boundaries

1. **Auxiliary Reliability Layer Only**:
   - The platform does not run forward dynamical numerical simulations (e.g. primitive equations, Navier-Stokes). It relies entirely on output from upstream operational NWP models (NCMRWF NCUM, ECMWF IFS, GFS).
   - If upstream NWP forecasts are interrupted or corrupted, bust predictions for future validity times cannot be computed.

2. **Reanalysis vs Ground-Truth Surface Observations**:
   - ERA5 is an atmospheric reanalysis produced by combining past observations with model physics via 4D-Var data assimilation.
   - While ERA5 provides spatially continuous fields across India, it may smooth localized orographic cloudbursts in complex terrain (e.g. Western Ghats ridges, Himalayan valleys) compared to physical surface rain gauges.

3. **Rare-Event Imbalance**:
   - Severe forecast busts represent approximately 10% to 15% of historical medium-range forecast runs.
   - Consequently, models must be evaluated using Precision-Recall curves (PR-AUC), Brier scores, and calibration metrics (ECE), rather than raw accuracy.

4. **India Geographic Domain**:
   - Physical boundary filters are calibrated for the Indian synoptic domain (6°N to 38°N, 68°E to 98°E). Running inference outside this geographical envelope will trigger coordinate warnings.

5. **Operational Retraining Criteria**:
   - Automatic retraining requires accumulation of verified ground-truth reference data (typically available with a 2-day to 5-day latency for preliminary reanalysis products).
   - Candidate models are strictly gated and will not replace the production model unless they meet pre-defined Brier score and PR-AUC thresholds.

6. **Free Public NWP Archive Horizon Depth (168h / Day 7)**:
   - Free public historical NWP endpoints (such as Open-Meteo Previous Runs) archive model initializations up to Day 7 (`previous_day1` through `previous_day7` = 24h to 168h).
   - Historical initializations for Day 8 (192h), Day 9 (216h), and Day 10 (240h) are not retained in public free endpoints. In accordance with strict scientific integrity guidelines, these days are not synthesized or fabricated. Live operational inference continues to support the full 10-day (240h) forecast window via live ECMWF IFS. Full historical Days 8–10 re-forecasting requires institutional NCMRWF/ECMWF MARS tape archive access.

