# SIH26079: Comprehensive Judge Q&A Playbook

**Organization**: Ministry of Earth Sciences (MoES) / NCMRWF  
**Target Audience**: Meteorological Experts, ML Engineers, and SIH Evaluation Panel  
**Rule**: Every answer must be technically precise, scientifically defensible, and grounded strictly in the repository's verified implementation.

---

### Q1: What exactly is a forecast bust?
**Answer**: In operational meteorology, a forecast bust is an extreme forecast failure where the Numerical Weather Prediction (NWP) model deviates substantially from realized post-event weather conditions at matching valid times. Unlike routine incremental errors (e.g., 1.5°C temperature difference), busts represent high-impact failures—such as completely missing an extreme convective storm, sudden baroclinic deepening, or issuing false alarms for severe weather. In our system, a bust is formally defined when the absolute error $|NWP - \text{Reference}|$ exceeds a lead-time dependent threshold.

### Q2: Why not simply use ensemble spread?
**Answer**: Ensemble spread measures the standard deviation among perturbed ensemble members, representing internal dynamical dispersion. While valuable, ensemble spread alone is known to suffer from under-dispersion (ensemble spread can remain artificially narrow even when the entire ensemble cluster misses a synoptic shift). Our ML model incorporates ensemble spread as one of 17 input features, combining it with consecutive run jumpiness, baroclinic pressure anomalies, moisture saturation proxies, seasonal solar phases, and geography to provide a more holistic reliability evaluation.

### Q3: Why use Machine Learning for this problem?
**Answer**: NWP models solve deterministic or ensemble fluid-dynamics equations forward in time. However, the relationship between forecast-time dynamical features, terrain, seasonal climatology, and historical model error tendencies is highly non-linear. Machine learning allows us to recognize complex multidimensional patterns that historically preceded anomalous forecast busts, translating high-dimensional NWP guidance into a single, calibrated probability of failure.

### Q4: Why LightGBM?
**Answer**: We selected LightGBM for three objective scientific reasons:
1. **Tabular Meteorological Features**: Decision tree ensembles routinely outperform deep learning on structured tabular data with heterogeneous numerical scales.
2. **Threshold Sensitivity**: Atmospheric physics is dominated by threshold effects (e.g., 100% relative humidity causing condensation, pressure dropping below 1000 hPa). Decision trees naturally partition feature space along sharp thresholds.
3. **Low Latency & Interpretability**: LightGBM provides sub-10 ms inference on standard CPUs and supports exact Shapley value attribution via TreeSHAP.

### Q5: Why not deep neural networks or Transformers?
**Answer**: Medium-range synoptic tabular indicators across 25 stations do not exhibit spatial continuity like raw 2D radar images or sequential language tokens. Neural networks on tabular meteorological features tend to overfit, require extensive compute, and output uncalibrated probabilities. LightGBM provided superior Precision-Recall AUC (0.2682), lower calibration error, and instant CPU execution without requiring GPU clusters.

### Q6: What is your target variable?
**Answer**: The target variable is binary: $\text{is\_bust} \in \{0, 1\}$. It equals 1 if the absolute forecast error $|NWP - ERA5|$ exceeds the dynamic lead-dependent threshold $\text{Threshold}(\tau)$ for the evaluated variable, or satisfies our multi-variable compound bust rule; otherwise, it equals 0.

### Q7: What dataset did you train on?
**Answer**: We trained on `dataset_real_v002.csv`, an authentic dataset of 37,800 spatio-temporally aligned records spanning 25 Indian synoptic stations from July 2024 to January 2026. It combines archived historical NWP forecast runs from Open-Meteo with matching valid-time ERA5 atmospheric reanalysis from the Copernicus Climate Data Store.

### Q8: Is your training data real, or is it synthetic?
**Answer**: It is 100% authentic, real data. The dataset was downloaded directly from open meteorological archives using the Copernicus CDS API and Open-Meteo previous runs endpoints. We do not use synthetic weather generators for our champion model. Data provenance is tracked as `REAL`, and synthetic demo datasets have been formally deprecated.

### Q9: What is ERA5?
**Answer**: ERA5 is the fifth-generation global atmospheric reanalysis produced by the European Centre for Medium-Range Weather Forecasts (ECMWF) via the Copernicus Climate Change Service. It provides hourly, 0.25° gridded estimates of atmospheric conditions globally by combining historical observations with numerical model physics using 4D-Var data assimilation.

### Q10: Why use ERA5 instead of raw station rain gauges?
**Answer**: In this open implementation, ERA5 provides consistent, continuous, quality-controlled atmospheric parameters across all four target variables (rainfall, temperature, wind, and pressure) across the entire Indian domain. However, we explicitly recognize that ERA5 is a reanalysis reference dataset. In an operational NCMRWF deployment, the system can seamlessly ingest IMD automatic weather station (AWS) and rain gauge networks.

### Q11: Is ERA5 ground truth?
**Answer**: Scientifically speaking, no reanalysis product is instantaneous "ground truth." Reanalysis is a model-assimilated historical reference field. We describe ERA5 strictly as a *reference dataset used for historical and post-event verification*, not as an instantaneous real-time observational station feed.

### Q12: How do you prevent data leakage?
**Answer**: Data leakage is prevented through two independent safeguards:
1. **Architectural Decoupling**: Operational predictions at $T_0$ use only features available at issuance time. Reference data is only ingested at valid time $T_0 + \tau$.
2. **Automated Keyword Gate**: The pipeline scans input feature vectors against 9 forbidden substrings (`actual`, `reference`, `observed`, `error`, `ground_truth`, `target`, `label`, `future`, `verification`). Any attempt to pass future reference values immediately triggers a `DataLeakageException`.

### Q13: What information is available at $T_0$?
**Answer**: At initialization time $T_0$, the system accesses: the issued NWP forecast values, forecast lead horizon $\tau$, station latitude, longitude, elevation, seasonal solar position ($\sin/\cos$ day of year), calendar month, monsoon flag, pressure anomaly, moisture saturation proxy, ensemble dispersion spread, and run revision consistency between recent model runs.

### Q14: What happens after $T_0$?
**Answer**: As time progresses, valid time $T_0 + \tau$ arrives. The realized atmospheric state is observed. In our historical pipeline, ERA5 reference data is ingested at this stage to calculate the true absolute error $|NWP - \text{Reference}|$ and establish whether a forecast bust occurred for validation and telemetry logging.

### Q15: How do you define the bust threshold?
**Answer**: Thresholds are lead-time scaled:
$$\text{Threshold}(\tau) = \text{Base\_Threshold} \times \left[1.0 + 0.12 \times \max\left(0, \frac{\tau - 24}{24}\right)\right]$$
Base thresholds at 24 hours are: Precipitation $25.0\text{ mm}$, Temperature $4.0^{\circ}\text{C}$, and Wind Speed $8.5\text{ m/s}$.

### Q16: Why does the bust threshold increase with lead time?
**Answer**: Due to the chaotic nature of the atmosphere, error growth is an intrinsic property of all numerical models. Holding a static 25 mm threshold across 10 days would label routine Day 9 ensemble divergence as busts. The +12% daily scaling allowance mathematically reflects standard error growth curves in medium-range forecasting.

### Q17: Why does historical training only cover through Day 7?
**Answer**: Free, public historical NWP archives (such as Open-Meteo Previous Runs) archive model initializations up to Day 7 (`previous_day1` through `previous_day7`). Historical initializations for Days 8–10 are not retained in public free endpoints. Rather than fabricating synthetic data for Days 8–10, we chose to document this archive limit honestly.

### Q18: How can you support operational inference for Days 8–10 if you only trained through Day 7?
**Answer**: Live operational NWP APIs (ECMWF IFS) provide real-time 10-day forecasts ($240\text{h}$). Our model feature pipeline normalizes lead hours as a continuous numerical feature ($\tau \in [24, 240]$). The model successfully interpolates operational risk through Day 10, while full historical training for Days 8–10 will be unlocked once institutional NCMRWF MARS tape archive data is integrated.

### Q19: What happens if your model's bust prediction is wrong?
**Answer**: Our system outputs a *calibrated probability* and *reliability index*, not a deterministic binary decree. If the model estimates a 20% bust risk and the forecast busts, that is consistent with probabilistic forecasting. Furthermore, all operational predictions are logged alongside eventual valid-time references in the database, allowing forecasters to monitor empirical calibration drift over time.

### Q20: What does TreeSHAP actually tell you?
**Answer**: TreeSHAP computes game-theoretic Shapley values that decompose the difference between the model's prediction and the baseline expected score into additive feature contributions: $f(x) = \phi_0 + \sum \phi_i$. It tells the forecaster which input features (e.g., high ensemble spread, extended lead time) pushed the probability up, and which features (e.g., moderate winds) pulled it down.

### Q21: Does TreeSHAP prove physical atmospheric causality?
**Answer**: **No.** TreeSHAP provides feature attributions explaining the *machine learning model's prediction*. It does not prove physical causality in the real atmosphere. We explicitly document this distinction across all code, API responses, and dashboard headers.

### Q22: Does your system replace NCMRWF?
**Answer**: **No.** NCMRWF is the national centre responsible for developing and running forward dynamical Numerical Weather Prediction models on supercomputers. Our platform operates downstream of NCMRWF's models as an auxiliary reliability evaluation tool.

### Q23: Does your system replace IMD?
**Answer**: **No.** Statutory authority for issuing official weather forecasts, severe weather warnings, and cyclone advisories across the Republic of India rests exclusively with the India Meteorological Department (IMD). Our platform is a decision-support tool for meteorologists.

### Q24: Who would actually use this platform?
**Answer**: Potential users include:
1. Operational forecast analysts at NCMRWF and IMD evaluating medium-range model guidance.
2. Disaster management authorities (NDMA / SDMA) requiring confidence scores to preposition relief supplies.
3. Agriculture and water-resource planners needing medium-range reliability metrics before releasing reservoir storage.

### Q25: What is the single biggest scientific limitation of the current system?
**Answer**: The lack of historical NWP training data for Days 8–10 in open public archives. While operational inference supports Day 10, historical model training currently caps at Day 7 (168 hours).

### Q26: How would access to institutional NCMRWF data improve this platform?
**Answer**: Access to internal NCMRWF archives would provide:
1. Authentic historical runs for Days 8–10 from the NCUM global and ensemble modeling systems.
2. Direct assimilation of physical surface sensor networks (IMD rain gauges and radar feeds).
3. Raw 51-member ensemble member grids, allowing computation of localized ensemble kurtosis and spatial variance.

### Q27: How do you know your probabilities are actually calibrated?
**Answer**: We evaluated calibration on a held-out chronological test set using two rigorous metrics:
1. **Brier Calibration Score**: $0.0450$ (mean squared error of probability predictions).
2. **Expected Calibration Error (ECE)**: $0.0257$ across 10 probability bins.
These low scores prove that predicted probabilities align tightly with observed event frequencies.

### Q28: What happens when the external forecast provider fails or times out?
**Answer**: The system strictly raises an `HTTP 503 (Service Unavailable)` with an explicit diagnostic message. It **never** invents synthetic weather data and **never** falsely attributes fabricated output to ECMWF. Forecasters can also use the manual "What-If" scenario mode to test sensitivity.

### Q29: What makes this more than just a frontend dashboard?
**Answer**: A standard dashboard simply displays raw numerical outputs. SIH26079 implements an intelligent evaluation engine:
- Feature extraction and dynamical proxy calculation.
- Automated anti-leakage protection.
- Calibrated non-linear machine learning inference.
- Local TreeSHAP explainability.
- Kolmogorov-Smirnov statistical distribution drift detection.
- Decoupled post-event verification and error tracking.

### Q30: What would full production deployment require?
**Answer**: Production deployment at NCMRWF would require:
1. Connecting the ingestion pipeline directly to NCMRWF's internal HPC post-processing pipelines (GRIB2/NetCDF feeds).
2. Replacing public ERA5 downloading with real-time IMD GTS/AWS surface observational feeds.
3. Conducting a multi-season shadow verification trial alongside operational meteorologists.
