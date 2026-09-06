# SIH26079: 2-Minute Structured Pitch

**Target Delivery Time**: 2 minutes (~280–320 words)  
**Tone**: Technical, Defensible, Authoritative, Scientifically Rigorous  

---

## 0:00–0:20 | The Problem
"Good morning, esteemed judges. Numerical Weather Prediction models like NCUM and ECMWF IFS form the backbone of Indian meteorology. Yet, due to non-linear atmospheric chaos and convective parameterization challenges, medium-range forecasts still suffer from severe, unexpected forecast busts. A 4-day forecast might show clear skies, yet an unexpected synoptic failure produces intense flooding. Today, forecasters have no automated layer estimating how vulnerable an individual medium-range forecast is to failing."

## 0:20–0:45 | The Solution
"To solve SIH26079 for the Ministry of Earth Sciences and NCMRWF, we built an AI-based forecast reliability platform. We do not replace NWP dynamical simulations, and we do not predict raw weather. Instead, our platform acts as an auxiliary confidence layer sitting directly on top of NWP guidance. At forecast issuance time $T_0$, it calculates the calibrated probability that the forecast will suffer a significant forecast error, assigning an operational risk badge from LOW to VERY HIGH."

## 0:45–1:10 | How It Works & Workflow
"The operational workflow is strictly decoupled to prevent future data leakage. At $T_0$, the system ingests live operational ECMWF IFS guidance across Days 3 to 10. Our anti-leakage gate screens the feature vector against nine forbidden reference and error patterns. It computes 17 forecast-time features—including synoptic pressure anomalies, seasonal solar phases, run revision consistency, and ensemble spread—and delivers instant risk predictions, TreeSHAP feature attributions, and a 25-station spatial risk map across India."

## 1:10–1:35 | AI Architecture & Authentic Data
"Under the hood, we trained a tuned LightGBM classifier with Isotonic probability calibration on `dataset_real_v002.csv`, containing 37,800 authentic historical NWP–ERA5 reanalysis pairs across 25 Indian synoptic stations from 2024 to 2026. We use lead-scaled dynamic thresholding that realistically accounts for non-linear error growth with lead time. And with TreeSHAP, we decompose every single prediction into risk amplifiers and mitigators, explaining the model decision process."

## 1:35–1:50 | Verified Results
"Evaluated on a strictly isolated chronological future test set of 7,560 records, our champion model achieved a PR-AUC of 0.2682—an absolute improvement of +0.1732 over baseline. Our ROC-AUC is 0.8756, our Brier calibration score is 0.0450, and Expected Calibration Error is just 0.0257, proving highly reliable probabilistic alignment with sub-10-millisecond inference."

## 1:50–2:00 | Impact and Limitations
"Finally, we maintain scientific honesty: while our live operational inference supports full 10-day horizons, historical training data extends through Day 7 due to public archive limits. We did not fabricate Days 8 to 10 training data. This platform gives forecasters quantitative, interpretable confidence to catch forecast busts before they strike."
