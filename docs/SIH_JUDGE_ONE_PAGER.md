# SIH26079: AI-Based Forecast Bust Detection Platform
### Ministry of Earth Sciences (MoES) / NCMRWF | One-Page Technical Brief

---

### The Problem
Numerical Weather Prediction (NWP) models (NCUM, ECMWF IFS, GFS) are the backbone of modern meteorology. However, non-linear atmospheric chaos, complex terrain, and convective parameterization uncertainties cause rare but severe **forecast busts**—extreme failures where forecasts deviate drastically from reality. Meteorologists and disaster authorities currently lack an automated, quantitative estimate of whether a medium-range forecast is stable or vulnerable to an imminent bust.

### The Solution
An **AI-based forecast reliability layer** that operates downstream of operational NWP models. At forecast issuance time $T_0$, the system evaluates forecast dynamics, ensemble dispersion, seasonal solar phases, and run revision consistency to estimate the calibrated probability of a significant forecast failure $P(\text{Bust} \in [0, 1])$.

```text
Operational NWP Forecast (T₀) ──► 17 Forecast-Time Features ──► Anti-Leakage Gate ──► Calibrated LightGBM
                                                                                              │
┌─────────────────────────────────────────────────────────────────────────────────────────────┘
▼
• Calibrated P(Bust) & Reliability Score (0–100%)       • TreeSHAP Factor Attribution (Amplifiers / Mitigators)
• Operational Risk Badge (🟢 LOW to 🔴 VERY HIGH)        • 25-Station Spatial Risk Map (India Synoptic Domain)
```

---

### Key Technical Architecture
- **Model**: Tuned LightGBM Decision Trees with **Isotonic Probability Calibration** (`model_real_v002`).
- **Explainability**: **TreeSHAP** additive feature attribution decomposes predictions into top risk amplifiers and mitigators, explaining the model's prediction without making unwarranted physical causal claims.
- **Dataset**: `dataset_real_v002.csv` containing **37,800 authentic, spatio-temporally aligned records** across 25 Indian synoptic observatories (2024–2026).
- **Decoupled Verification**: Historical forecast initialized at $T_0$ is evaluated against post-event Copernicus ERA5 reanalysis reference at valid time $T_0 + \tau$ using lead-scaled dynamic thresholding:
  $$\text{Threshold}(\tau) = \text{Base\_Threshold} \times \left[1.0 + 0.12 \times \max\left(0, \frac{\tau - 24}{24}\right)\right]$$
- **Anti-Leakage Safeguard**: 9-keyword forbidden pattern scanner blocks future references and error terms from entering $T_0$ feature extraction (13/13 adversarial attacks blocked).

---

### Verified Performance on Chronologically Isolated Test Set (7,560 Records)
*Evaluated on future partition (2026-01-15 to 2026-01-17; test bust prevalence: 5.38%):*
- **PR-AUC**: **0.2682** (Baseline: 0.0950 $\to$ **+0.1732 absolute improvement**, 2.82× baseline)
- **ROC-AUC**: **0.8756** (High discriminative resolution across all operating thresholds)
- **Brier Calibration Score**: **0.0450** | **Expected Calibration Error (ECE)**: **0.0257**
- **Overall Accuracy**: **94.62%** | **Prediction Latency**: **3–8 ms** (CPU)

---

### Core Innovation vs. Standard Dashboards
Most meteorological software simply displays raw NWP output. **SIH26079 builds an intelligence layer on top of NWP**: it asks not *"What does the model predict?"*, but *"How much can we trust this specific prediction given these synoptic conditions?"*.

### Key Scientific Limitations & Honest Boundaries
1. **Horizon Coverage**: Historical training covers Days 1–7 (24h–168h) due to public archive limits; live operational inference covers Days 3–10 (72h–240h). Days 8–10 historical data were not available and never fabricated.
2. **ERA5 Role**: ERA5 is a historical reanalysis reference product, not an instantaneous real-time station observation feed.
3. **Statutory Positioning**: This system does **not** replace NWP dynamical simulations, does **not** generate weather forecasts, and does **not** overwrite official bulletins issued by IMD / NCMRWF.
