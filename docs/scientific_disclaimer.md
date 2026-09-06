# Scientific Disclaimer & Operational Scope

**System**: AI-Based Forecast Bust Detection Platform  
**Target Organization**: Ministry of Earth Sciences (MoES) / National Centre for Medium Range Weather Forecasting (NCMRWF)

---

## 1. Operational Mandate & Scope

The system provides a **forecast-reliability layer alongside existing NWP forecasts**.

- **Complementary Positioning**: NWP provides the expected weather state; the ML system estimates the probability that the forecast may experience a significant forecast error.
- **No Substitute Forecasts**: The system does not replace NWP, does not replace IMD or NCMRWF, does not produce a better weather forecast than NWP, and does not predict weather independently of NWP.
- **Auxiliary Analysis**: It analyzes forecast parameters, ensemble dispersion, run revision consistency, and atmospheric dynamics proxies to estimate the risk of an anomalous forecast failure.
- **Under NO circumstances does this system generate substitute meteorological forecasts or overwrite official weather advisories.**

## 2. Statutory Authority & Intended Users

- **Statutory Authority**: Official weather forecasts, severe weather alerts, cyclone tracks, heavy rainfall red/orange alerts, and heatwave warnings across the Republic of India are under the statutory mandate of the **India Meteorological Department (IMD)** and the **National Centre for Medium Range Weather Forecasting (NCMRWF)**.
- **Intended Users**: Potential users include meteorological forecast analysts, forecast operations teams, researchers, disaster-management decision-support systems, and downstream applications that need forecast reliability information.
- **Adoption Status**: The project does not claim operational deployment or institutional adoption by IMD or NCMRWF.

## 3. Probabilistic Interpretation & Calibration

- **Model Estimate**: The Bust Probability $P(\text{Bust} = 1)$ is a calibrated model estimate. A low model probability (e.g. 0.7%) indicates the model estimates a low bust probability for the supplied forecast conditions; it is not physical proof of atmospheric stability, nor is probability a guarantee of certainty.
- **Calibration Meaning**: A calibrated probability is intended to correspond to observed event frequency over sufficiently large groups of predictions with similar predicted probabilities.
- **Directional Neutrality**: A high bust probability does not indicate which alternative direction the weather will deviate toward (e.g. higher vs lower precipitation), but indicates that the operational NWP solution has low confidence and elevated vulnerability to significant error.

