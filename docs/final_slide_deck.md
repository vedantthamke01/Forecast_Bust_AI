# SIH26079: Final Presentation Slide Deck Outline

**Problem Statement ID**: SIH26079  
**Title**: AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts (Days 3–10)  
**Target Organization**: Ministry of Earth Sciences (MoES) / NCMRWF  
**Total Slides**: 10 Slides (Target Time: 5–7 minutes)

---

### Slide 1: Title & Value Proposition
- **Header**: AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts
- **Subheader**: A Calibrated Machine Learning Reliability Layer for Operational NWP
- **Key Points**:
  - Target Organization: Ministry of Earth Sciences / NCMRWF
  - Core Goal: Estimating the probability of anomalous forecast failure before issuance.
  - Operational Scope: Days 3–10 medium-range medium-range forecasts across India.
- **Suggested Visual**: Hero graphic showing NWP forecast trajectory splitting into calibrated confidence bands with green/orange/red risk badges.
- **Speaker Notes**: "Good morning. We present SIH26079: an AI-based forecast reliability layer developed for the Ministry of Earth Sciences and NCMRWF to detect medium-range forecast busts."

---

### Slide 2: The Operational Problem
- **Header**: The Vulnerability: When Medium-Range Forecasts Bust
- **Key Points**:
  - NWP models (NCUM, ECMWF IFS, GFS) are computationally powerful but chaotic.
  - Rare, extreme forecast busts occur due to non-linear dynamics, terrain, and parameterization limits.
  - Disastrous consequences: Missed cloudbursts, unpredicted flooding, or false heatwave alarms.
  - Current gap: Forecasters lack an automated, quantitative probability of forecast failure.
- **Suggested Visual**: Side-by-side comparison of a 4-day NWP rainfall forecast showing 0 mm vs realized post-event rainfall showing 120 mm.
- **Speaker Notes**: "Even with supercomputers, chaotic atmosphere dynamics trigger forecast busts. When a 4-day forecast fails, emergency planners are caught unprepared."

---

### Slide 3: Why Raw Model Output & Spread Are Not Enough
- **Header**: Why Traditional Dispersion Metrics Fall Short
- **Key Points**:
  - Deterministic forecasts give no measure of forecast uncertainty.
  - Ensemble spread is valuable, but frequently suffers from under-dispersion.
  - Ensembles can cluster tightly around a shared physical bias and bust together.
  - Climatological variance varies drastically between Western Ghats, Thar Desert, and the Himalayas.
- **Suggested Visual**: Diagram illustrating ensemble under-dispersion: tight member clustering that completely misses the true atmospheric outcome.
- **Speaker Notes**: "Ensemble spread is standard, but spread alone can stay narrow even when the whole ensemble cluster misses a synoptic shift."

---

### Slide 4: The Proposed Solution: An AI Reliability Layer
- **Header**: Our Approach: Decoupled AI Reliability Evaluation
- **Key Points**:
  - **Not** a replacement weather model; does **not** predict weather independently.
  - Evaluates forecast stability at initialization time $T_0$ using 17 dynamical features.
  - Outputs calibrated bust probability $P(\text{Bust} \in [0, 1])$ and operational reliability scores.
  - Categorizes risk into 4 standardized tiers: 🟢 LOW, 🟡 MODERATE, 🟠 HIGH, 🔴 VERY HIGH.
- **Suggested Visual**: Conceptual diagram showing NWP output passing into the AI Reliability Gate, outputting P(Bust) and Risk Badges.
- **Speaker Notes**: "We don't replace NWP. We build an intelligence layer on top of NWP that asks: How much can we trust this specific forecast given these synoptic conditions?"

---

### Slide 5: System Architecture & Decoupled Data Flow
- **Header**: System Architecture: Strict Temporal Decoupling
- **Key Points**:
  - **Stage 1 (Inference at $T_0$)**: Live ECMWF IFS forecast $\to$ anti-leakage check $\to$ feature pipeline $\to$ LightGBM $\to$ P(Bust).
  - **Stage 2 (Verification at $T_0 + \tau$)**: Realized ERA5 reanalysis ingested strictly after valid time $\to$ error computation $\to$ bust label.
  - Automated anti-leakage gate intercepts 9 forbidden patterns; zero future leakage.
  - Lead-scaled dynamic thresholding: $\text{Threshold}(\tau) = \text{Base} \times [1 + 0.12 \times (\tau - 24)/24]$.
- **Suggested Visual**: End-to-end architecture diagram highlighting the temporal gap $\tau$ between $T_0$ prediction and $T_0 + \tau$ verification.
- **Speaker Notes**: "Our architecture enforces strict temporal separation: at forecast time, future reference data does not exist. The leakage gate ensures no future error terms enter inference."

---

### Slide 6: Machine Learning, Calibration & TreeSHAP
- **Header**: AI Architecture: LightGBM, Isotonic Calibration & TreeSHAP
- **Key Points**:
  - **LightGBM Classifier**: Handles non-linear thresholds and tabular atmospheric features on CPU (3–8 ms).
  - **Isotonic Probability Calibration**: Aligns raw leaf scores with empirical event frequencies (Brier Score: 0.0450, ECE: 0.0257).
  - **TreeSHAP Explainability**: Decomposes prediction into local risk amplifiers and mitigators.
  - Explains the *model decision*, avoiding unscientific claims of atmospheric causality.
- **Suggested Visual**: Waterfall TreeSHAP chart showing how ensemble spread and wind features push probability from baseline to final calibrated score.
- **Speaker Notes**: "We use LightGBM calibrated with Isotonic regression. With TreeSHAP, every prediction is fully interpretable, showing forecasters exactly which features drove the risk."

---

### Slide 7: Live Web Dashboard & 25-Station GIS Map
- **Header**: Operational Implementation: Interactive Meteorological Dashboard
- **Key Points**:
  - Guided 5-step judge workflow: Observatory $\to$ Horizon $\to$ Variable $\to$ NWP Guidance $\to$ AI Risk.
  - Interactive Leaflet OpenStreetMap spatial risk grid across 25 Indian synoptic stations.
  - "What-If" scenario sensitivity mode for testing extreme winds or convective spreads.
  - Built on a strict ₹0 infrastructure budget with 100% open-source software.
- **Suggested Visual**: Screenshot montage of the live web dashboard showing the Pune Day 4 forecast card, TreeSHAP panel, and India spatial risk map.
- **Speaker Notes**: "Our dashboard allows forecasters to inspect any of 25 stations across India, adjust horizons from Day 3 to 10, inspect TreeSHAP drivers, and evaluate spatial risk."

---

### Slide 8: Verified Scientific Evaluation Results
- **Header**: Empirical Results: Held-Out Chronological Test Set
- **Key Points**:
  - Evaluated on future partition (2026-01-15 to 2026-01-17; 7,560 records; 5.38% bust prevalence).
  - **PR-AUC**: **0.2682** vs 0.0950 baseline (**+0.1732 absolute improvement**, 2.82× gain).
  - **ROC-AUC**: **0.8756** (High discriminative resolution across operating thresholds).
  - **Brier Calibration Score**: **0.0450** | **Expected Calibration Error**: **0.0257**.
  - **Overall Accuracy**: **94.62%** | **Inference Latency**: **3–8 ms**.
- **Suggested Visual**: Calibration curve (reliability diagram) showing predicted probability vs fraction of positives tracking the diagonal line.
- **Speaker Notes**: "On our future test partition, PR-AUC improved from 0.0950 to 0.2682. Our Brier score is 0.0450 and ECE is 0.0257, proving strong probabilistic reliability."

---

### Slide 9: Scientific Integrity, Authenticity & Honest Limitations
- **Header**: Scientific Rigor: Authentic Data & Explicit Limitations
- **Key Points**:
  - **100% Real Data**: 37,800 authentic records from Open-Meteo NWP and Copernicus ERA5.
  - **Archive Boundary**: Historical training covers Days 1–7 (168h); operational inference covers Days 3–10 (240h).
  - **No Fabrication**: Days 8–10 historical data were unavailable from free archives and were not fabricated.
  - **ERA5 Role**: Reanalysis reference dataset for development, not instantaneous station ground truth.
- **Suggested Visual**: Matrix summarizing Data Provenance: REAL, Leakage Gate: PASSED, Horizon Coverage: Days 1–7 Training / Days 3–10 Operational.
- **Speaker Notes**: "We maintain complete scientific honesty: our historical archive covers Days 1 to 7. Rather than fabricating fake Day 8 to 10 training data, we clearly document this archive boundary."

---

### Slide 10: Operational Value & Future Institutional Integration
- **Header**: Impact & Roadmap for NCMRWF Deployment
- **Key Points**:
  - **Immediate Value**: Provides quantitative reliability scores to forecasters and disaster agencies.
  - **Institutional Roadmap**:
    1. Connect directly to NCMRWF HPC output queues (NCUM GRIB2 streams).
    2. Ingest IMD automated weather station networks for real-time station-level verification.
    3. Ingest raw 51-member ensemble member grids for spatial ensemble variance.
  - **Conclusion**: A reproducible, scientifically defensible decision-support platform for India.
- **Suggested Visual**: Roadmap diagram showing transition from current open prototype to integrated NCMRWF HPC workflow.
- **Speaker Notes**: "By integrating this reliability layer with NCMRWF's supercomputing workflows, we can empower Indian forecasters to catch forecast busts before they strike. Thank you."
