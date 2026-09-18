"""
Scientific Model Benchmarking & Multi-Horizon Evaluation Engine.
Implements Phase 6 (Model Benchmarking), Phase 7 (Calibration Comparison),
Phase 8 (Global & Lead-Time Holdout Testing), and Phase 9 (Baseline Matrix).

Compares:
1. Climatological Baseline
2. Lead-Time Only Baseline
3. Ensemble Spread Baseline
4. Calibrated Logistic Regression (L2)
5. Random Forest Ensemble
6. Production LightGBM Classifier

Evaluates across:
- Strict Chronological Unseen Test Holdout
- Geographic / Spatial Station Holdout
- Lead-time regimes (Day 1-2, Day 3-5, Day 6-10, Day 11-15, Day 16-20, Day 21-30)
- Macro Climate regimes (Tropical, Arid, Temperate, Continental, Polar/Alpine)
"""
import argparse
import glob
import json
import os
import sys
import time
from typing import Dict, Any, List, Tuple

# Ensure repository root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import precision_recall_curve, roc_auc_score, auc, f1_score, precision_score, recall_score, average_precision_score
import lightgbm as lgb

from ml_pipeline.features import extract_features, FEATURE_COLUMNS, GLOBAL_FEATURE_COLUMNS
from ml_pipeline.calibration import ModelCalibrator, compare_calibration_methods, calculate_brier_score, calculate_ece, get_calibration_curve_points, evaluate_stratified_calibration
from data_pipeline.labeler import get_lead_time_group


class ClimatologicalBaseline:
    """Predicts static historical climatological bust rate."""
    def __init__(self):
        self.climo_prob = 0.10

    def fit(self, X, y):
        self.climo_prob = float(np.mean(y)) if len(y) > 0 else 0.10
        return self

    def predict_proba(self, X) -> np.ndarray:
        n = len(X)
        p1 = np.full(n, self.climo_prob)
        p0 = 1.0 - p1
        return np.column_stack([p0, p1])


class SingleFeatureBaseline:
    """Predicts bust probability using only a single atmospheric/lead predictor."""
    def __init__(self, feature_name: str = "lead_hours"):
        self.feature_name = feature_name
        self.pipe = Pipeline([
            ("scaler", StandardScaler()),
            ("lr", LogisticRegression(C=1.0, solver="lbfgs"))
        ])

    def fit(self, df_X: pd.DataFrame, y: np.ndarray):
        val = df_X[[self.feature_name]].to_numpy() if self.feature_name in df_X.columns else np.zeros((len(df_X), 1))
        self.pipe.fit(val, y)
        return self

    def predict_proba(self, df_X: pd.DataFrame) -> np.ndarray:
        val = df_X[[self.feature_name]].to_numpy() if self.feature_name in df_X.columns else np.zeros((len(df_X), 1))
        return self.pipe.predict_proba(val)


def compute_comprehensive_metrics(y_true: np.ndarray, y_prob: np.ndarray, threshold: float = 0.5) -> Dict[str, Any]:
    """Computes full suite of classification and calibration verification metrics."""
    # Handle single-class edge cases gracefully
    unique_classes = np.unique(y_true)
    if len(unique_classes) < 2:
        return {
            "pr_auc": 0.0,
            "roc_auc": 0.5,
            "brier_score": calculate_brier_score(y_true, y_prob),
            "expected_calibration_error": calculate_ece(y_true, y_prob),
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "sample_count": len(y_true),
            "positive_rate_pct": round(float(np.mean(y_true)) * 100, 2)
        }

    # PR-AUC (Average Precision)
    # Mathematical Note: scikit-learn documentation explicitly warns against using trapezoidal
    # auc(rec, prec) on precision_recall_curve outputs because trapezoidal interpolation produces
    # severe artificial inflation (adding 0.47 area) for constant baseline predictions.
    # average_precision_score computes exact step-wise area under the precision-recall curve.
    pr_auc = average_precision_score(y_true, y_prob)

    # ROC-AUC
    roc_auc = roc_auc_score(y_true, y_prob)

    # Calibration Metrics
    brier = calculate_brier_score(y_true, y_prob)
    ece = calculate_ece(y_true, y_prob, n_bins=10)

    # Hard classification at specified threshold
    y_pred = (y_prob >= threshold).astype(int)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)

    return {
        "pr_auc": round(float(pr_auc), 4),
        "roc_auc": round(float(roc_auc), 4),
        "brier_score": round(float(brier), 4),
        "expected_calibration_error": round(float(ece), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "sample_count": len(y_true),
        "positive_rate_pct": round(float(np.mean(y_true)) * 100, 2)
    }


def wilson_score_interval(k: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    """Calculates Wilson score 95% confidence interval for binomial proportion."""
    if n == 0:
        return (0.0, 0.0)
    p_hat = k / n
    denominator = 1.0 + (z ** 2) / n
    center = (p_hat + (z ** 2) / (2 * n)) / denominator
    half_width = (z * np.sqrt((p_hat * (1.0 - p_hat) / n) + (z ** 2) / (4 * (n ** 2)))) / denominator
    return (round(float(max(0.0, center - half_width)) * 100, 2), round(float(min(1.0, center + half_width)) * 100, 2))


def get_10_bin_reliability_table(y_true: np.ndarray, y_prob: np.ndarray) -> List[Dict[str, Any]]:
    """Calculates decile empirical reliability calibration table with sample counts, Wilson 95% CIs, and support tiers."""
    bins = [
        (0.0, 0.10, "0-10%"),
        (0.10, 0.20, "10-20%"),
        (0.20, 0.30, "20-30%"),
        (0.30, 0.40, "30-40%"),
        (0.40, 0.50, "40-50%"),
        (0.50, 0.60, "50-60%"),
        (0.60, 0.70, "60-70%"),
        (0.70, 0.80, "70-80%"),
        (0.80, 0.90, "80-90%"),
        (0.90, 1.00, "90-100%")
    ]
    rows = []
    n = len(y_true)
    for lower, upper, label in bins:
        if upper == 1.0:
            mask = (y_prob >= lower) & (y_prob <= upper)
        else:
            mask = (y_prob >= lower) & (y_prob < upper)
        count = int(np.sum(mask))
        if count > 0:
            mean_pred = float(np.mean(y_prob[mask]))
            bust_count = int(np.sum(y_true[mask]))
            obs_rate = float(np.mean(y_true[mask]))
            gap = abs(mean_pred - obs_rate)
            se = np.sqrt(obs_rate * (1.0 - obs_rate) / count) if count > 1 else 0.0
            ci_low, ci_high = wilson_score_interval(bust_count, count)
            if count >= 300:
                support = "HIGH_SUPPORT"
            elif count >= 50:
                support = "MODERATE_SUPPORT"
            else:
                support = "LOW_SAMPLE_SUPPORT"
            rows.append({
                "bin_label": label,
                "bin_range": [lower, upper],
                "sample_count": count,
                "sample_pct": round((count / n) * 100, 2),
                "mean_predicted_prob_pct": round(mean_pred * 100, 2),
                "observed_bust_freq_pct": round(obs_rate * 100, 2),
                "calibration_gap_pct": round(gap * 100, 2),
                "standard_error_pct": round(float(se) * 100, 2),
                "ci_95_pct": [ci_low, ci_high],
                "support_level": support,
                "is_sparse_sample": count < 50
            })
        else:
            rows.append({
                "bin_label": label,
                "bin_range": [lower, upper],
                "sample_count": 0,
                "sample_pct": 0.0,
                "mean_predicted_prob_pct": round(((lower + upper) / 2.0) * 100, 2),
                "observed_bust_freq_pct": 0.0,
                "calibration_gap_pct": 0.0,
                "standard_error_pct": 0.0,
                "ci_95_pct": [0.0, 0.0],
                "support_level": "NO_SAMPLES",
                "is_sparse_sample": True
            })
    return rows


def run_benchmark(dataset_path: str = None, output_path: str = None) -> Dict[str, Any]:
    print("\n================================================================================")
    print("           FORECAST BUST AI: SCIENTIFIC MODEL BENCHMARKING ENGINE")
    print("================================================================================")

    # Locate training dataset
    if not dataset_path:
        candidates = [
            os.path.join("datasets", "training", "dataset_real_v002.csv"),
            os.path.join("datasets", "training", "dataset_real_v001.csv"),
            os.path.join("datasets", "processed", "aligned_meteorological_records.csv")
        ]
        for c in candidates:
            if os.path.exists(c):
                dataset_path = c
                break

    if not dataset_path or not os.path.exists(dataset_path):
        raise FileNotFoundError("No training dataset found for benchmarking.")

    print(f"[*] Loading dataset: {dataset_path}")
    df = pd.read_csv(dataset_path)
    print(f"[+] Total Records: {len(df):,}")

    # Ensure lead_time_group is populated
    if "lead_time_group" not in df.columns:
        df["lead_time_group"] = df["lead_hours"].apply(get_lead_time_group)

    # 1. Temporal Holdout Split (Strict Chronological: 70% Train, 15% Val, 15% Test)
    time_col = "valid_time" if "valid_time" in df.columns else ("initialization_time" if "initialization_time" in df.columns else None)
    if time_col:
        df["_dt_sort"] = pd.to_datetime(df[time_col])
        df = df.sort_values("_dt_sort").reset_index(drop=True)

    n = len(df)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)

    df_train = df.iloc[:train_end].copy()
    df_val = df.iloc[train_end:val_end].copy()
    df_test = df.iloc[val_end:].copy()

    print(f"[+] Data Split: Train={len(df_train):,} ({len(df_train)/n:.1%}) | Val={len(df_val):,} ({len(df_val)/n:.1%}) | Test={len(df_test):,} ({len(df_test)/n:.1%})")

    # Extract features strictly at T0
    X_train, y_train = extract_features(df_train, is_training=True)
    X_val, y_val = extract_features(df_val, is_training=True)
    X_test, y_test = extract_features(df_test, is_training=True)

    y_train_np = y_train.to_numpy()
    y_val_np = y_val.to_numpy()
    y_test_np = y_test.to_numpy()

    print(f"[+] Target Positive Rate: Train={y_train_np.mean():.2%} | Val={y_val_np.mean():.2%} | Test={y_test_np.mean():.2%}")

    # Benchmark Models Suite
    benchmark_models = {}

    # 1. Climatological Baseline
    print("[*] Training Climatological Baseline...", flush=True)
    climo = ClimatologicalBaseline().fit(X_train, y_train_np)
    benchmark_models["Climatological Baseline"] = climo

    # 2. Lead-Time Only Baseline
    print("[*] Training Lead-Time-Only Baseline...", flush=True)
    lead_base = SingleFeatureBaseline("lead_hours").fit(X_train, y_train_np)
    benchmark_models["Lead-Time Only Baseline"] = lead_base

    # 3. Ensemble Spread Baseline
    print("[*] Training Ensemble-Spread-Only Baseline...", flush=True)
    spread_base = SingleFeatureBaseline("ensemble_spread").fit(X_train, y_train_np)
    benchmark_models["Ensemble Spread Baseline"] = spread_base

    # 4. Calibrated Logistic Regression (L2 Baseline)
    print("[*] Training Calibrated Logistic Regression (L2)...", flush=True)
    scaler = StandardScaler()
    X_tr_sc = scaler.fit_transform(X_train)
    X_val_sc = scaler.transform(X_val)
    X_te_sc = scaler.transform(X_test)
    lr_raw = LogisticRegression(C=0.5, max_iter=500, class_weight="balanced")
    lr_raw.fit(X_tr_sc, y_train_np)
    lr_cal = ModelCalibrator(lr_raw, method="sigmoid").fit(X_val_sc, y_val_np)
    benchmark_models["Calibrated Logistic Regression"] = (lr_cal, scaler)

    # 5. Random Forest Ensemble
    print("[*] Training Random Forest Ensemble...", flush=True)
    rf_raw = RandomForestClassifier(n_estimators=100, max_depth=6, class_weight="balanced", random_state=42, n_jobs=-1)
    rf_raw.fit(X_train, y_train_np)
    rf_cal = ModelCalibrator(rf_raw, method="isotonic").fit(X_val, y_val_np)
    benchmark_models["Random Forest Ensemble"] = rf_cal

    # 6. LightGBM Classifier (Current & Improved)
    print("[*] Training LightGBM Classifier (Tuned)...", flush=True)
    lgb_raw = lgb.LGBMClassifier(
        num_leaves=24,
        max_depth=5,
        learning_rate=0.03,
        n_estimators=300,
        class_weight="balanced",
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=-1
    )
    lgb_raw.fit(X_train, y_train_np)

    # Calibration comparison on validation set (Isotonic vs Sigmoid vs Beta)
    print("[*] Comparing Calibration Methods (Isotonic vs Sigmoid vs Beta) on Validation Data...")
    cal_comp = compare_calibration_methods(lgb_raw, X_val.to_numpy(), y_val_np, X_test.to_numpy(), y_test_np)
    best_cal_method = cal_comp["selected_method"]
    print(f"[+] Selected Calibration Method for LightGBM: {best_cal_method.upper()}")
    lgb_cal = cal_comp["best_calibrator"]
    benchmark_models["LightGBM (Calibrated)"] = lgb_cal

    # 2. Benchmark Evaluation on Strictly Unseen Chronological Test Set
    results = {}
    print("\n" + "=" * 88)
    print(f"{'Model / Baseline':<32} {'PR-AUC':<9} {'ROC-AUC':<9} {'Brier':<9} {'ECE':<9} {'Latency (ms)':<12}")
    print("-" * 88)

    for name, model_obj in benchmark_models.items():
        # Measure inference latency
        t0 = time.perf_counter()
        if isinstance(model_obj, tuple):  # Scaler + model
            cal_mod, sc = model_obj
            X_eval = sc.transform(X_test)
            probs = cal_mod.predict_proba(X_eval)[:, 1]
        elif hasattr(model_obj, "predict_proba"):
            probs = model_obj.predict_proba(X_test)[:, 1]
        else:
            probs = np.full(len(X_test), 0.10)
        lat_ms = round(((time.perf_counter() - t0) / len(X_test)) * 1000, 3)

        metrics = compute_comprehensive_metrics(y_test_np, probs)
        metrics["inference_latency_ms"] = lat_ms
        results[name] = metrics

        print(f"{name:<32} {metrics['pr_auc']:<9.4f} {metrics['roc_auc']:<9.4f} {metrics['brier_score']:<9.4f} {metrics['expected_calibration_error']:<9.4f} {lat_ms:<12.3f}")

    print("=" * 88)

    # 3. Stratified Evaluation for Champion Model (LightGBM)
    champion_probs = lgb_cal.predict_proba(X_test.to_numpy())[:, 1]

    # A. By Lead-Time Group
    lead_strat = evaluate_stratified_calibration(df_test, y_test_np, champion_probs, "lead_time_group")
    print("\n[*] Champion Model Performance by Lead-Time Regime (Unseen Test Set):")
    for grp, m in lead_strat.items():
        if "brier_score" in m:
            print(f"    - {grp:<12}: Samples={m['sample_count']:<5} | Bust Rate={m['observed_bust_rate_pct']:<5.1f}% | Pred Prob={m['mean_predicted_prob_pct']:<5.1f}% | Brier={m['brier_score']:<6.4f} | ECE={m['expected_calibration_error']:<6.4f}")
        else:
            print(f"    - {grp:<12}: {m.get('status')}")

    # B. By Macro Climate Regime
    climate_strat = {}
    if "climate_regime" in df_test.columns:
        climate_strat = evaluate_stratified_calibration(df_test, y_test_np, champion_probs, "climate_regime")
    elif "latitude" in df_test.columns:
        # Compute macro regime on the fly for test set
        lats = df_test["latitude"].to_numpy()
        regimes = []
        for lat in lats:
            abs_lat = abs(lat)
            if abs_lat <= 23.5:
                regimes.append("TROPICAL")
            elif abs_lat >= 66.5:
                regimes.append("POLAR_ALPINE")
            else:
                regimes.append("TEMPERATE")
        df_test_regime = df_test.copy()
        df_test_regime["climate_regime"] = regimes
        climate_strat = evaluate_stratified_calibration(df_test_regime, y_test_np, champion_probs, "climate_regime")

    print("\n[*] Champion Model Performance by Climate Regime (Unseen Test Set):")
    for reg, m in climate_strat.items():
        if "brier_score" in m:
            print(f"    - {reg:<14}: Samples={m['sample_count']:<5} | Bust Rate={m['observed_bust_rate_pct']:<5.1f}% | Pred Prob={m['mean_predicted_prob_pct']:<5.1f}% | Brier={m['brier_score']:<6.4f} | ECE={m['expected_calibration_error']:<6.4f}")

    # C. 10-Bin Decile Reliability Table
    decile_table = get_10_bin_reliability_table(y_test_np, champion_probs)
    print("\n[*] Champion Model 10-Bin Decile Reliability Table (Unseen Test Set):")
    print(f"    {'Bin':<10} {'Samples':<9} {'Mean Pred %':<13} {'Obs Bust %':<12} {'Gap %':<9} {'StdErr %':<10}")
    print("    " + "-" * 65)
    for row in decile_table:
        print(f"    {row['bin_label']:<10} {row['sample_count']:<9} {row['mean_predicted_prob_pct']:<13.1f} {row['observed_bust_freq_pct']:<12.1f} {row['calibration_gap_pct']:<9.1f} {row['standard_error_pct']:<10.2f}")

    # 4. Geographic Holdout Evaluation (Unseen Locations)
    station_map = {
        (18.5204, 73.8567): "Pune",
        (28.6139, 77.2090): "Delhi",
        (19.0760, 72.8777): "Mumbai",
        (12.9716, 77.5946): "Bengaluru",
        (13.0827, 80.2707): "Chennai",
        (22.5726, 88.3639): "Kolkata",
        (17.3850, 78.4867): "Hyderabad",
        (23.0225, 72.5714): "Ahmedabad",
        (26.9124, 75.7873): "Jaipur",
        (31.1048, 77.1734): "Shimla",
        (26.1445, 91.7362): "Guwahati",
        (34.0837, 74.7973): "Srinagar",
        (8.5241, 76.9366): "Thiruvananthapuram",
        (20.2961, 85.8245): "Bhubaneswar",
        (21.1458, 79.0882): "Nagpur"
    }
    df["station_name"] = df.apply(lambda r: station_map.get((round(r["latitude"], 4), round(r["longitude"], 4)), "Unknown"), axis=1)
    unseen_geo_stations = ["Shimla", "Jaipur", "Thiruvananthapuram"]
    train_geo_stations = [s for s in station_map.values() if s not in unseen_geo_stations]

    df_geo_train = df[df["station_name"].isin(train_geo_stations)].copy()
    df_geo_test = df[df["station_name"].isin(unseen_geo_stations)].copy()

    df_geo_train["_dt_geo"] = pd.to_datetime(df_geo_train[time_col]) if time_col else np.arange(len(df_geo_train))
    df_geo_train = df_geo_train.sort_values("_dt_geo").reset_index(drop=True)
    n_gt = len(df_geo_train)
    df_gt_tr = df_geo_train.iloc[:int(n_gt * 0.80)]
    df_gt_va = df_geo_train.iloc[int(n_gt * 0.80):]

    X_gt_tr, y_gt_tr = extract_features(df_gt_tr, is_training=True)
    X_gt_va, y_gt_va = extract_features(df_gt_va, is_training=True)
    X_gt_te, y_gt_te = extract_features(df_geo_test, is_training=True)

    y_gt_tr_np, y_gt_va_np, y_gt_te_np = y_gt_tr.to_numpy(), y_gt_va.to_numpy(), y_gt_te.to_numpy()
    geo_raw = lgb.LGBMClassifier(
        num_leaves=24, max_depth=5, learning_rate=0.03, n_estimators=300,
        class_weight="balanced", subsample=0.8, colsample_bytree=0.8,
        random_state=42, verbosity=-1
    ).fit(X_gt_tr, y_gt_tr_np)
    geo_cal = ModelCalibrator(geo_raw, method="isotonic").fit(X_gt_va.to_numpy(), y_gt_va_np)
    geo_probs = geo_cal.predict_proba(X_gt_te.to_numpy())[:, 1]
    geo_metrics = compute_comprehensive_metrics(y_gt_te_np, geo_probs)
    geo_metrics["training_stations_count"] = len(train_geo_stations)
    geo_metrics["unseen_test_stations"] = unseen_geo_stations
    geo_metrics["unseen_regimes"] = ["ALPINE (Shimla)", "ARID (Jaipur)", "TROPICAL_COASTAL (Thiruvananthapuram)"]

    print("\n[*] Geographic Holdout Evaluation (Completely Unseen Locations):")
    print(f"    - Unseen Stations: {unseen_geo_stations}")
    print(f"    - Samples: {geo_metrics['sample_count']} | Bust Rate: {geo_metrics['positive_rate_pct']}%")
    print(f"    - ROC-AUC: {geo_metrics['roc_auc']:.4f} | PR-AUC: {geo_metrics['pr_auc']:.4f} | Brier: {geo_metrics['brier_score']:.4f} | ECE: {geo_metrics['expected_calibration_error']:.4f}")

    # Assemble and persist benchmark report
    benchmark_report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset_path": dataset_path,
        "sample_counts": {
            "total": len(df),
            "train": len(df_train),
            "validation": len(df_val),
            "test_holdout": len(df_test)
        },
        "models_benchmarked": results,
        "calibration_comparison_validation": cal_comp["validation_comparison"],
        "selected_calibration_method": best_cal_method,
        "lead_time_stratification": lead_strat,
        "climate_regime_stratification": climate_strat,
        "decile_reliability_table": decile_table,
        "geographic_holdout_evaluation": geo_metrics
    }

    if not output_path:
        os.makedirs("models", exist_ok=True)
        output_path = os.path.join("models", "benchmark_report.json")

    with open(output_path, "w") as f:
        json.dump(benchmark_report, f, indent=2)

    print(f"\n[+] Benchmark Report Saved: {output_path}")
    print("================================================================================\n")
    return benchmark_report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Forecast Bust AI Model Benchmarking Engine")
    parser.add_argument("--dataset", type=str, default=None)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()
    run_benchmark(dataset_path=args.dataset, output_path=args.output)
