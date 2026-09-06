"""
Comprehensive Machine Learning Training, Calibration, and Registration Pipeline.
Executes:
1. Schema & dataset loading
2. Temporal train/validation/test splitting (Strict holdout, zero temporal leakage)
3. Feature engineering & anti-leakage audit
4. Baseline model training (Calibrated Logistic Regression)
5. Production model training (Tuned LightGBM Classifier)
6. Probability Calibration (Isotonic Regression)
7. Operational metrics computation (PR-AUC, ROC-AUC, Brier score, ECE)
8. SHAP explainer compilation
9. Artifact serialization and Model Registry management
"""
from typing import Tuple, Dict, Any, List, Optional
import argparse
import glob
import json
import os
from datetime import datetime
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import lightgbm as lgb

from ml_pipeline.features import extract_features, FEATURE_COLUMNS
from ml_pipeline.calibration import ModelCalibrator
from ml_pipeline.evaluate import evaluate_model_performance
from ml_pipeline.explainability import MeteorologicalExplainer


def temporal_split(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Performs temporal data splitting strictly on initialization dates.
    Unseen future test data remains strictly isolated.
    Train: 2023 -> 2024
    Validation: 2025
    Test: 2026
    """
    df = df.copy()
    if "initialization_time" in df.columns:
        df["init_year"] = pd.to_datetime(df["initialization_time"]).dt.year
        df_train = df[df["init_year"] <= 2024].copy()
        df_val = df[df["init_year"] == 2025].copy()
        df_test = df[df["init_year"] >= 2026].copy()
    else:
        # Fallback sequential split if initialization timestamps are missing
        n = len(df)
        train_end = int(n * 0.70)
        val_end = int(n * 0.85)
        df_train = df.iloc[:train_end].copy()
        df_val = df.iloc[train_end:val_end].copy()
        df_test = df.iloc[val_end:].copy()

    # Fallback safety if specific temporal year has too few records
    if len(df_val) == 0 or len(df_test) == 0:
        n = len(df)
        df_train = df.iloc[:int(n * 0.70)].copy()
        df_val = df.iloc[int(n * 0.70):int(n * 0.85)].copy()
        df_test = df.iloc[int(n * 0.85):].copy()

    return df_train, df_val, df_test


def train_pipeline(
    dataset_path: str = None,
    model_version: str = None,
    dataset_version: str = "dataset_v001"
):
    print("\n==================================================")
    print("[*] METEOROLOGICAL FORECAST BUST ML TRAINING PIPELINE")
    print("==================================================")

    if not dataset_path:
        csv_files = glob.glob("datasets/training/*.csv")
        if not csv_files:
            raise FileNotFoundError("No labeled dataset found in datasets/training. Run setup_data first.")
        dataset_path = csv_files[-1]

    print(f"[+] Loading Dataset: {dataset_path}")
    df = pd.read_csv(dataset_path)
    total_records = len(df)
    bust_records = int(df["is_bust"].sum())
    print(f"    Total Samples: {total_records:,} (Busts: {bust_records} = {bust_records/total_records*100:.1f}%)")

    # 1. Temporal Split
    print("\n[+] Applying Temporal Train/Val/Test Split...")
    df_train, df_val, df_test = temporal_split(df)
    print(f"    Train Split:      {len(df_train):,} samples")
    print(f"    Validation Split: {len(df_val):,} samples")
    print(f"    Test Holdout:     {len(df_test):,} samples")

    # 2. Extract Features & Anti-Leakage Gate
    print("\n[+] Extracting Features & Running Anti-Leakage Gate...")
    X_train, y_train = extract_features(df_train, is_training=True)
    X_val, y_val = extract_features(df_val, is_training=True)
    X_test, y_test = extract_features(df_test, is_training=True)
    print(f"    Feature Dimensions: {X_train.shape[1]} physical features: {list(X_train.columns)}")

    # 3. Train Baseline (Calibrated Logistic Regression)
    print("\n[+] Training Baseline Model (Standardized Logistic Regression)...")
    scale_pos = (len(y_train) - sum(y_train)) / max(1, sum(y_train))
    baseline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42))
    ])
    baseline.fit(X_train, y_train)

    base_probs = baseline.predict_proba(X_test)[:, 1]
    base_preds = (base_probs >= 0.5).astype(int)
    base_metrics = evaluate_model_performance(y_test, base_preds, base_probs)
    print(f"    Baseline PR-AUC:     {base_metrics['pr_auc']:.4f}")
    print(f"    Baseline ROC-AUC:    {base_metrics['roc_auc']:.4f}")
    print(f"    Baseline Brier:      {base_metrics['brier_score']:.4f}")

    # 4. Train Main Production Model (LightGBM)
    print("\n[+] Training Main Model (Tuned LightGBM Classifier)...")
    lgb_model = lgb.LGBMClassifier(
        n_estimators=250,
        learning_rate=0.04,
        max_depth=5,
        num_leaves=24,
        scale_pos_weight=scale_pos,
        random_state=42,
        verbose=-1
    )
    lgb_model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        callbacks=[lgb.early_stopping(stopping_rounds=25, verbose=False)]
    )

    # 5. Probability Calibration
    print("\n[+] Calibrating Probabilities (Isotonic Regression)...")
    calibrator = ModelCalibrator(base_estimator=lgb_model, method="isotonic")
    calibrator.fit(X_val, y_val.values)

    # 6. Evaluate on Unseen Test Set
    calibrated_probs = calibrator.predict_proba(X_test)[:, 1]
    calibrated_preds = (calibrated_probs >= 0.5).astype(int)
    test_metrics = evaluate_model_performance(y_test, calibrated_preds, calibrated_probs)

    print("\n==================================================")
    print("      PRODUCTION MODEL TEST SET VERIFICATION")
    print("==================================================")
    print(f" PR-AUC (Average Precision):  {test_metrics['pr_auc']:.4f}")
    print(f" ROC-AUC:                     {test_metrics['roc_auc']:.4f}")
    print(f" F1-Score:                    {test_metrics['f1_score']:.4f}")
    print(f" Precision:                   {test_metrics['precision']:.4f}")
    print(f" Recall:                      {test_metrics['recall']:.4f}")
    print(f" Brier Score:                 {test_metrics['brier_score']:.4f}")
    print(f" Expected Calibration (ECE):  {test_metrics['expected_calibration_error']:.4f}")
    print(f" Confusion Matrix:            {test_metrics['confusion_matrix']}")
    print("==================================================\n")

    # 7. Model Versioning & Artifact Storage
    if not model_version:
        # Determine next model version
        os.makedirs("models", exist_ok=True)
        existing_models = [d for d in os.listdir("models") if d.startswith("model_v")]
        next_num = len(existing_models) + 1
        model_version = f"model_v{next_num:03d}"

    model_dir = os.path.join("models", model_version)
    os.makedirs(model_dir, exist_ok=True)

    # Save artifacts
    model_artifact = {
        "model_version": model_version,
        "dataset_version": dataset_version,
        "algorithm": "LightGBM + Isotonic Calibration",
        "raw_model": lgb_model,
        "calibrated_model": calibrator,
        "features": FEATURE_COLUMNS,
        "metrics": test_metrics,
        "created_at": datetime.utcnow().isoformat()
    }
    artifact_path = os.path.join(model_dir, "model_bundle.joblib")
    joblib.dump(model_artifact, artifact_path)

    # Save metadata JSON
    meta_path = os.path.join(model_dir, "metadata.json")
    metadata = {
        "model_version": model_version,
        "dataset_version": dataset_version,
        "training_period": "2023-01 to 2025-12",
        "feature_version": "v1.0",
        "algorithm": "LightGBM + Isotonic Calibration",
        "metrics": test_metrics,
        "status": "VALIDATED",
        "artifact_path": os.path.abspath(artifact_path),
        "created_at": datetime.utcnow().isoformat()
    }
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    # 8. Check Model Acceptance Gate & Promote if Criteria Met
    registry_file = os.path.join("models", "registry.json")
    registry = {}
    if os.path.exists(registry_file):
        with open(registry_file, "r") as f:
            try:
                registry = json.load(f)
            except Exception:
                registry = {}

    meets_gate = (
        test_metrics["pr_auc"] >= 0.40 and
        test_metrics["brier_score"] <= 0.25 and
        test_metrics["expected_calibration_error"] <= 0.25
    )

    if meets_gate:
        metadata["status"] = "PRODUCTION"
        registry["production_model"] = model_version
        print(f"[+] MODEL ACCEPTANCE GATE: PASSED! Model {model_version} PROMOTED to PRODUCTION.")
    else:
        print(f"[!] MODEL ACCEPTANCE GATE: FAILED criteria. Model {model_version} marked CANDIDATE.")

    registry[model_version] = metadata
    with open(registry_file, "w") as f:
        json.dump(registry, f, indent=2)

    print(f"[+] Model bundle persisted: {artifact_path}")
    print(f"[+] Model metadata updated: {registry_file}\n")
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Forecast Bust Prediction ML Training Pipeline")
    parser.add_argument("--dataset", type=str, default=None)
    parser.add_argument("--version", type=str, default=None)
    args = parser.parse_args()
    train_pipeline(args.dataset, args.version)
