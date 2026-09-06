"""
Probability Calibration and Verification Metrics Engine.
Ensures that predicted bust probabilities (0% to 100%) correspond to empirical
frequencies. Implements Isotonic Regression, Platt Scaling (Sigmoid),
Brier Score calculation, and Expected Calibration Error (ECE).
"""
from typing import Dict, Any, Tuple
import numpy as np
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import brier_score_loss


def calculate_brier_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """Computes mean squared difference between predicted probabilities and actual outcomes."""
    return round(float(brier_score_loss(y_true, y_prob)), 4)


def calculate_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """
    Computes Expected Calibration Error (ECE):
    ECE = sum_{m=1}^M (|B_m| / N) * |acc(B_m) - conf(B_m)|
    """
    bin_limits = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(y_true)

    for i in range(n_bins):
        bin_lower = bin_limits[i]
        bin_upper = bin_limits[i + 1]

        # Find samples in this bin
        if i == n_bins - 1:
            mask = (y_prob >= bin_lower) & (y_prob <= bin_upper)
        else:
            mask = (y_prob >= bin_lower) & (y_prob < bin_upper)

        bin_count = np.sum(mask)
        if bin_count > 0:
            bin_acc = np.mean(y_true[mask])
            bin_conf = np.mean(y_prob[mask])
            ece += (bin_count / n) * abs(bin_acc - bin_conf)

    return round(float(ece), 4)


def get_calibration_curve_points(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> Dict[str, Any]:
    """Generates coordinates for plotting reliability diagrams in UI dashboards."""
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy="uniform")
    return {
        "fraction_of_positives": [round(float(x), 4) for x in prob_true],
        "mean_predicted_value": [round(float(x), 4) for x in prob_pred]
    }


from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression


class ModelCalibrator:
    def __init__(self, base_estimator, method: str = "isotonic"):
        self.base_estimator = base_estimator
        self.method = method
        if method == "isotonic":
            self.calibrator = IsotonicRegression(out_of_bounds="clip")
        else:
            self.calibrator = LogisticRegression(C=1.0)
        self.is_fitted = False

    def fit(self, X_val: np.ndarray, y_val: np.ndarray):
        raw_probs = self.base_estimator.predict_proba(X_val)[:, 1]
        if self.method == "isotonic":
            self.calibrator.fit(raw_probs, y_val)
        else:
            self.calibrator.fit(raw_probs.reshape(-1, 1), y_val)
        self.is_fitted = True
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Calibrator must be fitted before predict_proba.")
        raw_probs = self.base_estimator.predict_proba(X)[:, 1]
        if self.method == "isotonic":
            calibrated_p1 = self.calibrator.predict(raw_probs)
        else:
            calibrated_p1 = self.calibrator.predict_proba(raw_probs.reshape(-1, 1))[:, 1]

        calibrated_p1 = np.clip(calibrated_p1, 0.001, 0.999)
        calibrated_p0 = 1.0 - calibrated_p1
        return np.column_stack([calibrated_p0, calibrated_p1])

    def evaluate_calibration(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        probs = self.predict_proba(X_test)[:, 1]
        brier = calculate_brier_score(y_test, probs)
        ece = calculate_ece(y_test, probs)
        curve = get_calibration_curve_points(y_test, probs)

        return {
            "calibration_method": self.method,
            "brier_score": brier,
            "expected_calibration_error": ece,
            "reliability_curve": curve
        }
