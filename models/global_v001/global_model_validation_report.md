# Scientific Model Validation Report: Global Forecast Bust AI Model (global_v001)

**SIH Problem Statement:** SIH26079 – AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts  
**Experiment Identifier:** `global_v001`  
**Evaluation Date:** 2026-09-17T15:06:31.021266  
**Provenance / Pipeline Status:** Fully Validated & Reproducible  

---

## Executive Summary & Core Claim

> [!IMPORTANT]
> **Defensible Meteorological Claim:**
> "Globally trained and geographically evaluated."  
> The system estimates the empirical probability of a medium-range NWP forecast bust according to the standardized multi-variable bust criterion. It does not predict future weather or provide individual-case certainty; it provides verified, calibrated forecast reliability probabilities across diverse global climate regimes.

| Metric / Dimension | Old Regional Model (`model_real_v002`) | New Global Model (`global_v001`) | Variance ($\Delta$) |
| :--- | :--- | :--- | :--- |
| **Training Records** | ~37,800 (15 Indian synoptic stations) | **378,000** (150 global stations) | +340,200 (+900%) |
| **Validation Records**| 5,670 (Regional) | **63,000** (25 global stations) | +57,330 |
| **Geographic Holdout**| 3 stations (1,890 records) | **25 unseen stations (63,000 records)** | +61,110 |
| **Geographic Coverage**| 1 Country, 1 Sub-continent | **88 Countries, 6 Continents** | Global expansion |
| **Holdout ROC-AUC** | N/A | **0.7771** | Robust discrimination |
| **Holdout AP (PR-AUC)** | N/A | **0.3811** | Rare event detection |
| **Holdout Brier Score** | N/A | **0.0852** | Well-calibrated |
| **Holdout ECE** | N/A | **0.0132** | Low calibration error |
| **Frozen Test ROC-AUC** | 0.9040 | **0.8922** | -0.0118 |
| **Frozen Test AP (PR-AUC)** | 0.5547 | **0.6082** | +0.0535 |
| **Frozen Test Brier Score** | 0.0686 | **0.0688** | +0.0002 |
| **Frozen Test ECE** | 0.0185 | **0.0191** | +0.0006 |

---

## 1. Dataset Partitioning & Anti-Leakage Audit

- **Total Global Dataset:** 504,000 authentic historical NWP-ERA5 records (`dataset_global_v001.csv`).
- **Station Split:**
  - **Train:** 150 stations (378,000 records, 75.0%)
  - **Validation:** 25 stations (63,000 records, 12.5%)
  - **Geographic Holdout:** 25 stations (63,000 records, 12.5%) — **100% unseen during all training & tuning**
- **Existing Frozen Test Benchmark:** `dataset_real_v002.csv` (37,800 records) — **STRICTLY PRESERVED & UNCHANGED**.
- **Anti-Leakage Audit:** **PASS**. All 21 features strictly evaluated at initialization $T_0$. Zero forbidden substring violations. Imputation medians computed strictly on Train.

---

## 2. Baseline Model Comparison (Evaluated on Validation Set)

Before evaluating LightGBM, standard meteorological baselines were established on the exact same validation population:

| Model Architecture | ROC-AUC | PR-AUC (AP) | Brier Score | ECE | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Climatology Baseline** | 0.5000 | 0.1066 | 0.0952 | 0.0033 | Constant empirical training prevalence (378,000 samples) |
| **Lead-Time Only** | 0.5654 | 0.1271 | 0.0947 | 0.0033 | Single-variable Logistic Regression |
| **Logistic Regression (Standardized)** | 0.6963 | 0.2781 | 0.2344 | 0.3678 | Linear decision boundary with balanced weighting |
| **Random Forest** | 0.7854 | 0.3898 | 0.1784 | 0.3017 | 100 trees, depth 12, min leaf 30 |
| **LightGBM (Default)** | 0.7926 | 0.3630 | 0.0820 | 0.0174 | Baseline tree boosting |

---

## 3. LightGBM Hyperparameter Selection

Controlled exploration across tree capacity, regularization, and learning rates on Train/Val:

| Candidate | Leaves | Depth | LR | Min Child | Subsample | Colsample | Reg $\alpha / \lambda$ | Val ROC-AUC | Val AP |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Config_A_Baseline** | 31 | 6 | 0.05 | 50 | 0.8 | 0.8 | 0.0 / 0.0 | 0.7896 | 0.3745 |
| **Config_B_DeepTree** | 63 | 8 | 0.03 | 80 | 0.85 | 0.75 | 0.1 / 0.5 | 0.7931 | 0.3629 |
| **Config_C_Regularized** | 24 | 5 | 0.03 | 120 | 0.75 | 0.7 | 0.5 / 1.0 | 0.7898 | 0.3786 |
| **Config_D_HighCapacity** | 45 | 7 | 0.04 | 100 | 0.8 | 0.8 | 0.2 / 0.8 | 0.7910 | 0.3675 |

**Selected Architecture:** `ISOTONIC` calibrated `Config_C_Regularized` based on composite discrimination and logloss minimization.

---

## 4. Probability Calibration Analysis

Evaluated raw model vs. Platt Scaling (Sigmoid), Isotonic Regression, and Beta Calibration strictly on validation data:

| Calibration Method | Validation Brier Score | Expected Calibration Error (ECE) | Validation AP | Selection Decision |
| :--- | :--- | :--- | :--- | :--- |
| **Raw Probabilities** | 0.0808 | 0.0161 | 0.3786 | Uncalibrated baseline |
| **Platt Scaling (Sigmoid)** | 0.0814 | 0.0140 | 0.3784 | Parametric logistic scaling |
| **Isotonic Regression** | 0.0804 | 0.0013 | 0.3743 | Non-parametric monotonic binning |
| **Beta Calibration** | 0.0806 | 0.0047 | 0.3782 | Kull et al. (2017) beta distribution |

**Winning Calibrator:** `ISOTONIC` (Selected and locked prior to any holdout or frozen test evaluation).

---

## 5. Unseen Geographic Holdout Performance (25 Stations, 63,000 Records)

Evaluated on 25 completely unseen global synoptic stations across 6 continents:

### Overall Geographic Holdout
- **Total Records:** 63,000
- **Bust Prevalence:** 11.40% (7,185 events)
- **ROC-AUC:** 0.7771
- **Average Precision (AP):** 0.3811
- **Brier Score:** 0.0852
- **ECE:** 0.0132
- **Confusion Matrix:** TN=55,165, FP=650, FN=5,865, TP=1,320

### Performance by Continent
| Continent | Stations | Records | Bust Prevalence | ROC-AUC | AP | Brier Score | ECE |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Asia** | 5 | 12,600 | 15.07% | 0.7896 | 0.4962 | 0.1006 | 0.0271 |
| **Europe** | 5 | 12,600 | 9.33% | 0.8377 | 0.4976 | 0.0628 | 0.0254 |
| **Africa** | 4 | 10,080 | 13.91% | 0.8005 | 0.4033 | 0.1002 | 0.0299 |
| **North America** | 5 | 12,600 | 12.41% | 0.7760 | 0.3302 | 0.0977 | 0.0371 |
| **South America** | 4 | 10,080 | 8.07% | 0.7418 | 0.1883 | 0.0699 | 0.0102 |
| **Oceania** | 2 | 5,040 | 6.57% | 0.6356 | 0.1082 | 0.0725 | 0.0825 |

### Performance by Lead Horizon (Days 1–7)
| Lead Horizon | Day | Sample Size ($N$) | Bust Prevalence | Mean Pred Prob | Observed Bust Rate | ROC-AUC | AP | Brier Score | ECE |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **24h** | Day 1 | 9,000 | 15.76% | 14.51% | 15.76% | 0.7499 | 0.4375 | 0.1110 | 0.0212 |
| **48h** | Day 2 | 9,000 | 14.34% | 13.21% | 14.34% | 0.7713 | 0.4334 | 0.1013 | 0.0129 |
| **72h** | Day 3 | 9,000 | 11.94% | 11.36% | 11.94% | 0.7618 | 0.3872 | 0.0889 | 0.0136 |
| **96h** | Day 4 | 9,000 | 10.29% | 10.17% | 10.29% | 0.7741 | 0.3657 | 0.0784 | 0.0130 |
| **120h** | Day 5 | 9,000 | 10.13% | 9.64% | 10.13% | 0.7830 | 0.3529 | 0.0777 | 0.0107 |
| **144h** | Day 6 | 9,000 | 8.60% | 8.99% | 8.60% | 0.7901 | 0.3469 | 0.0670 | 0.0128 |
| **168h** | Day 7 | 9,000 | 8.77% | 9.05% | 8.77% | 0.7845 | 0.2864 | 0.0724 | 0.0196 |

### Performance by Köppen Macro Climate Regime
| Climate Category | Sample Count ($N$) | Bust Prevalence | ROC-AUC | AP | Brier Score | ECE |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Tropical** | 10,080 | 9.72% | 0.8736 | 0.4800 | 0.0694 | 0.0387 |
| **Temperate** | 30,240 | 7.85% | 0.7576 | 0.3071 | 0.0637 | 0.0189 |
| **Continental** | 12,600 | 10.44% | 0.6665 | 0.1950 | 0.0914 | 0.0292 |
| **Arid / Desert** | 7,560 | 22.55% | 0.7671 | 0.5550 | 0.1372 | 0.0220 |
| **Polar / Alpine** | 2,520 | 32.14% | 0.6489 | 0.4791 | 0.2201 | 0.1309 |

### Performance by Geographic Setting
| Geographic Setting | Sample Count ($N$) | Bust Prevalence | ROC-AUC | AP | Brier Score | ECE |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Coastal** | 20,160 | 13.12% | 0.8102 | 0.4720 | 0.0890 | 0.0174 |
| **Inland** | 20,160 | 9.11% | 0.6997 | 0.2111 | 0.0781 | 0.0146 |
| **Mountain / Alpine** | 15,120 | 11.78% | 0.7918 | 0.3141 | 0.0916 | 0.0251 |
| **Island** | 5,040 | 6.94% | 0.6687 | 0.1158 | 0.0729 | 0.0623 |
| **Desert / Arid** | 2,520 | 22.78% | 0.9038 | 0.7652 | 0.0990 | 0.0657 |

---

## 6. Empirical Reliability Decile Breakdown

Analysis across 8 standardized probability risk bins on the unseen geographic holdout:

| Probability Bin | Samples ($N$) | Busts | Mean Pred Prob | Observed Bust Rate | Calibration Gap | Wilson 95% CI | Support Flag |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **0-10%** | 36,433 | 1,638 | 3.87% | 4.50% | 0.63% | [4.3%, 4.7%] | `NORMAL` |
| **10-20%** | 17,133 | 2,396 | 12.60% | 13.98% | 1.38% | [13.5%, 14.5%] | `NORMAL` |
| **20-30%** | 4,351 | 942 | 23.68% | 21.65% | 2.03% | [20.4%, 22.9%] | `NORMAL` |
| **30-40%** | 2,134 | 530 | 31.64% | 24.84% | 6.80% | [23.1%, 26.7%] | `NORMAL` |
| **40-50%** | 979 | 359 | 42.02% | 36.67% | 5.35% | [33.7%, 39.7%] | `NORMAL` |
| **50-60%** | 1,059 | 598 | 54.31% | 56.47% | 2.16% | [53.5%, 59.4%] | `NORMAL` |
| **60-70%** | 533 | 360 | 62.22% | 67.54% | 5.32% | [63.5%, 71.4%] | `NORMAL` |
| **70-100%** | 378 | 362 | 87.24% | 95.77% | 8.53% | [93.2%, 97.4%] | `NORMAL` |

---

## 7. Frozen Test Evaluation (`dataset_real_v002.csv`)

> [!CAUTION]
> The frozen test was evaluated strictly post-hoc with zero retraining, parameter tuning, or calibration fitting.

| Operational Metric | Old Model (`model_real_v002`) | New Global Model (`global_v001`) | Variance ($\Delta$) | Scientific Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **ROC-AUC** | 0.9040 | 0.8922 | -0.0118 | Discrimination across authentic Indian cases |
| **Average Precision (AP)** | 0.5547 | 0.6082 | +0.0535 | Precision-recall skill on rare bust events |
| **Brier Score** | 0.0686 | 0.0688 | +0.0002 | Probability accuracy (Comparable) |
| **Expected Calibration (ECE)**| 0.0185 | 0.0191 | +0.0006 | Calibration deviation across risk bins |

---

## 8. SHAP Explainability Verification

- **Explainer Architecture:** `shap.TreeExplainer`
- **Methodological Disclaimer:** Attribution values are defined strictly as **statistical model contributions**, not physical atmospheric causes.

### Top Global Statistical Predictors
- **1. `forecast_wind`**: 0.6483 mean |SHAP| impact
- **2. `latitude`**: 0.5040 mean |SHAP| impact
- **3. `forecast_humidity`**: 0.3710 mean |SHAP| impact
- **4. `lead_hours`**: 0.1940 mean |SHAP| impact
- **5. `forecast_pressure`**: 0.1020 mean |SHAP| impact
- **6. `temp_dew_depression_proxy`**: 0.0814 mean |SHAP| impact
- **7. `forecast_temperature`**: 0.0774 mean |SHAP| impact
- **8. `forecast_cloud_cover`**: 0.0671 mean |SHAP| impact
- **9. `ensemble_spread`**: 0.0612 mean |SHAP| impact
- **10. `climate_regime_code`**: 0.0573 mean |SHAP| impact

### Representative Instance Explanation
> "Overall bust risk is LOW (13.1%). The forecast is currently assessed as highly reliable. The main factors increasing the estimated risk are Extended Forecast Horizon (Day 1), Latitude Coordinate (26.9°N). The strongest mitigating factors are Forecasted 10m Wind Speed (8.3 m/s), climate_regime_code (1.0)."

---

## 9. Scientific Limitations & Deployment Status

1. **Horizon Limit:** Scientifically validated strictly for Days 1–7 (24h–168h). Extended horizons (Days 8–30) remain strictly experimental.
2. **Production Separation:** `global_v001` is saved independently in `models/global_v001/`. Production endpoints and active serving models remain completely untouched until formal acceptance.
3. **Reproducibility:** Seed 42, deterministic training split stored in `models/global_v001/station_split.json`.

---
*Report automatically compiled by Forecast Bust AI Scientific Verification Engine.*
