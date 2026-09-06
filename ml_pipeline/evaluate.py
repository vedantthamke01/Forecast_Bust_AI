"""
Scientific Evaluation Metrics Suite for Meteorological Bust Prediction.
Computes comprehensive diagnostic metrics tailored for rare event detection:
PR-AUC, ROC-AUC, Brier score, ECE, F1-Score, Precision, Recall, and Confusion Matrix.
"""
from typing import Dict, Any
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix
)
from ml_pipeline.calibration import calculate_brier_score, calculate_ece, get_calibration_curve_points


def evaluate_model_performance(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> Dict[str, Any]:
    """Calculates all key operational metrics for a candidate or production model."""
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    y_prob = np.asarray(y_prob, dtype=float)

    # Classification Metrics
    acc = round(float(accuracy_score(y_true, y_pred)), 4)
    prec = round(float(precision_score(y_true, y_pred, zero_division=0)), 4)
    rec = round(float(recall_score(y_true, y_pred, zero_division=0)), 4)
    f1 = round(float(f1_score(y_true, y_pred, zero_division=0)), 4)

    # Probability & Ranking Metrics
    try:
        roc_auc = round(float(roc_auc_score(y_true, y_prob)), 4)
    except Exception:
        roc_auc = 0.5

    try:
        pr_auc = round(float(average_precision_score(y_true, y_prob)), 4)
    except Exception:
        pr_auc = 0.0

    # Calibration Metrics
    brier = calculate_brier_score(y_true, y_prob)
    ece = calculate_ece(y_true, y_prob)
    curve = get_calibration_curve_points(y_true, y_prob)

    # Confusion Matrix
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = [int(x) for x in cm.ravel()] if cm.size == 4 else [0, 0, 0, 0]

    return {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "brier_score": brier,
        "expected_calibration_error": ece,
        "confusion_matrix": {
            "true_negatives": tn,
            "false_positives": fp,
            "false_negatives": fn,
            "true_positives": tp
        },
        "reliability_curve": curve
    }
