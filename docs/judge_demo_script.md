# SIH26079: 3–5 Minute Judge Live Demonstration Script

**Application URL**: [http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/)  
**Presenter Roles**: Presenter (Voice/Narrator) & Navigator (Interacting with the live UI)  
**Total Target Duration**: 4 minutes 30 seconds  

---

## 0:00–0:30 | Introduction & Problem Framing
**Navigator Action**: Display the Web Dashboard main screen at [http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/).

**Presenter**:
"Respected judges, welcome to the SIH26079 platform: AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts, developed for the Ministry of Earth Sciences and NCMRWF. 

Every day, supercomputers run Numerical Weather Prediction (NWP) models to tell us what weather is expected across India. But in non-linear fluid dynamics, forecasts occasionally suffer catastrophic errors—known as forecast busts. 

Our system does not attempt to replace NWP or predict weather independently. Instead, we have created an auxiliary forecast-reliability layer that evaluates incoming NWP forecasts to answer one critical question: *What is the probability that this specific forecast will experience a major forecast bust?*"

---

## 0:30–1:15 | Step A–E Live Forecast Workflow (Pune Day 4)
**Navigator Action**:
1. In **Step A**, click the **Pune** preset button (Latitude: 18.52°N, Longitude: 73.86°E).
2. In **Step B**, click **Day 4 (96h)**.
3. In **Step C**, select **Precipitation**.
4. Observe **Step D** update with live operational ECMWF IFS guidance, and **Step E** display the prediction cards.

**Presenter**:
"Let us demonstrate the live operational workflow. In Step A, we select Pune Observatory. In Step B, we choose a 4-day forecast horizon—96 hours out. In Step C, we focus on Precipitation.

Notice Step D: the system immediately ingests live operational ECMWF IFS guidance for this valid time. And in Step E, our calibrated LightGBM model evaluates the atmospheric and dynamical features. 

Here we see the calibrated bust probability is 0.1%, yielding an operational reliability score of 99.9% and a 🟢 LOW risk badge. The forecast for Pune at Day 4 is stable under these synoptic conditions."

---

## 1:15–1:45 | Model Explainability via TreeSHAP
**Navigator Action**: Scroll to the TreeSHAP insight box and the **Top Contributing Model Features** list.

**Presenter**:
"Black-box machine learning is unacceptable in operational meteorology. That is why our engine executes local TreeSHAP attribution for every prediction. 

Notice the factors listed here: TreeSHAP isolates the top risk amplifiers—such as solar position phase—and the top risk mitigators, such as moderate surface wind speeds (8.9 m/s) and geographical baselines. 

Importantly, we make a strict scientific distinction: TreeSHAP identifies which model inputs influenced the AI prediction; it explains the machine learning model, rather than claiming proof of physical atmospheric causality."

---

## 1:45–2:20 | High-Risk "What-If" Sensitivity Analysis
**Navigator Action**:
1. In Step A, click **Kolkata**.
2. In Step B, select **Day 3 (72h)**.
3. In Step C, select **Wind**.
4. In Step D, click **"What-If / Scenario"** toggle: enter Forecast Wind = `28.7 m/s` and Ensemble Spread = `4.0σ`.
5. Observe Step E turn to **🟠 HIGH** risk.

**Presenter**:
"To demonstrate how the system responds to anomalous synoptic conditions, let us run a controlled sensitivity analysis for Kolkata at Day 3. 

Suppose operational ensemble guidance indicates extreme gale-force winds of 28.7 m/s with a high ensemble spread of 4.0 standard deviations. 

Notice that the model immediately updates: the bust probability climbs to 62.0%, elevating the risk level to 🟠 HIGH. The TreeSHAP engine instantly highlights the elevated ensemble spread and extreme wind gradient as the primary risk amplifiers driving this warning. 

We clearly distinguish: this is an exploratory What-If scenario, distinct from the calm live forecast we inspected in Pune."

---

## 2:20–2:50 | Geographic Spatial Risk Map (India Synoptic Domain)
**Navigator Action**: Click on the **"2. Spatial Risk Map (India)"** tab in the navigation bar.

**Presenter**:
"Forecast risk is not isolated to a single point. Moving to Tab 2, the platform renders a model-generated spatial visualization across 25 synoptic stations covering India's diverse climatic zones—from the Western Ghats and Indo-Gangetic plains to coastal cyclonic corridors. 

Each station marker reflects its model-estimated bust probability for the chosen lead time and variable. A forecaster can click on any station—such as Mumbai or New Delhi—to inspect localized bust likelihood. 

As scientifically documented, this map visualizes model-estimated forecast vulnerability under the scenario; it does not claim to depict observed future weather."

---

## 3:30–4:00 | Decoupled Historical Forecast Verification
**Navigator Action**: Click on the **"3. Forecast vs Reference"** tab.

**Presenter**:
"Now we come to the most critical scientific innovation: **temporal decoupling**. 

At forecast issuance time $T_0$, ground truth does not exist. In Tab 3, we demonstrate post-event verification. After the valid time passes, the platform ingests Copernicus ERA5 atmospheric reanalysis as the historical reference. 

Looking at the verification table, you see the exact forecast issued at $T_0$, the realized ERA5 reference value, the absolute error, and the operational threshold scaled dynamically by lead time:
$$\text{Threshold}(\tau) = \text{Base} \times [1 + 0.12 \times (\tau - 24)/24]$$

This proves that forecast issuance and verification are strictly separated, eliminating data leakage."

---

## 4:00–4:30 | Scientific Integrity, Authentic Data & Limitations
**Navigator Action**: Click on the **"4. Model Registry & Audit"** tab.

**Presenter**:
"To conclude, our platform is built on verified, reproducible science:
1. **Authentic Data**: Trained on `dataset_real_v002.csv`—37,800 genuine NWP–ERA5 records.
2. **Chronological Splitting**: Chronologically isolated test partition from January 2026, achieving a PR-AUC of 0.2682 (+0.1732 over baseline), Brier score of 0.0450, and ECE of 0.0257.
3. **Anti-Leakage Gate**: Nine forbidden keywords strictly prevent future reference information from entering $T_0$ features.
4. **Honest Limitations**: While operational inference supports Day 10, historical training data extends through Day 7 due to public archive limits. We refused to fabricate Days 8–10 training data.

Thank you, esteemed judges. We are now ready for your questions."
