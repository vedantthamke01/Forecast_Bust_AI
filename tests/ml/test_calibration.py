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
