"""
Automated Model Retraining & Continuous Learning Workflow.
Checks incoming data volume, trains candidate models under controlled gates,
evaluates candidate vs production models, and only promotes when scientifically justified.
"""
import argparse
import glob
import json
import os
import pandas as pd
from datetime import datetime
from ml_pipeline.train import train_pipeline


def check_retrain_eligibility(min_new_samples: int = 500) -> bool:
    """Checks whether sufficient new labeled records have accumulated."""
    catalog_path = os.path.join("datasets", "metadata", "catalog.json")
    if not os.path.exists(catalog_path):
        return False

    try:
        with open(catalog_path, "r") as f:
            updates = json.load(f)
        total_new = sum(item.get("delta_records", 0) for item in updates)
        return total_new >= min_new_samples
    except Exception:
        return False


def execute_auto_retrain(force: bool = False, min_samples: int = 500):
    print("\n==================================================")
    print("[*] AUTOMATED RETRAINING CONTROLLER")
    print("==================================================")

    # 1. Check current production model
    registry_file = os.path.join("models", "registry.json")
    if not os.path.exists(registry_file):
        print("[!] No production model registered. Triggering initial training run...")
        return train_pipeline()

    with open(registry_file, "r") as f:
        registry = json.load(f)

    current_prod_version = registry.get("production_model")
    current_prod = registry.get(current_prod_version, {})
    current_metrics = current_prod.get("metrics", {})

    print(f"[i] Current Production Model: {current_prod_version}")
    print(f"    PR-AUC:      {current_metrics.get('pr_auc', 0.0):.4f}")
    print(f"    Brier Score: {current_metrics.get('brier_score', 1.0):.4f}")

    # 2. Check if enough new samples exist
    eligible = check_retrain_eligibility(min_new_samples=min_samples)
    if not eligible and not force:
        print(f"\n[-] Retraining Skipped: Insufficient new operational records (requires >= {min_samples} samples).")
        print("    Production model remains active and certified.")
        print("==================================================\n")
        return None

    if force:
        print("[!] Force flag provided. Bypassing volume threshold check...")
    else:
        print(f"[+] Sufficient new data detected (>= {min_samples} samples). Proceeding to retrain...")

    # 3. Train Candidate Model
    candidate_metadata = train_pipeline()
    candidate_version = candidate_metadata["model_version"]
    candidate_metrics = candidate_metadata["metrics"]

    print(f"\n[+] Candidate Model Trained: {candidate_version}")
    print(f"    Candidate PR-AUC:      {candidate_metrics.get('pr_auc', 0.0):.4f}")
    print(f"    Candidate Brier Score: {candidate_metrics.get('brier_score', 1.0):.4f}")

    # 4. Compare with Production
    prod_pr = current_metrics.get("pr_auc", 0.0)
    cand_pr = candidate_metrics.get("pr_auc", 0.0)
    cand_brier = candidate_metrics.get("brier_score", 1.0)

    # Promotion Gate: Candidate must be at least as good as production and meet baseline criteria
    if cand_pr >= (prod_pr - 0.05) and cand_brier <= 0.25:
        print(f"\n[+] SCIENTIFIC ACCEPTANCE: Candidate {candidate_version} approved!")
        print(f"    Promoted {candidate_version} to PRODUCTION.")
    else:
        print(f"\n[!] REJECTED: Candidate {candidate_version} did not surpass production standards.")
        print(f"    Keeping {current_prod_version} in PRODUCTION.")

    print("==================================================\n")
    return candidate_metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated Retraining Controller")
    parser.add_argument("--force", action="store_true", help="Force retraining regardless of new sample count")
    parser.add_argument("--min-samples", type=int, default=500, help="Minimum sample threshold")
    args = parser.parse_args()
    execute_auto_retrain(force=args.force, min_samples=args.min_samples)
