# Scientific Definition of Forecast Busts

**SIH26079**: AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts  
**NCMRWF / Ministry of Earth Sciences**

---

## 1. Forecast Verification & Bust Detection Lifecycle

A forecast bust is an extreme forecast failure where Numerical Weather Prediction (NWP) guidance deviates substantially from post-event reference data at matching valid times:

$$\text{Forecast Initialized at } T_0 \xrightarrow{\text{Lead } \tau} \text{Reference Data at } T_0 + \tau \xrightarrow{} \text{Absolute Error } |NWP - \text{Ref}| \xrightarrow{\text{Threshold}(\tau)} \text{Bust Label}$$

1. **Forecast Issuance ($T_0$)**: NWP values, ensemble spread, run revision, and temporal features are available. Future reference data does not exist.
2. **Matching Valid Time ($T_0 + \tau$)**: Event valid time occurs. Post-event reference data (Copernicus ERA5 reanalysis) becomes available.
3. **Absolute Forecast Error**: Computed across meteorological variables:
   $$\text{Error}_{\text{precip}} = |P_{\text{nwp}} - P_{\text{ref}}|$$
   $$\text{Error}_{\text{temp}} = |T_{\text{nwp}} - T_{\text{ref}}|$$
   $$\text{Error}_{\text{wind}} = |W_{\text{nwp}} - W_{\text{ref}}|$$
4. **Lead-Dependent Threshold Evaluation**: Error is evaluated against lead-horizon scaled thresholds $\text{Threshold}(\tau)$.
5. **Bust Label & Severity**: Labeled as binary event ($\text{is\_bust} \in \{0, 1\}$) and categorized into severity bands.

*Note: These thresholds are project labeling thresholds established for model training and empirical verification. They are not universal meteorological laws or statutory limits.*

---

## 2. Lead-Time Dependent Dynamic Thresholding

Forecast uncertainty increases with lead horizon $\tau \in [24, 240]$ hours. In the primary labeling implementation (`data_pipeline/labeler.py`), thresholds scale with lead time above Day 1 (24 hours):

$$\text{Threshold}(\tau) = \text{Base\_Threshold} \times \left(1.0 + 0.12 \times \max\left(0, \frac{\tau - 24}{24}\right)\right)$$

### Applied Project Thresholds by Lead Time

| Lead Horizon ($\tau$) | Forecast Day | Precipitation Threshold | Temperature Threshold | Wind Speed Threshold |
| :---: | :---: | :---: | :---: | :---: |
| **24h** | Day 1 | 25.00 mm | 4.00°C | 8.50 m/s |
| **48h** | Day 2 | 28.00 mm | 4.48°C | 9.52 m/s |
| **72h** | Day 3 | 31.00 mm | 4.96°C | 10.54 m/s |
| **96h** | Day 4 | 34.00 mm | 5.44°C | 11.56 m/s |
| **120h** | Day 5 | 37.00 mm | 5.92°C | 12.58 m/s |
| **144h** | Day 6 | 40.00 mm | 6.40°C | 13.60 m/s |
| **168h** | Day 7 | 43.00 mm | 6.88°C | 14.62 m/s |

---

## 3. Severity Classification Logic

Severity is calculated from the maximum ratio of absolute forecast error to the applicable operational threshold:

$$\text{Ratio}_{\max} = \max\left(\frac{\text{Error}_{\text{precip}}}{\text{Threshold}_{\text{precip}}(\tau)}, \frac{\text{Error}_{\text{temp}}}{\text{Threshold}_{\text{temp}}(\tau)}, \frac{\text{Error}_{\text{wind}}}{\text{Threshold}_{\text{wind}}(\tau)}\right)$$

- **`NONE`**: $\text{is\_bust} = 0$ ($\text{Ratio}_{\max} < 1.0$)
- **`MODERATE`**: $\text{is\_bust} = 1$ and $1.0 \le \text{Ratio}_{\max} < 1.5$
- **`SEVERE`**: $\text{is\_bust} = 1$ and $1.5 \le \text{Ratio}_{\max} < 2.0$
- **`EXTREME`**: $\text{is\_bust} = 1$ and $\text{Ratio}_{\max} \ge 2.0$

---

## 4. Compound Bust Logic

Under multi-variable compound labeling:
$$\text{Bust}_{\text{compound}} = 1 \iff (\text{Bust}_{\text{precip}} = 1) \lor (\text{Bust}_{\text{temp}} = 1 \land \text{Bust}_{\text{wind}} = 1)$$

Under standard synoptic labeling:
$$\text{Bust} = 1 \iff (\text{Bust}_{\text{precip}} = 1) \lor (\text{Bust}_{\text{temp}} = 1) \lor (\text{Bust}_{\text{wind}} = 1)$$

