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
