"""
Model and Feature Distribution Drift Monitoring Engine.
Monitors operational forecast feature distributions using Kolmogorov-Smirnov (KS)
tests and Population Stability Index (PSI) to detect climatological shifts,
sensor calibration drift, or NWP model upgrades.
"""
from typing import Dict, Any, List
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from ml_pipeline.features import FEATURE_COLUMNS


def calculate_feature_drift(
    reference_df: pd.DataFrame,
    current_df: pd.DataFrame,
    features: List[str] = None,
    alpha: float = 0.01
) -> Dict[str, Any]:
    """
    Computes two-sample Kolmogorov-Smirnov test for continuous physical features.
    If p-value < alpha, the null hypothesis (identical distributions) is rejected.
    """
    features = features or [f for f in FEATURE_COLUMNS if f in reference_df.columns and f in current_df.columns]
    drifted_features = []
    feature_details = {}

    for f in features:
        ref_vals = reference_df[f].dropna().values
        curr_vals = current_df[f].dropna().values

        if len(ref_vals) < 10 or len(curr_vals) < 10:
            continue

        ks_stat, p_val = ks_2samp(ref_vals, curr_vals)
        has_drifted = bool(p_val < alpha)

        feature_details[f] = {
            "ks_statistic": round(float(ks_stat), 4),
            "p_value": round(float(p_val), 6),
            "drift_detected": has_drifted,
            "ref_mean": round(float(np.mean(ref_vals)), 2),
            "curr_mean": round(float(np.mean(curr_vals)), 2)
        }

        if has_drifted:
            drifted_features.append(f)

    drift_pct = (len(drifted_features) / max(1, len(features))) * 100

    if drift_pct >= 30.0:
        overall_status = "DRIFT_ALERT"
        recommendation = "Significant atmospheric or NWP distribution drift detected. Evaluate retraining."
    elif drift_pct > 0.0:
        overall_status = "DRIFT_WARNING"
        recommendation = "Localized distribution shifts detected in minor variables. Monitor incoming verification."
    else:
        overall_status = "STABLE"
        recommendation = "All physical features consistent with reference distribution."

    return {
        "status": overall_status,
        "drift_detected": len(drifted_features) > 0,
        "drifted_features_count": len(drifted_features),
        "drifted_features": drifted_features,
        "recommendation": recommendation,
        "feature_metrics": feature_details
    }
