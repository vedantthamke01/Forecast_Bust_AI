# SIH26079: Live Demonstration Checklist & Runbook

**Goal**: Flawless, repeatable technical presentation for SIH judges and meteorological evaluators.  
**Golden Rule**: Never fabricate data. If an external API fails, follow the documented degraded recovery procedure.

---

## 1. Pre-Demonstration Environment Checklist (10 Minutes Prior)

Verify that each component is active before the judges arrive:

- [ ] **1. Backend Server Running**:
  - Run: `curl http://127.0.0.1:8000/health`
  - Expected JSON:
    - `"status": "healthy"`
    - `"data_type": "REAL"`
    - `"is_demo_model": false`
    - `"demo_mode": false`
    - `"model_version": "model_real_v002"`
- [ ] **2. Readiness Probe Clean**:
  - Run: `curl http://127.0.0.1:8000/ready`
  - Expected: `"status": "ready"`, `"model_loaded": true`, `"database": "connected"`.
- [ ] **3. Web Dashboard Accessible**:
  - Open: [http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/) in browser.
  - Verify that Leaflet CSS and JS load without network errors.
- [ ] **4. Automated Integrity Pass**:
  - Run in terminal: `python scripts/verify_judge_demo.py`
  - Verify that all 12 test steps report `SUCCESS` and exit with code 0.
- [ ] **5. Browser Zoom & Window Setup**:
  - Set browser zoom to 100% or 110% on a 1080p display for optimal card visibility.
  - Have developer tools console closed or muted.

---

## 2. During-Demo Execution Steps

Follow this exact sequence during the live presentation:

1. **Step A: Select Pune Observatory**
   - Click the `Pune` preset button (18.52°N, 73.86°E).
   - Point out that coordinates update and sync with elevation baselines.
2. **Step B: Select Forecast Horizon**
   - Click `Day 4 (96h)`.
   - Point out that horizons from Day 3 to Day 10 are available.
3. **Step C: Select Variable**
   - Click `Precipitation`.
4. **Step D: Operational NWP Guidance**
   - Point out live ECMWF IFS forecast values (e.g. 0.0 mm rain, temperature, wind, pressure).
   - Point out the `Anti-Leakage Certified` badge proving inference strictly at $T_0$.
5. **Step E: AI Risk Assessment & Reliability**
   - Point out Calibrated Bust Probability (0.1%), Operational Reliability (99.9%), and 🟢 LOW risk badge.
6. **TreeSHAP Explainability Decomposition**
   - Highlight the top risk amplifiers and mitigators.
   - Clarify: *"TreeSHAP explains the machine learning model's prediction, not atmospheric causality."*
7. **What-If Scenario Analysis**
   - Select `Kolkata`, `Day 3`, and `Wind`.
   - In Step D, enter `Forecast Wind = 28.7 m/s` and `Spread = 4.0σ`.
   - Show the risk elevate to 🟠 HIGH with TreeSHAP highlighting the wind gradient.
8. **Spatial Risk Map (Tab 2)**
   - Click on the `Spatial Risk Map (India)` tab.
   - Show the 25-station synoptic grid. Click a station marker (e.g. Mumbai) to inspect localized bust risk.
   - Note: *"This map is a model-generated spatial risk visualization under the scenario, not observed future weather."*
9. **Historical Verification (Tab 3)**
   - Click `Forecast vs Reference`.
   - Explain the two stages: Stage 1 ($T_0$ forecast) $\to$ valid time elapsed $\to$ Stage 2 ($T_0 + \tau$ ERA5 reference verification).
   - Point out lead-dependent dynamic threshold scaling in the table.
10. **State Scientific Boundaries Honestly**
    - State clearly: *"Historical training covers Days 1 to 7 due to public archive limits; operational inference supports Days 3 to 10. We did not fabricate Days 8 to 10 training data."*

---

## 3. Failure Recovery Runbook

If any external network or environment glitch occurs, follow this protocol:

### Scenario A: Open-Meteo Operational NWP Provider Times Out or Returns 503
- **What happens**: The dashboard shows a banner: `Live operational NWP forecast unavailable. Switched to Scenario Override.`
- **Presenter Script**: 
  *"Notice our explicit error handling: our platform adheres to strict scientific integrity. When an external upstream provider is unreachable, the system returns an explicit 503 and never invents synthetic weather values or falsely claims ECMWF attribution. We can immediately switch to What-If Scenario mode to evaluate the model under defined conditions."*
- **Action**: Use the manual scenario inputs in Step D (e.g., enter Precipitation = 42 mm, Spread = 3.8) and proceed with the demonstration.

### Scenario B: Leaflet Map Tiles Do Not Render (No Internet Connection)
- **What happens**: Map markers display, but base OpenStreetMap tiles show grey backgrounds.
- **Presenter Script**:
  *"The application is running in an air-gapped local environment. Notice that all 25 station coordinates, risk scores, and tooltips are computed locally on the CPU without requiring any paid cloud APIs."*

### Scenario C: Judge Asks to See a Non-Existent Historical Forecast ID
- **Action**: Query `http://127.0.0.1:8000/forecast/fake_id_999/comparison`.
- **Expected**: HTTP 404 with detail `Historical verification record 'fake_id_999' not found in verification archive.`
- **Presenter Script**:
  *"Our API strictly enforces referential integrity: it returns a clean 404 and never fabricates mock verification records."*
