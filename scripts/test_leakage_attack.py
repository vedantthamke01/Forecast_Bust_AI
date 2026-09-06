"""
Adversarial Future Data Leakage Attack Test Script.
Validates that ml_pipeline/features.py rejects all variations of future information:
actual, reference, observed, error, ground_truth, target, label, future, verification,
including uppercase, lowercase, mixed-case, prefixed, and suffixed column names.
"""
import os
import sys
sys.path.insert(0, os.path.abspath("."))

from ml_pipeline.features import check_data_leakage, FORBIDDEN_LEAKAGE_SUBSTRINGS

def run_leakage_attacks():
    print("=" * 80)
    print("STARTING ADVERSARIAL FUTURE DATA LEAKAGE ATTACK TEST")
    print("=" * 80)
    print(f"Forbidden substrings ({len(FORBIDDEN_LEAKAGE_SUBSTRINGS)}): {FORBIDDEN_LEAKAGE_SUBSTRINGS}")

    attack_columns = [
        "actual_temperature",
        "REFERENCE_TEMP",
        "future_error",
        "ObservedWind",
        "ground_truth_precipitation",
        "target_label",
        "verification_outcome",
        "prefixed_reference_val",
        "ACTUAL_WIND_SPEED",
        "Ground_Truth",
        "model_error_rate",
        "future_observation",
        "is_verification_bust",
        "TARGET_PROB",
        "observed_humidity",
        "verification_flag"
    ]

    all_detected = True
    for col in attack_columns:
        res = check_data_leakage([col])
        if not res:
            print(f"CRITICAL FAILURE: Leaked column '{col}' EVADED detection!")
            all_detected = False
        else:
            col_name, matched_pattern = res[0]
            print(f"PASS: Column '{col:28}' intercepted by pattern '{matched_pattern}'")

    # Also test that genuine forecast columns are NOT blocked
    genuine_cols = [
        "lead_hours", "latitude", "longitude",
        "forecast_temperature", "forecast_precipitation",
        "forecast_wind", "forecast_pressure", "forecast_humidity",
        "ensemble_spread", "run_revision"
    ]
    false_positives = check_data_leakage(genuine_cols)
    if false_positives:
        print(f"CRITICAL FAILURE: False positives detected on legitimate NWP features: {false_positives}")
        all_detected = False
    else:
        print(f"PASS: Legitimate NWP features ({len(genuine_cols)}) passed without false alarms.")

    print("=" * 80)
    if all_detected:
        print("ALL LEAKAGE ATTACKS INTERCEPTED & ZERO FALSE POSITIVES.")
        print("=" * 80)
        sys.exit(0)
    else:
        print("LEAKAGE GATE AUDIT FAILED.")
        print("=" * 80)
        sys.exit(1)

if __name__ == "__main__":
    run_leakage_attacks()
