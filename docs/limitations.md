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
