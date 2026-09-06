"""
Comprehensive Machine Learning Training, Calibration, and Registration Pipeline.
Executes:
1. Schema & dataset loading with Provenance Tracking (REAL vs SYNTHETIC)
2. Dynamic Chronological Splitting (Train -> Validation -> Unseen Test Holdout)
3. Strict Feature Engineering & Anti-Leakage Audit
4. Baseline Model Training (Calibrated Logistic Regression)
5. Production Model Training (Tuned LightGBM Classifier)
6. Probability Calibration (Isotonic Regression)
7. Operational Metrics Computation (PR-AUC, ROC-AUC, Brier score, ECE, Recall, Precision)
8. Artifact Serialization and Model Registry Management
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


def temporal_split(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, str]]:
    """
    Performs dynamic chronological data splitting based on actual dates in dataset.
    Ensures zero temporal leakage:
    - Train Set: Oldest 70% of chronological timeline
    - Validation Set: Intermediate 15% of timeline
    - Test Holdout: Newest 15% of timeline (strictly unseen future)
    """
    df = df.copy()
    time_col = "valid_time" if "valid_time" in df.columns else ("initialization_time" if "initialization_time" in df.columns else None)

    if time_col:
        df["_dt_sort"] = pd.to_datetime(df[time_col])
        df = df.sort_values("_dt_sort").reset_index(drop=True)

        unique_dates = df["_dt_sort"].dt.date.drop_duplicates().tolist()
        num_dates = len(unique_dates)

        if num_dates >= 3:
            train_idx = int(num_dates * 0.70)
            val_idx = int(num_dates * 0.85)

            train_cutoff = unique_dates[train_idx]
            val_cutoff = unique_dates[val_idx]

            df_train = df[df["_dt_sort"].dt.date < train_cutoff].copy()
            df_val = df[(df["_dt_sort"].dt.date >= train_cutoff) & (df["_dt_sort"].dt.date < val_cutoff)].copy()
            df_test = df[df["_dt_sort"].dt.date >= val_cutoff].copy()
        else:
            n = len(df)
            df_train = df.iloc[:int(n * 0.70)].copy()
            df_val = df.iloc[int(n * 0.70):int(n * 0.85)].copy()
            df_test = df.iloc[int(n * 0.85):].copy()

        df_train.drop(columns=["_dt_sort"], errors="ignore", inplace=True)
        df_val.drop(columns=["_dt_sort"], errors="ignore", inplace=True)
        df_test.drop(columns=["_dt_sort"], errors="ignore", inplace=True)
    else:
        n = len(df)
        df_train = df.iloc[:int(n * 0.70)].copy()
        df_val = df.iloc[int(n * 0.70):int(n * 0.85)].copy()
        df_test = df.iloc[int(n * 0.85):].copy()

    # Safety fallback if any partition is empty
    if len(df_val) == 0 or len(df_test) == 0:
        n = len(df)
        df_train = df.iloc[:int(n * 0.70)].copy()
        df_val = df.iloc[int(n * 0.70):int(n * 0.85)].copy()
        df_test = df.iloc[int(n * 0.85):].copy()

    split_ranges = {
        "train_period": f"{df_train[time_col].min()} to {df_train[time_col].max()}" if time_col else "Chronological 70%",
        "val_period": f"{df_val[time_col].min()} to {df_val[time_col].max()}" if time_col else "Chronological 15%",
        "test_period": f"{df_test[time_col].min()} to {df_test[time_col].max()}" if time_col else "Chronological 15%"
    }

    return df_train, df_val, df_test, split_ranges


def train_pipeline(
    dataset_path: str = None,
    model_version: str = None,
    dataset_version: str = "dataset_real_v001"
):
    print("\n==================================================")
    print("[*] METEOROLOGICAL FORECAST BUST ML TRAINING PIPELINE")
    print("==================================================")

    if not dataset_path:
        # Prefer real dataset if present, fallback to available training CSV
        if os.path.exists("datasets/training/dataset_real_v001.csv"):
            dataset_path = "datasets/training/dataset_real_v001.csv"
            dataset_version = "dataset_real_v001"
        else:
            csv_files = glob.glob("datasets/training/*.csv")
            if not csv_files:
                raise FileNotFoundError("No labeled dataset found in datasets/training. Run prepare_real first.")
            dataset_path = csv_files[-1]

    print(f"[+] Loading Dataset: {dataset_path}")
    df = pd.read_csv(dataset_path)
    total_records = len(df)
    bust_records = int(df["is_bust"].sum())
    data_type = str(df["data_type"].iloc[0]) if "data_type" in df.columns else ("REAL" if "real" in dataset_path.lower() else "SYNTHETIC")
    print(f"    Total Samples: {total_records:,} (Busts: {bust_records} = {bust_records/total_records*100:.1f}%)")
    print(f"    Data Provenance: {data_type}")

    # 1. Chronological Split
    print("\n[+] Applying Dynamic Chronological Train/Val/Test Split...")
    df_train, df_val, df_test, split_ranges = temporal_split(df)
    print(f"    Train Period:      {split_ranges['train_period']} ({len(df_train):,} samples)")
    print(f"    Validation Period: {split_ranges['val_period']} ({len(df_val):,} samples)")
    print(f"    Test Holdout:      {split_ranges['test_period']} ({len(df_test):,} samples)")

    # 2. Extract Features & Anti-Leakage Gate
    print("\n[+] Extracting Features & Running Anti-Leakage Gate...")
    X_train, y_train = extract_features(df_train, is_training=True)
    X_val, y_val = extract_features(df_val, is_training=True)
    X_test, y_test = extract_features(df_test, is_training=True)
    print(f"    Feature Dimensions: {X_train.shape[1]} physical features: {list(X_train.columns)}")

    # 3. Train Baseline (Calibrated Logistic Regression)
    print("\n[+] Training Baseline Model (Standardized Logistic Regression)...")
    pos_count = max(1, sum(y_train))
    neg_count = len(y_train) - pos_count
    scale_pos = neg_count / pos_count

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
        n_estimators=300,
        learning_rate=0.03,
        max_depth=5,
        num_leaves=24,
        scale_pos_weight=scale_pos,
        random_state=42,
        verbose=-1
    )
    lgb_model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        callbacks=[lgb.early_stopping(stopping_rounds=30, verbose=False)]
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
    print(f" Data Provenance:             {data_type}")
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
        prefix = "model_real_v" if data_type == "REAL" else "model_v"
        os.makedirs("models", exist_ok=True)
        existing_models = [d for d in os.listdir("models") if d.startswith(prefix)]
        next_num = len(existing_models) + 1
        model_version = f"{prefix}{next_num:03d}"

    model_dir = os.path.join("models", model_version)
    os.makedirs(model_dir, exist_ok=True)

    # Save artifacts
    model_artifact = {
        "model_version": model_version,
        "dataset_version": dataset_version,
        "data_type": data_type,
        "algorithm": "LightGBM + Isotonic Calibration",
        "raw_model": lgb_model,
        "calibrated_model": calibrator,
        "features": FEATURE_COLUMNS,
        "metrics": test_metrics,
        "split_ranges": split_ranges,
        "created_at": datetime.utcnow().isoformat()
    }
    artifact_path = os.path.join(model_dir, "model_bundle.joblib")
    joblib.dump(model_artifact, artifact_path)

    # Save metadata JSON
    meta_path = os.path.join(model_dir, "metadata.json")
    metadata = {
        "model_version": model_version,
        "dataset_version": dataset_version,
        "data_type": data_type,
        "training_period": split_ranges["train_period"],
        "validation_period": split_ranges["val_period"],
        "test_period": split_ranges["test_period"],
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

    # Promotion gate: must have meaningful skill above random chance and good calibration
    meets_gate = (
        test_metrics["pr_auc"] >= 0.20 and
        test_metrics["roc_auc"] >= 0.60 and
        test_metrics["brier_score"] <= 0.30
    )

    if meets_gate:
        metadata["status"] = "PRODUCTION"
        registry["production_model"] = model_version
        print(f"[+] MODEL ACCEPTANCE GATE: PASSED! Model {model_version} PROMOTED to PRODUCTION.")
    else:
        print(f"[!] MODEL ACCEPTANCE GATE: Criteria not met. Model {model_version} registered as CANDIDATE.")

    registry[model_version] = metadata
    with open(registry_file, "w") as f:
        json.dump(registry, f, indent=2)

    print(f"[+] Model bundle persisted: {artifact_path}")
    print(f"[+] Model metadata updated: {registry_file}\n")
    return metadata


def main():
    parser = argparse.ArgumentParser(description="Forecast Bust Prediction ML Training Pipeline")
    parser.add_argument("--dataset", type=str, default=None)
    parser.add_argument("--version", type=str, default=None)
    parser.add_argument("--dataset-version", type=str, default="dataset_real_v001")
    args = parser.parse_args()
    train_pipeline(args.dataset, args.version, args.dataset_version)


if __name__ == "__main__":
    main()
