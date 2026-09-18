"""
Operational Forecast Bust Verification Service.
Enforces strict temporal separation between:
1. Forecast Initialization Time T0 (where Bust Probability is predicted)
2. Valid Time T0 + tau (where ground-truth ERA5/station observation is realized)

Stores and audits:
- forecast_id
- initialization_time & valid_time
- location (lat, lon, station)
- forecast_value
- reference_value (realized post-valid time)
- absolute_error
- operational_threshold_applied
- predicted_bust_probability
- realized_bust_outcome (0 or 1)
- brier_contribution = (predicted_bust_probability - realized_bust_outcome)^2
- model_version
"""
from typing import Dict, Any, List, Optional
import os
import json
import math
from datetime import datetime, timezone
import numpy as np

from ml_pipeline.calibration import calculate_brier_score, calculate_ece
from data_pipeline.labeler import get_lead_time_group


class VerificationService:
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.join("datasets", "metadata", "verification_log.json")
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        self._load_log()

    def _load_log(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    self.records = json.load(f)
            except Exception:
                self.records = []
        else:
            self.records = []

    def _save_log(self):
        with open(self.storage_path, "w") as f:
            json.dump(self.records, f, indent=2)

    def record_t0_prediction(
        self,
        prediction_id: str,
        initialization_time: str,
        valid_time: str,
        latitude: float,
        longitude: float,
        lead_hours: int,
        variable: str,
        forecast_value: float,
        bust_probability: float,
        operational_threshold: float,
        model_version: str = "model_real_v002"
    ) -> Dict[str, Any]:
        """
        Logs prediction event strictly at initialization time T0.
        Status is marked as AWAITING_REALIZATION until valid_time arrives.
        """
        record = {
            "prediction_id": prediction_id,
            "status": "AWAITING_REALIZATION",
            "initialization_time": initialization_time,
            "valid_time": valid_time,
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "lead_hours": lead_hours,
            "lead_time_group": get_lead_time_group(lead_hours),
            "variable": variable.lower().strip(),
            "forecast_value": round(float(forecast_value), 2),
            "bust_probability": round(float(bust_probability), 4),
            "operational_threshold": round(float(operational_threshold), 2),
            "model_version": model_version,
            "reference_value": None,
            "absolute_error": None,
            "realized_bust_outcome": None,
            "brier_contribution": None,
            "verified_at": None
        }
        self.records.append(record)
        self._save_log()
        return record

    def verify_prediction(
        self,
        prediction_id: str,
        reference_value: float,
        reference_source: str = "era5-reanalysis"
    ) -> Optional[Dict[str, Any]]:
        """
        Executes historical verification strictly after valid time has elapsed.
        Calculates authentic error, evaluates bust status, and computes Brier score contribution.
        """
        target = None
        for rec in self.records:
            if rec["prediction_id"] == prediction_id:
                target = rec
                break

        if not target:
            return None

        # Compute realized error
        fc_val = float(target["forecast_value"])
        ref_val = float(reference_value)
        abs_err = round(abs(fc_val - ref_val), 3)
        th = float(target["operational_threshold"])

        # Determine binary bust outcome
        realized_bust = int(abs_err > th)
        prob = float(target["bust_probability"])
        brier_contrib = round((prob - realized_bust) ** 2, 4)

        target["status"] = "VERIFIED"
        target["reference_value"] = ref_val
        target["reference_source"] = reference_source
        target["absolute_error"] = abs_err
        target["realized_bust_outcome"] = realized_bust
        target["brier_contribution"] = brier_contrib
        target["verified_at"] = datetime.now(timezone.utc).isoformat()

        self._save_log()
        return target

    def get_verification_summary(self) -> Dict[str, Any]:
        """
        Aggregates verification performance metrics across all realized forecasts.
        """
        verified_recs = [r for r in self.records if r.get("status") == "VERIFIED"]
        if not verified_recs:
            return {
                "total_logged_predictions": len(self.records),
                "verified_predictions_count": 0,
                "status": "No forecasts have elapsed past valid time for ground-truth verification."
            }

        y_true = np.array([r["realized_bust_outcome"] for r in verified_recs])
        y_prob = np.array([r["bust_probability"] for r in verified_recs])

        overall_brier = calculate_brier_score(y_true, y_prob)
        overall_ece = calculate_ece(y_true, y_prob)
        bust_count = int(np.sum(y_true))
        bust_rate = round(float(np.mean(y_true)) * 100, 2)
        mean_pred = round(float(np.mean(y_prob)) * 100, 2)

        # Stratified by lead time group
        lead_groups = {}
        for r in verified_recs:
            grp = r.get("lead_time_group", "Unknown")
            if grp not in lead_groups:
                lead_groups[grp] = {"y_true": [], "y_prob": []}
            lead_groups[grp]["y_true"].append(r["realized_bust_outcome"])
            lead_groups[grp]["y_prob"].append(r["bust_probability"])

        lead_breakdown = {}
        for grp, vals in lead_groups.items():
            g_true = np.array(vals["y_true"])
            g_prob = np.array(vals["y_prob"])
            lead_breakdown[grp] = {
                "verified_samples": len(g_true),
                "observed_bust_pct": round(float(np.mean(g_true)) * 100, 2),
                "mean_predicted_prob_pct": round(float(np.mean(g_prob)) * 100, 2),
                "brier_score": calculate_brier_score(g_true, g_prob)
            }

        return {
            "total_logged_predictions": len(self.records),
            "verified_predictions_count": len(verified_recs),
            "observed_bust_count": bust_count,
            "observed_bust_rate_pct": bust_rate,
            "mean_predicted_probability_pct": mean_pred,
            "overall_brier_score": overall_brier,
            "overall_expected_calibration_error": overall_ece,
            "lead_time_breakdown": lead_breakdown
        }
