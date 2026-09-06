# Operational Limitations and Scientific Considerations

**SIH26079**: AI-Based Forecast Bust Detection Platform  
**Organization**: Ministry of Earth Sciences (MoES) / NCMRWF

---

## 1. Operational Scope & Boundaries

1. **Auxiliary Reliability Layer Only**:
   - The platform does not run forward dynamical numerical simulations (e.g. primitive equations, Navier-Stokes). It relies entirely on output from upstream operational NWP models (NCMRWF NCUM, ECMWF IFS, GFS).
   - If upstream NWP forecasts are interrupted or corrupted, bust predictions for future validity times cannot be computed.

2. **Reanalysis vs In-Situ Surface Observations**:
   - ERA5 is an atmospheric reanalysis produced by combining past observations with model physics via 4D-Var data assimilation.
   - In this project, ERA5 reanalysis is used as the historical and post-event reference dataset for error calculation and model development. It is not an instantaneous real-time observational station feed.
   - While ERA5 provides spatially continuous fields across India, it may smooth localized orographic cloudbursts in complex terrain (e.g. Western Ghats ridges, Himalayan valleys) compared to physical surface rain gauges.

3. **Rare-Event Imbalance**:
   - Severe forecast busts represent approximately 10% to 15% of historical medium-range forecast runs (11.87% in the real training dataset).
   - Consequently, models must be evaluated using Precision-Recall curves (PR-AUC), Brier scores, and calibration metrics (ECE), rather than raw accuracy.

4. **India Geographic Domain**:
   - Physical boundary filters are calibrated for the Indian synoptic domain (6°N to 38°N, 68°E to 98°E). Running inference outside this geographical envelope will trigger coordinate warnings.

5. **Operational Retraining Criteria**:
   - The system supports retraining when newly verified forecast/reference pairs become available (rather than online continuous learning).
   - Automated retraining requires accumulation of verified post-event reference data. Candidate models are strictly gated and will not replace the production model unless they meet pre-defined Brier score and PR-AUC thresholds.

6. **Free Public NWP Archive Horizon Depth (168h / Day 7) vs Operational (240h / Day 10)**:
   - The system supports operational bust-risk estimation through Day 10, while the current public historical archive used for model development extends through Day 7 (24–168h).
   - Historical training coverage for Days 8–10 requires access to a deeper institutional NWP archive. Days 8–10 historical training data were not available from the public archive and have not been fabricated.

7. **Intended Users**:
   - Potential users include meteorological forecast analysts, forecast operations teams, researchers, disaster-management decision-support systems, and downstream applications that need forecast reliability information.
   - The platform is an auxiliary reliability layer; it does not claim current institutional adoption or operational deployment by IMD or NCMRWF.


