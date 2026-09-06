# Scientific Definition of Forecast Busts

**SIH26079**: AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts  
**NCMRWF / Ministry of Earth Sciences**

---

## 1. What Constitutes a Forecast Bust?

In operational meteorological science, a **forecast bust** refers to an extreme forecast failure where the Numerical Weather Prediction (NWP) model deviates substantially from realized ground truth observations or reanalysis (ERA5). 

Unlike routine incremental bias (e.g. 1.5°C temperature error or 4 mm light drizzle discrepancy), forecast busts are characterized by:
1. **High Operational Consequence**: Missing an extreme synoptic or mesoscale convective event (e.g., flash flood, intense thunderstorm, severe cold/heat wave) or issuing false alarms for benign conditions.
2. **Horizon Dependency**: Errors that are intolerable at Day 2 (48 hours) might be within standard ensemble spread boundaries at Day 8 (192 hours).

---

## 2. Configurable Labeling Strategies

Our system provides four mathematically sound labeling methods. Every labeled record explicitly preserves its labeling strategy in its metadata:

### Strategy 1: Absolute Error Thresholding
A binary bust flag is raised if the absolute error between NWP forecast $\hat{y}$ and reference observation $y$ exceeds an operational threshold:

$$\text{Error}_{\text{abs}} = |\hat{y} - y|$$

- **Precipitation (24h accumulation)**: $\text{Threshold}_{\text{rain}} = 25.0\text{ mm}$ (or $50.0\text{ mm}$ for severe event)
- **Temperature ($2m$)**: $\text{Threshold}_{\text{temp}} = 4.0^{\circ}\text{C}$
- **Wind Speed ($10m$)**: $\text{Threshold}_{\text{wind}} = 8.5\text{ m/s}$ ($\sim 30\text{ km/h}$)
- **Mean Sea Level Pressure (MSLP)**: $\text{Threshold}_{\text{press}} = 5.0\text{ hPa}$

### Strategy 2: Climatological / Percentile-Based Thresholding
Because variance varies drastically across geography (e.g., Western Ghats vs Thar Desert) and seasons (SW Monsoon vs Winter), a threshold can be defined dynamically:

$$\text{Bust} = 1 \iff |\hat{y} - y| > P_{95}(\text{Historical Errors for Sub-Division and Season})$$

### Strategy 3: Lead-Time Dependent Dynamic Thresholding
Forecast uncertainty grows non-linearly with forecast lead time $\tau \in [24, 240]$ hours. An operational threshold is scaled with lead time:

$$\text{Threshold}(\tau) = \text{Threshold}_0 \times \left(1 + \gamma \times \frac{\tau - 24}{24}\right)$$

Where $\gamma \approx 0.10$ to $0.15$ per 24 hours of lead time. Under this regime, a 20 mm rainfall error constitutes a severe bust at 48 hours (Day 2), but is recognized as standard variance at 216 hours (Day 9).

### Strategy 4: Multi-Variable Compound Bust
In many high-impact situations, no single variable alone reaches extreme thresholds, but the compound state is disastrous (e.g., moderate rainfall coupled with gale-force winds and rapid pressure plunge).
- Bust flagged if:
  $$\text{Bust}_{\text{compound}} = 1 \iff (\text{Bust}_{\text{rain}} = 1) \lor (\text{Bust}_{\text{temp}} = 1 \land \text{Bust}_{\text{wind}} = 1) \lor (\text{Bust}_{\text{press}} = 1 \land \text{Bust}_{\text{wind}} = 1)$$
