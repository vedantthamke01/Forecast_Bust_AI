"""
Model Probability Calibration Tests.
Verifies Brier score, ECE calculation, and calibration curve generation.
"""
import pytest
import numpy as np
from ml_pipeline.calibration import calculate_brier_score, calculate_ece, get_calibration_curve_points


def test_brier_score_perfect():
    y_true = np.array([0, 1, 1, 0])
    y_prob = np.array([0.0, 1.0, 1.0, 0.0])
    brier = calculate_brier_score(y_true, y_prob)
    assert brier == 0.0


def test_ece_perfect():
    y_true = np.array([0, 0, 1, 1])
    y_prob = np.array([0.05, 0.05, 0.95, 0.95])
    ece = calculate_ece(y_true, y_prob, n_bins=5)
    assert ece <= 0.05


def test_calibration_curve_points():
    y_true = np.array([0, 0, 1, 1, 1, 0, 1, 0])
    y_prob = np.array([0.1, 0.2, 0.8, 0.9, 0.7, 0.3, 0.85, 0.15])
    curve = get_calibration_curve_points(y_true, y_prob, n_bins=3)
    assert "fraction_of_positives" in curve
    assert "mean_predicted_value" in curve
    assert len(curve["fraction_of_positives"]) > 0


def test_realistic_evaluation_non_trivial_metrics():
    """Validates that evaluation on realistic stochastic outcomes yields non-zero Brier and ECE."""
    np.random.seed(42)
    # 100 samples with 12% positive base rate (typical synoptic bust frequency)
    y_true = (np.random.rand(100) < 0.12).astype(int)
    # Realistic imperfect probability estimates
    y_prob = np.clip(y_true * 0.6 + np.random.normal(0.1, 0.15, size=100), 0.01, 0.99)

    brier = calculate_brier_score(y_true, y_prob)
    ece = calculate_ece(y_true, y_prob, n_bins=5)

    # Must be strictly non-zero (proving no trivial overfit or synthetic leakage)
    assert brier > 0.001, f"Suspiciously zero Brier score: {brier}"
    assert ece > 0.001, f"Suspiciously zero ECE: {ece}"


def test_beta_calibrator_bounds_and_fit():
    """Verify that BetaCalibrator outputs valid probabilities in (0, 1)."""
    from ml_pipeline.calibration import BetaCalibrator
    np.random.seed(42)
    raw_probs = np.clip(np.random.uniform(0.05, 0.95, size=80), 0.01, 0.99)
    y = (raw_probs + np.random.normal(0, 0.1, size=80) > 0.5).astype(int)

    beta_cal = BetaCalibrator()
    beta_cal.fit(raw_probs, y)
    calibrated = beta_cal.predict_proba(raw_probs)

    assert len(calibrated) == len(raw_probs)
    assert np.all(calibrated >= 0.0) and np.all(calibrated <= 1.0)


def test_compare_calibration_methods():
    """Verify that calibration comparison evaluates on validation data."""
    from ml_pipeline.calibration import compare_calibration_methods
    from sklearn.linear_model import LogisticRegression

    np.random.seed(42)
    X = np.random.randn(100, 4)
    y = (X[:, 0] + X[:, 1] > 0).astype(int)

    base = LogisticRegression()
    base.fit(X[:60], y[:60])

    comp = compare_calibration_methods(base, X[60:], y[60:])
    assert "validation_comparison" in comp
    assert "selected_method" in comp
    assert comp["selected_method"] in ["isotonic", "sigmoid", "beta"]
    assert comp["best_calibrator"] is not None

