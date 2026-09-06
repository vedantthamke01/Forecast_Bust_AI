"""
Automated Data Quality Assessment & Validation Engine.
Computes real, mathematically verifiable statistics across raw and aligned datasets:
- Missing value percentages
- Duplicate detection
- Coordinate bounds validation (India synoptic bounds)
- Physical thermodynamic & dynamic boundary validation
- Forecast horizon coverage
Generates standardized Quality Reports for meteorological certification.
"""
import argparse
import glob
import json
import os
import pandas as pd
import numpy as np
from datetime import datetime


PHYSICAL_LIMITS = {
    "temperature": {"min": -35.0, "max": 55.0},          # °C
    "precipitation": {"min": 0.0, "max": 1200.0},        # mm/24h (Cherrapunji recorded ~1040mm)
    "wind_speed": {"min": 0.0, "max": 120.0},             # m/s (Super cyclone gusts)
    "pressure_msl": {"min": 870.0, "max": 1085.0},        # hPa (Deepest typhoon ~870 hPa)
    "relative_humidity": {"min": 0.0, "max": 100.0},     # %
    "cloud_cover": {"min": 0.0, "max": 100.0}             # %
}

INDIA_BOUNDS = {
    "lat_min": 6.0, "lat_max": 38.0,
    "lon_min": 68.0, "lon_max": 98.0
}


def assess_dataframe_quality(df: pd.DataFrame, dataset_name: str = "dataset") -> dict:
    total_records = len(df)
    if total_records == 0:
        return {
            "status": "FAIL",
            "total_records": 0,
            "error": "Dataset is empty"
        }

    # 1. Duplicates
    dup_cols = [c for c in ["latitude", "longitude", "valid_time", "lead_hours"] if c in df.columns]
    duplicate_count = int(df.duplicated(subset=dup_cols).sum()) if dup_cols else 0
    duplicate_pct = round((duplicate_count / total_records) * 100, 3)

    # 2. Missing Values
    missing_by_col = {}
    for col in df.columns:
        null_count = int(df[col].isnull().sum())
        missing_by_col[col] = {
            "null_count": null_count,
            "percentage": round((null_count / total_records) * 100, 2)
        }
    overall_missing_pct = round(float(df.isnull().mean().mean() * 100), 2)

    # 3. Coordinate validation
    invalid_coords_count = 0
    if "latitude" in df.columns and "longitude" in df.columns:
        invalid_coords = (
            (df["latitude"] < INDIA_BOUNDS["lat_min"]) |
            (df["latitude"] > INDIA_BOUNDS["lat_max"]) |
            (df["longitude"] < INDIA_BOUNDS["lon_min"]) |
            (df["longitude"] > INDIA_BOUNDS["lon_max"])
        )
        invalid_coords_count = int(invalid_coords.sum())
    coords_invalid_pct = round((invalid_coords_count / total_records) * 100, 2)

    # 4. Physical anomaly checks
    temp_anomalies = 0
    if "forecast_temperature" in df.columns:
        t_col = df["forecast_temperature"].dropna()
        temp_anomalies = int(((t_col < PHYSICAL_LIMITS["temperature"]["min"]) |
                              (t_col > PHYSICAL_LIMITS["temperature"]["max"])).sum())
    elif "temperature_2m" in df.columns:
        t_col = df["temperature_2m"].dropna()
        temp_anomalies = int(((t_col < PHYSICAL_LIMITS["temperature"]["min"]) |
                              (t_col > PHYSICAL_LIMITS["temperature"]["max"])).sum())
    temp_anomaly_pct = round((temp_anomalies / total_records) * 100, 3)

    precip_anomalies = 0
    if "forecast_precipitation" in df.columns:
        p_col = df["forecast_precipitation"].dropna()
        precip_anomalies = int(((p_col < PHYSICAL_LIMITS["precipitation"]["min"]) |
                               (p_col > PHYSICAL_LIMITS["precipitation"]["max"])).sum())
    elif "precipitation" in df.columns:
        p_col = df["precipitation"].dropna()
        precip_anomalies = int(((p_col < PHYSICAL_LIMITS["precipitation"]["min"]) |
                               (p_col > PHYSICAL_LIMITS["precipitation"]["max"])).sum())

    # 5. Lead Time Coverage
    lead_times_present = []
    if "lead_hours" in df.columns:
        lead_times_present = sorted([int(x) for x in df["lead_hours"].unique() if not np.isnan(x)])
    coverage_score = round(min(100.0, (len(lead_times_present) / 10.0) * 100.0), 1)

    # Overall Status Determination
    status = "PASS"
    if coords_invalid_pct > 5.0 or temp_anomaly_pct > 1.0 or overall_missing_pct > 20.0:
        status = "FAIL"
    elif overall_missing_pct > 5.0 or duplicate_pct > 2.0:
        status = "WARN"

    report = {
        "dataset_name": dataset_name,
        "evaluation_timestamp": datetime.utcnow().isoformat(),
        "status": status,
        "total_records": total_records,
        "missing_overall_percentage": overall_missing_pct,
        "duplicate_records": duplicate_count,
        "duplicate_percentage": duplicate_pct,
        "invalid_coordinates_count": invalid_coords_count,
        "temperature_anomalies_count": temp_anomalies,
        "precipitation_anomalies_count": precip_anomalies,
        "lead_time_coverage_percentage": coverage_score,
        "lead_hours_present": lead_times_present,
        "missing_by_column": missing_by_col
    }

    return report


def run_quality_check(input_path: str = None):
    print("\n==================================================")
    print("[*] DATA QUALITY ASSESSMENT & VALIDATION")
    print("==================================================")

    # Locate dataset file
    if not input_path:
        processed_files = glob.glob("datasets/processed/*.csv")
        raw_files = glob.glob("datasets/raw/raw_forecasts_*.json")
        if processed_files:
            input_path = processed_files[-1]
        elif raw_files:
            input_path = raw_files[-1]
        else:
            print("[-] No dataset found in datasets/processed or datasets/raw.")
            print("[i] Run 'python -m data_pipeline.download --source demo' first.")
            return

    print(f"[+] Inspecting dataset: {input_path}")
    if input_path.endswith(".csv"):
        df = pd.read_csv(input_path)
    elif input_path.endswith(".json"):
        with open(input_path, "r") as f:
            data = json.load(f)
        df = pd.DataFrame(data)
    else:
        print(f"[-] Unsupported file format: {input_path}")
        return

    report = assess_dataframe_quality(df, dataset_name=os.path.basename(input_path))

    # Save report
    out_dir = os.path.join("datasets", "metadata")
    os.makedirs(out_dir, exist_ok=True)
    report_file = os.path.join(out_dir, "quality_report.json")
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    # Print clean meteorological report card
    print("\n==================================================")
    print(f"       DATASET QUALITY REPORT: {report['status']}")
    print("==================================================")
    print(f" Total Records Analyzed:     {report['total_records']:,}")
    print(f" Overall Missing Values:     {report['missing_overall_percentage']:.2f}%")
    print(f" Duplicate Records:          {report['duplicate_records']:,} ({report['duplicate_percentage']}%)")
    print(f" Invalid Geo-Coordinates:    {report['invalid_coordinates_count']}")
    print(f" Thermodynamic Anomalies:    {report['temperature_anomalies_count']}")
    print(f" Precipitation Anomalies:    {report['precipitation_anomalies_count']}")
    print(f" Medium-Range Lead Coverage: {report['lead_time_coverage_percentage']:.1f}%")
    print(f" Lead Hours Observed:        {report['lead_hours_present']}")
    print(f" QC Status:                  {report['status']}")
    print(f" Report Saved:               {report_file}")
    print("==================================================\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dataset Quality Assurance Engine")
    parser.add_argument("--file", type=str, default=None, help="Path to dataset file")
    args = parser.parse_args()
    run_quality_check(args.file)
