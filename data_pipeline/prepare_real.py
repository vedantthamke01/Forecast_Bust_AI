"""
Real Historical Meteorological Dataset Preparation Script.
Retrieves genuine historical NWP forecasts (Days 1 to 10: 24h to 240h) from the
Previous-Runs archive and matches them with ERA5 reanalysis ground truth
at identical valid times and station coordinates across India.
Generates:
- datasets/training/dataset_real_v001.csv
- datasets/metadata/dataset_real_v001.json
- datasets/metadata/quality_report_real.json
STRICT RULE: Only authentic, non-fabricated records with proven provenance.
"""
import asyncio
import os
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any

from data_pipeline.providers.historical_nwp import HistoricalNWPProvider
from data_pipeline.providers.era5 import ERA5CDSProvider
from data_pipeline.providers.geocoding import INDIAN_CITIES_DB
from data_pipeline.aligner import ForecastReferenceAligner
from data_pipeline.quality import assess_dataframe_quality
from data_pipeline.labeler import BustLabeler


async def generate_real_dataset():
    print("\n==================================================")
    print("[*] GENERATING GENUINE REAL-WORLD TRAINING DATASET")
    print("    Source: NWP Previous Runs Archive + ERA5 Reanalysis")
    print("==================================================")

    os.makedirs("datasets/raw", exist_ok=True)
    os.makedirs("datasets/processed", exist_ok=True)
    os.makedirs("datasets/training", exist_ok=True)
    os.makedirs("datasets/metadata", exist_ok=True)

    nwp_provider = HistoricalNWPProvider(model="gfs_seamless")
    era5_provider = ERA5CDSProvider()

    # Representative Indian synoptic stations spanning distinct climatic regimes:
    # Western Ghats, Gangetic Plains, Deccan Plateau, Coastal, Himalayas, Northeast, Desert
    target_stations = [
        "Pune", "New Delhi", "Mumbai", "Kolkata", "Chennai",
        "Bengaluru", "Hyderabad", "Bhubaneswar", "Jaipur", "Guwahati",
        "Nagpur", "Ahmedabad", "Srinagar", "Thiruvananthapuram", "Shimla"
    ]
    stations = [c for c in INDIAN_CITIES_DB if c["name"] in target_stations]

    # Chronological periods representing diverse Indian meteorological seasons:
    # 1. 2024 Monsoon active phase (July 2024)
    # 2. 2024 Post-Monsoon / Northeast Monsoon (November 2024)
    # 3. 2025 Pre-Monsoon convective phase (April 2025)
    # 4. 2025 Monsoon active phase (August 2025)
    # 5. 2026 Unseen Test period (January 2026)
    sampling_windows = [
        {"name": "2024_Monsoon", "start": "2024-07-10", "end": "2024-07-12"},
        {"name": "2024_PostMonsoon", "start": "2024-11-15", "end": "2024-11-17"},
        {"name": "2025_PreMonsoon", "start": "2025-04-10", "end": "2025-04-12"},
        {"name": "2025_Monsoon", "start": "2025-08-05", "end": "2025-08-07"},
        {"name": "2026_UnseenTest", "start": "2026-01-15", "end": "2026-01-17"}
    ]

    all_forecasts: List[Dict[str, Any]] = []
    all_references: List[Dict[str, Any]] = []

    print(f"[+] Sampling {len(stations)} stations across {len(sampling_windows)} chronological regimes...")

    for window in sampling_windows:
        w_name = window["name"]
        start_d = window["start"]
        end_d = window["end"]
        print(f"\n--- Ingesting {w_name} ({start_d} to {end_d}) ---")

        for station in stations:
            name = station["name"]
            lat = station["lat"]
            lon = station["lon"]
            print(f"    Retrieving {name} (Lat: {lat:.2f}, Lon: {lon:.2f})...", end="", flush=True)

            try:
                # 1. Ingest genuine NWP previous forecast runs for Days 1 to 10
                fc_list = await nwp_provider.get_historical_forecast(lat, lon, start_d, end_d)
                # 2. Ingest matching ERA5 reanalysis observations for the exact valid period
                ref_list = await era5_provider.get_reference_data(lat, lon, start_d, end_d)

                for fc in fc_list:
                    all_forecasts.append(fc.model_dump(mode="json"))
                for ref in ref_list:
                    all_references.append(ref.model_dump(mode="json"))

                print(f" OK (FC: {len(fc_list)}, REF: {len(ref_list)})")
            except Exception as e:
                print(f" Error: {e}")

            # Brief pause to respect free-tier rate limits
            await asyncio.sleep(0.3)

    print(f"\n[+] Ingestion Summary:")
    print(f"    Total Forecast Records:  {len(all_forecasts):,}")
    print(f"    Total Reference Records: {len(all_references):,}")

    # 1. Save Raw Real Datasets
    raw_fc_file = "datasets/raw/raw_forecasts_real_archive.json"
    raw_ref_file = "datasets/raw/raw_references_real_era5.json"
    with open(raw_fc_file, "w") as f:
        json.dump(all_forecasts, f, indent=2, default=str)
    with open(raw_ref_file, "w") as f:
        json.dump(all_references, f, indent=2, default=str)

    # 2. Spatio-Temporal Alignment with Hard Validation
    print("\n[+] Aligning forecast horizons with ground-truth ERA5 observations...")
    aligner = ForecastReferenceAligner(spatial_tolerance_deg=0.5)
    df_aligned = aligner.align(all_forecasts, all_references)

    stats = aligner.alignment_stats
    print(f"    -> Matched Records:     {len(df_aligned):,}")
    print(f"    -> Unmatched Forecasts: {stats.get('unmatched_forecasts', 0):,}")
    print(f"    -> Temporal Match Rate: {stats.get('temporal_match_success_pct', 0)}%")
    print(f"    -> Spatial Match Rate:  {stats.get('spatial_match_success_pct', 0)}%")

    if df_aligned.empty:
        raise RuntimeError("No records were successfully aligned! Check date ranges and provider formats.")

    # 3. Apply Scientifically Configurable Bust Labeling
    print("\n[+] Applying dynamic lead-time forecast bust labeling...")
    # Base rain threshold: 25mm, Temp threshold: 4.0°C, Wind threshold: 8.5 m/s, scaling 12% per 24h lead
    labeler = BustLabeler(strategy="lead_time_dynamic")
    df_labeled = labeler.label_dataframe(df_aligned)

    training_file = "datasets/training/dataset_real_v001.csv"
    df_labeled.to_csv(training_file, index=False)
    bust_pct = round((df_labeled["is_bust"].sum() / len(df_labeled)) * 100, 2)
    print(f"    -> Real Training Dataset v001 Created: {len(df_labeled):,} rows ({bust_pct}% bust rate)")
    print(f"    -> Saved to {training_file}")

    # 4. Generate Quality Assurance Report
    print("\n[+] Executing Data Quality & Thermodynamic Assessment...")
    qc_report = assess_dataframe_quality(
        df_labeled,
        dataset_name="dataset_real_v001.csv",
        alignment_stats=stats
    )
    with open("datasets/metadata/quality_report_real.json", "w") as f:
        json.dump(qc_report, f, indent=2)
    print(f"    -> QC Status: {qc_report['status']} (Lead coverage: {qc_report['lead_time_coverage_percentage']}%)")

    # 5. Save Dataset Version Metadata Catalog
    metadata = {
        "version": "dataset_real_v001",
        "data_type": "REAL",
        "forecast_source": "Open-Meteo Previous Runs NWP Archive (GFS / ECMWF IFS)",
        "reference_source": "ECMWF ERA5 Reanalysis (Copernicus CDS)",
        "start_date": sampling_windows[0]["start"],
        "end_date": sampling_windows[-1]["end"],
        "stations_count": len(stations),
        "lead_hours": sorted([int(x) for x in df_labeled["lead_hours"].unique()]),
        "total_records": len(df_labeled),
        "bust_records": int(df_labeled["is_bust"].sum()),
        "bust_rate_percentage": bust_pct,
        "alignment_metrics": stats,
        "qc_status": qc_report["status"],
        "created_at": datetime.utcnow().isoformat()
    }
    with open("datasets/metadata/dataset_real_v001.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print("\n[+] Real dataset preparation completed successfully!")
    print("==================================================\n")
    return training_file


if __name__ == "__main__":
    asyncio.run(generate_real_dataset())
