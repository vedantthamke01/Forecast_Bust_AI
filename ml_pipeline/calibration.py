"""
Probability Calibration and Verification Metrics Engine.
Ensures that predicted bust probabilities (0% to 100%) correspond to empirical
frequencies. Implements Isotonic Regression, Platt Scaling (Sigmoid),
Brier Score calculation, and Expected Calibration Error (ECE).
"""
from typing import Dict, Any, Tuple, Optional, List
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import brier_score_loss
from sklearn.model_selection import KFold


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


class BetaCalibrator:
    """
    Beta Calibration for Probabilistic Classifiers (Kull et al., 2017).
    Models probability distributions on the unit interval using beta distributions,
    fitting logistic regression on features [ln(p), -ln(1-p)].
    Particularly well-suited for skewed weather events and extreme forecast busts.
    """
    def __init__(self, eps: float = 1e-6):
        self.eps = eps
        self.lr = LogisticRegression(C=1.0, solver="lbfgs", max_iter=500)
        self.is_fitted = False

    def _transform(self, probs: np.ndarray) -> np.ndarray:
        p = np.clip(probs, self.eps, 1.0 - self.eps)
        feat1 = np.log(p)
        feat2 = -np.log(1.0 - p)
        return np.column_stack([feat1, feat2])

    def fit(self, probs: np.ndarray, y: np.ndarray):
        X_trans = self._transform(probs)
        self.lr.fit(X_trans, y)
        self.is_fitted = True
        return self

    def predict_proba(self, probs: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("BetaCalibrator must be fitted before predict_proba.")
        X_trans = self._transform(probs)
        return self.lr.predict_proba(X_trans)[:, 1]


class ModelCalibrator:
    def __init__(self, base_estimator, method: str = "isotonic"):
        self.base_estimator = base_estimator
        self.method = method.lower().strip()
        if self.method == "isotonic":
            self.calibrator = IsotonicRegression(out_of_bounds="clip")
        elif self.method in ["beta", "beta_calibration"]:
            self.calibrator = BetaCalibrator()
        else:  # sigmoid / platt
            self.calibrator = LogisticRegression(C=1.0)
        self.is_fitted = False

    def fit(self, X_val: np.ndarray, y_val: np.ndarray):
        raw_probs = self.base_estimator.predict_proba(X_val)[:, 1]
        if self.method == "isotonic":
            self.calibrator.fit(raw_probs, y_val)
        elif self.method in ["beta", "beta_calibration"]:
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
        elif self.method in ["beta", "beta_calibration"]:
            calibrated_p1 = self.calibrator.predict_proba(raw_probs)
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


def compare_calibration_methods(
    base_estimator,
    X_val: np.ndarray,
    y_val: np.ndarray,
    X_test: Optional[np.ndarray] = None,
    y_test: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Compares Isotonic, Sigmoid (Platt), and Beta calibration strictly on validation data.
    Uses out-of-fold cross-validation on the validation set to eliminate in-sample step-fitting bias.
    Identifies the best calibration method by minimizing out-of-fold Brier Score and ECE.
    """
    methods = ["isotonic", "sigmoid", "beta"]
    val_results = {}
    fitted_calibrators = {}

    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    for m in methods:
        oof_probs = np.zeros(len(y_val))
        for fit_idx, eval_idx in kf.split(X_val):
            X_fit, y_fit = X_val[fit_idx], y_val[fit_idx]
            X_eval = X_val[eval_idx]
            cal_fold = ModelCalibrator(base_estimator, method=m).fit(X_fit, y_fit)
            oof_probs[eval_idx] = cal_fold.predict_proba(X_eval)[:, 1]

        brier = calculate_brier_score(y_val, oof_probs)
        ece = calculate_ece(y_val, oof_probs)
        val_results[m] = {
            "brier_score": brier,
            "expected_calibration_error": ece,
            "composite_score": round(brier + ece, 4)
        }
        # Fit final calibrator on the entire validation set for downstream inference
        full_cal = ModelCalibrator(base_estimator, method=m).fit(X_val, y_val)
        fitted_calibrators[m] = full_cal

    # Select best calibration method on validation set
    best_method = min(val_results.keys(), key=lambda m: val_results[m]["composite_score"])
    best_calibrator = fitted_calibrators[best_method]

    output = {
        "validation_comparison": val_results,
        "selected_method": best_method,
        "best_calibrator": best_calibrator
    }

    # If test data provided for out-of-sample evaluation
    if X_test is not None and y_test is not None:
        test_results = {}
        for m in methods:
            cal = fitted_calibrators[m]
            test_probs = cal.predict_proba(X_test)[:, 1]
            test_results[m] = {
                "brier_score": calculate_brier_score(y_test, test_probs),
                "expected_calibration_error": calculate_ece(y_test, test_probs),
                "reliability_curve": get_calibration_curve_points(y_test, test_probs)
            }
        output["test_evaluation"] = test_results

    return output


def evaluate_stratified_calibration(
    df_eval: pd.DataFrame,
    y_true: np.ndarray,
    y_prob: np.ndarray,
    group_col: str
) -> Dict[str, Dict[str, Any]]:
    """
    Evaluates Brier Score, ECE, sample count, and observed bust rate across distinct
    meteorological groups (e.g. lead_time_group or climate_regime).
    """
    stratified_metrics = {}
    if group_col not in df_eval.columns:
        return stratified_metrics

    groups = df_eval[group_col].dropna().unique()
    for g in sorted(groups):
        idx = (df_eval[group_col] == g).to_numpy()
        sub_y = y_true[idx]
        sub_p = y_prob[idx]

        if len(sub_y) >= 10:
            stratified_metrics[str(g)] = {
                "sample_count": int(len(sub_y)),
                "observed_bust_rate_pct": round(float(np.mean(sub_y)) * 100, 2),
                "mean_predicted_prob_pct": round(float(np.mean(sub_p)) * 100, 2),
                "brier_score": calculate_brier_score(sub_y, sub_p),
                "expected_calibration_error": calculate_ece(sub_y, sub_p)
            }
        else:
            stratified_metrics[str(g)] = {
                "sample_count": int(len(sub_y)),
                "status": "Insufficient samples (< 10) for robust calibration scoring"
            }

    return stratified_metrics
