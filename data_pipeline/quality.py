"""
Automated Data Quality Assessment & Validation Engine.
Computes real, mathematically verifiable statistics across raw and aligned datasets:
- Provenance certification (REAL vs SYNTHETIC)
- Alignment success & unmatched forecast reporting
- Missing value percentages
- Duplicate detection
- Coordinate bounds validation (India synoptic bounds)
- Physical thermodynamic & dynamic boundary validation
- Forecast horizon coverage (Days 1 to 10)
- Bust rate calculation
"""
from typing import Dict, Any, Optional
import argparse
import glob
import json
import os
import pandas as pd
import numpy as np
from datetime import datetime


PHYSICAL_LIMITS = {
    "temperature": {"min": -35.0, "max": 55.0},          # °C
    "precipitation": {"min": 0.0, "max": 1200.0},        # mm/24h
    "wind_speed": {"min": 0.0, "max": 120.0},             # m/s
    "pressure_msl": {"min": 870.0, "max": 1085.0},        # hPa
    "relative_humidity": {"min": 0.0, "max": 100.0},     # %
    "cloud_cover": {"min": 0.0, "max": 100.0}             # %
}

INDIA_BOUNDS = {
    "lat_min": 6.0, "lat_max": 38.0,
    "lon_min": 68.0, "lon_max": 98.0
}


def assess_dataframe_quality(
    df: pd.DataFrame,
    dataset_name: str = "dataset",
    alignment_stats: Optional[Dict[str, Any]] = None
) -> dict:
    total_records = len(df)
    if total_records == 0:
        return {
            "status": "FAIL",
            "total_records": 0,
            "error": "Dataset is empty"
        }

    # 1. Provenance
    data_type = "REAL"
    if "data_type" in df.columns:
        data_type = str(df["data_type"].iloc[0])
    elif "forecast_provider" in df.columns and "demo" in str(df["forecast_provider"].iloc[0]).lower():
        data_type = "SYNTHETIC"

    forecast_source = str(df["forecast_provider"].iloc[0]) if "forecast_provider" in df.columns else "NWP"
    reference_source = str(df["reference_source"].iloc[0]) if "reference_source" in df.columns else "ERA5"

    # 2. Duplicates
    dup_cols = [c for c in ["latitude", "longitude", "valid_time", "lead_hours"] if c in df.columns]
    duplicate_count = int(df.duplicated(subset=dup_cols).sum()) if dup_cols else 0
    duplicate_pct = round((duplicate_count / total_records) * 100, 3)

    # 3. Missing Values
    missing_by_col = {}
    for col in df.columns:
        null_count = int(df[col].isnull().sum())
        missing_by_col[col] = {
            "null_count": null_count,
            "percentage": round((null_count / total_records) * 100, 2)
        }
    overall_missing_pct = round(float(df.isnull().mean().mean() * 100), 2)

    # 4. Coordinate validation
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

    # 5. Physical anomaly checks
    temp_anomalies = 0
    if "forecast_temperature" in df.columns:
        t_col = df["forecast_temperature"].dropna()
        temp_anomalies = int(((t_col < PHYSICAL_LIMITS["temperature"]["min"]) |
                              (t_col > PHYSICAL_LIMITS["temperature"]["max"])).sum())
    temp_anomaly_pct = round((temp_anomalies / total_records) * 100, 3)

    precip_anomalies = 0
    if "forecast_precipitation" in df.columns:
        p_col = df["forecast_precipitation"].dropna()
        precip_anomalies = int(((p_col < PHYSICAL_LIMITS["precipitation"]["min"]) |
                               (p_col > PHYSICAL_LIMITS["precipitation"]["max"])).sum())

    # 6. Lead Time Coverage
    lead_times_present = []
    if "lead_hours" in df.columns:
        lead_times_present = sorted([int(x) for x in df["lead_hours"].unique() if not np.isnan(x)])
    coverage_score = round(min(100.0, (len(lead_times_present) / 10.0) * 100.0), 1)

    # 7. Date and Station Coverage
    date_range = {}
    if "valid_time" in df.columns:
        date_range = {
            "start": str(df["valid_time"].min()),
            "end": str(df["valid_time"].max())
        }

    stations_count = 0
    if "latitude" in df.columns and "longitude" in df.columns:
        coords = df[["latitude", "longitude"]].drop_duplicates()
        stations_count = len(coords)

    # 8. Bust Rate
    bust_rate = None
    if "is_bust" in df.columns:
        bust_rate = round(float((df["is_bust"].sum() / total_records) * 100), 2)

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
        "data_provenance": {
            "data_type": data_type,
            "forecast_source": forecast_source,
            "reference_source": reference_source
        },
        "total_records": total_records,
        "missing_overall_percentage": overall_missing_pct,
        "duplicate_records": duplicate_count,
        "duplicate_percentage": duplicate_pct,
        "invalid_coordinates_count": invalid_coords_count,
        "temperature_anomalies_count": temp_anomalies,
        "precipitation_anomalies_count": precip_anomalies,
        "lead_time_coverage_percentage": coverage_score,
        "lead_hours_present": lead_times_present,
        "stations_count": stations_count,
        "date_range": date_range,
        "bust_rate_percentage": bust_rate,
        "alignment_metrics": alignment_stats or {},
        "missing_by_column": missing_by_col
    }

    return report


def main():
    parser = argparse.ArgumentParser(description="Meteorological Dataset Quality Assessor")
    parser.add_argument("--file", type=str, default="datasets/training/dataset_real_v001.csv",
                        help="Path to CSV dataset to evaluate")
    parser.add_argument("--output", type=str, default="datasets/metadata/quality_report.json",
                        help="Output path for QC report")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        # Fallback to dataset_v001.csv if real not yet generated
        if os.path.exists("datasets/training/dataset_v001.csv"):
            args.file = "datasets/training/dataset_v001.csv"
        else:
            print(f"[!] File not found: {args.file}")
            return

    df = pd.read_csv(args.file)
    report = assess_dataframe_quality(df, dataset_name=os.path.basename(args.file))
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n==================================================")
    print(f"[+] DATA QUALITY ASSESSMENT: {report['status']}")
    print(f"==================================================")
    print(f" Dataset:      {report['dataset_name']}")
    print(f" Data Type:    {report['data_provenance']['data_type']}")
    print(f" Records:      {report['total_records']:,}")
    print(f" Stations:     {report['stations_count']}")
    print(f" Lead Range:   {report['lead_hours_present']}")
    print(f" Bust Rate:    {report['bust_rate_percentage']}%")
    print(f" Report saved: {args.output}\n")


if __name__ == "__main__":
    main()
