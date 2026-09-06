"""
SHAP-Based Model Explainability Engine.
SHAP provides a game-theoretic additive feature-attribution framework used to identify
which model inputs most influenced an individual prediction. It explains the model prediction,
not the physical atmosphere itself.
Translates mathematical SHAP coefficients into human-interpretable descriptions
of model input features.
"""
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
import shap
from ml_pipeline.features import FEATURE_COLUMNS

FEATURE_DESCRIPTIONS = {
    "lead_hours": "Extended Forecast Horizon (Day {val})",
    "forecast_temperature": "Forecasted 2m Temperature ({val}°C)",
    "forecast_precipitation": "Forecasted 24h Precipitation ({val} mm)",
    "forecast_wind": "Forecasted 10m Wind Speed ({val} m/s)",
    "forecast_pressure": "Mean Sea Level Pressure ({val} hPa)",
    "forecast_humidity": "Forecasted Relative Humidity ({val}%)",
    "forecast_cloud_cover": "Forecasted Cloud Cover ({val}%)",
    "ensemble_spread": "NWP Ensemble Spread / Dispersion ({val})",
    "run_revision": "Run Revision / Consistency Signal ({val})",
    "sin_day_of_year": "Seasonal Day-of-Year Phase",
    "cos_day_of_year": "Climatological Solar Position",
    "month": "Seasonal Month ({val})",
    "is_monsoon_season": "Southwest Monsoon Active Phase",
    "pressure_anomaly": "Baroclinic Pressure Anomaly ({val} hPa)",
    "temp_dew_depression_proxy": "Dewpoint Depression Proxy ({val}°C)",
    "latitude": "Latitude Coordinate ({val}°N)",
    "longitude": "Longitude Coordinate ({val}°E)"
}


class MeteorologicalExplainer:
    def __init__(self, model, feature_names: List[str] = None):
        self.model = model
        self.feature_names = feature_names or FEATURE_COLUMNS
        try:
            self.explainer = shap.TreeExplainer(model)
        except Exception:
            # Fallback if model is calibrated wrapper or linear
            self.explainer = None

    def explain_instance(
        self,
        x_vector: pd.DataFrame,
        top_k: int = 5,
        risk_level: Optional[str] = None,
        bust_prob: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Computes local SHAP values for a single prediction instance.
        Returns top risk amplifiers (+) and risk mitigators (-).
        """
        if self.explainer is not None:
            try:
                shap_values = self.explainer.shap_values(x_vector)
                # TreeExplainer on binary LightGBM may return 1D array or list [class0, class1]
                if isinstance(shap_values, list):
                    vals = np.array(shap_values[1][0])
                elif len(shap_values.shape) == 2:
                    vals = np.array(shap_values[0])
                else:
                    vals = np.array(shap_values)
            except Exception:
                vals = self._heuristic_feature_impacts(x_vector)
        else:
            vals = self._heuristic_feature_impacts(x_vector)

        factors = []
        for i, col in enumerate(self.feature_names):
            if i >= len(vals):
                break
            shap_val = float(vals[i])
            actual_val = float(x_vector[col].iloc[0]) if col in x_vector.columns else 0.0

            # Format human-readable atmospheric description
            desc_template = FEATURE_DESCRIPTIONS.get(col, f"{col} ({{val}})")
            if "{val}" in desc_template:
                if col == "lead_hours":
                    day_num = int(actual_val // 24)
                    desc = desc_template.format(val=day_num)
                else:
                    desc = desc_template.format(val=round(actual_val, 1))
            else:
                desc = desc_template

            factors.append({
                "feature": col,
                "description": desc,
                "actual_value": round(actual_val, 2),
                "shap_value": round(shap_val, 4),
                "impact": "AMPLIFIER" if shap_val > 0 else "MITIGATOR"
            })

        # Sort by absolute SHAP magnitude
        factors.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

        top_amplifiers = [f for f in factors if f["impact"] == "AMPLIFIER"][:top_k]
        top_mitigators = [f for f in factors if f["impact"] == "MITIGATOR"][:top_k]

        return {
            "all_factors": factors,
            "top_amplifiers": top_amplifiers,
            "top_mitigators": top_mitigators,
            "summary_text": self._generate_scientific_summary(
                top_amplifiers, top_mitigators, risk_level=risk_level, bust_prob=bust_prob
            )
        }

    def _heuristic_feature_impacts(self, x_vector: pd.DataFrame) -> np.ndarray:
        """Fallback attribution based on standardized physical variances."""
        impacts = np.zeros(len(self.feature_names))
        for i, col in enumerate(self.feature_names):
            if col in x_vector.columns:
                val = float(x_vector[col].iloc[0])
                if col == "ensemble_spread":
                    impacts[i] = (val - 1.0) * 0.4
                elif col == "lead_hours":
                    impacts[i] = (val - 48.0) / 240.0 * 0.3
                elif col == "run_revision":
                    impacts[i] = val * 0.25
                elif col == "forecast_precipitation":
                    impacts[i] = (val - 20.0) / 100.0 * 0.2
        return impacts

    def _generate_scientific_summary(
        self,
        amplifiers: List[dict],
        mitigators: List[dict],
        risk_level: Optional[str] = None,
        bust_prob: Optional[float] = None
    ) -> str:
        return generate_scientific_summary(
            amplifiers=amplifiers,
            mitigators=mitigators,
            risk_level=risk_level,
            bust_prob=bust_prob
        )


def generate_scientific_summary(
    amplifiers: List[Dict[str, Any]],
    mitigators: List[Dict[str, Any]],
    risk_level: Optional[str] = None,
    bust_prob: Optional[float] = None
) -> str:
    """
    Generates a natural-language summary strictly consistent with the final
    calibrated bust probability and assigned risk level.
    
    Distinguishes overall forecast risk from individual model feature contributions,
    avoiding unwarranted claims of physical causality or describing LOW-risk forecasts
    as having 'elevated' risk.
    """
    # 1. Normalize risk level and determine default if absent
    norm_risk = str(risk_level).upper().strip() if risk_level is not None else None
    if norm_risk is None:
        if bust_prob is not None:
            if bust_prob < 0.25:
                norm_risk = "LOW"
            elif bust_prob < 0.50:
                norm_risk = "MODERATE"
            elif bust_prob < 0.75:
                norm_risk = "HIGH"
            else:
                norm_risk = "VERY HIGH"
        else:
            norm_risk = "LOW"

    # Format percentage string if probability provided
    pct_str = f" ({round(float(bust_prob) * 100, 1)}%)" if bust_prob is not None else ""

    # 2. Overall forecast reliability assessment
    if norm_risk == "LOW":
        lead = f"Overall bust risk is LOW{pct_str}. The forecast is currently assessed as highly reliable."
    elif norm_risk in ["MODERATE", "MEDIUM"]:
        lead = f"Overall bust risk is MODERATE{pct_str}. The forecast has some reliability concerns."
    elif norm_risk == "HIGH":
        lead = f"Overall bust risk is HIGH{pct_str}. The forecast shows elevated risk of a significant forecast error."
    elif norm_risk == "VERY HIGH":
        lead = f"Overall bust risk is VERY HIGH{pct_str}. The forecast shows severe risk of a significant forecast error."
    else:
        lead = f"Overall bust risk is {norm_risk}{pct_str}."

    # 3. Model feature contributions (amplifying and mitigating factors)
    amp_sentence = ""
    if amplifiers:
        amp_names = [a.get("description") or a.get("feature", "Atmospheric factor") for a in amplifiers[:2]]
        if len(amp_names) == 1:
            amp_sentence = f"The main factor increasing the estimated risk is {amp_names[0]}."
        else:
            amp_sentence = f"The main factors increasing the estimated risk are {', '.join(amp_names)}."

    mit_sentence = ""
    if mitigators:
        mit_names = [m.get("description") or m.get("feature", "Atmospheric factor") for m in mitigators[:2]]
        if len(mit_names) == 1:
            mit_sentence = f"The strongest mitigating factor is {mit_names[0]}."
        else:
            mit_sentence = f"The strongest mitigating factors are {', '.join(mit_names)}."

    # 4. Construct final multi-sentence summary
    parts = [lead]
    if amp_sentence:
        parts.append(amp_sentence)
    if mit_sentence:
        parts.append(mit_sentence)
    if not amp_sentence and not mit_sentence:
        parts.append("Atmospheric indicators and model dispersion are within baseline climatological ranges.")

    return " ".join(parts)
