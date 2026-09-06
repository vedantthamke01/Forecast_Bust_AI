"""
Real Historical Meteorological Dataset Preparation Script (Version 002).
Retrieves genuine historical NWP forecasts across all medium-range horizons
(Days 1 to 10 requested: 24h to 240h) from the legitimate Previous-Runs archive
and matches them with ERA5 reanalysis ground truth at identical valid times and station coordinates across India.

Generates:
- datasets/training/dataset_real_v002.csv
- datasets/metadata/dataset_real_v002.json
- datasets/metadata/quality_report_real_v002.json

STRICT SCIENTIFIC INTEGRITY RULES:
1. Zero fabrication: Days 8–10 are requested from the archive; if unpopulated by the public provider, no synthetic records are generated.
2. Hard alignment: forecast.valid_time == reference.valid_time.
3. Hard lead verification: lead_hours == valid_time - initialization_time.
4. Preserves dataset_real_v001.csv and benchmark demo datasets.
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


async def generate_real_dataset_v002():
    print("\n==================================================")
    print("[*] GENERATING GENUINE REAL-WORLD TRAINING DATASET V002")
    print("    Target: Medium-Range Weather Forecast Bust Detection")
    print("    Source: NWP Previous Runs Archive + ERA5 Reanalysis")
    print("==================================================")

    os.makedirs("datasets/raw", exist_ok=True)
    os.makedirs("datasets/processed", exist_ok=True)
    os.makedirs("datasets/training", exist_ok=True)
    os.makedirs("datasets/metadata", exist_ok=True)

    # Initialize providers
    nwp_provider = HistoricalNWPProvider(model="gfs_seamless")
    era5_provider = ERA5CDSProvider()

    # 15 Synoptic stations spanning all key Indian climatic regimes
    target_stations = [
        "Pune", "New Delhi", "Mumbai", "Kolkata", "Chennai",
        "Bengaluru", "Hyderabad", "Bhubaneswar", "Jaipur", "Guwahati",
        "Nagpur", "Ahmedabad", "Srinagar", "Thiruvananthapuram", "Shimla"
    ]
    stations = [c for c in INDIAN_CITIES_DB if c["name"] in target_stations]

    # Chronological seasonal sampling windows
    sampling_windows = [
        {"name": "2024_Monsoon", "start": "2024-07-10", "end": "2024-07-12"},
        {"name": "2024_PostMonsoon", "start": "2024-11-15", "end": "2024-11-17"},
        {"name": "2025_PreMonsoon", "start": "2025-04-10", "end": "2025-04-12"},
        {"name": "2025_Monsoon", "start": "2025-08-05", "end": "2025-08-07"},
        {"name": "2026_UnseenTest", "start": "2026-01-15", "end": "2026-01-17"}
    ]

    all_forecasts: List[Dict[str, Any]] = []
    all_references: List[Dict[str, Any]] = []

    print(f"[+] Requesting Days 1 to 10 (24h to 240h) across {len(stations)} stations...")

    for window in sampling_windows:
        w_name = window["name"]
        start_d = window["start"]
        end_d = window["end"]
        print(f"\n--- Ingesting {w_name} ({start_d} to {end_d}) ---")

        for station in stations:
            name = station["name"]
            lat, lon = station["lat"], station["lon"]
            print(f"    Retrieving {name} ({lat:.2f}, {lon:.2f})...", end="", flush=True)

            try:
                fc_list = await nwp_provider.get_historical_forecast(lat, lon, start_d, end_d)
                ref_list = await era5_provider.get_reference_data(lat, lon, start_d, end_d)

                for fc in fc_list:
                    all_forecasts.append(fc.model_dump(mode="json"))
                for ref in ref_list:
                    all_references.append(ref.model_dump(mode="json"))

                print(f" OK (FC: {len(fc_list)}, REF: {len(ref_list)})")
            except Exception as e:
                print(f" Error: {e}")

            await asyncio.sleep(0.2)

    print(f"\n[+] Ingestion Summary:")
    print(f"    Total Forecast Records Ingested:  {len(all_forecasts):,}")
    print(f"    Total Reference Records Ingested: {len(all_references):,}")

    # 1. Spatio-Temporal Alignment with Hard Constraint Verification
    print("\n[+] Aligning forecast horizons with ground-truth ERA5 observations...")
    aligner = ForecastReferenceAligner(spatial_tolerance_deg=0.5)
    df_aligned = aligner.align(all_forecasts, all_references)
    stats = aligner.alignment_stats

    print(f"    -> Matched Records:     {len(df_aligned):,}")
    print(f"    -> Unmatched Forecasts: {stats.get('unmatched_forecasts', 0):,}")
    print(f"    -> Temporal Match Rate: {stats.get('temporal_match_success_pct', 0)}%")
    print(f"    -> Spatial Match Rate:  {stats.get('spatial_match_success_pct', 0)}%")

    # 2. Hard Lead-Hour Consistency Audit (valid_time - init_time == lead_hours)
    print("\n[+] Performing Independent Lead-Hour Consistency Audit...")
    v_times = pd.to_datetime(df_aligned["valid_time"])
    i_times = pd.to_datetime(df_aligned["initialization_time"])
    calc_leads = ((v_times - i_times).dt.total_seconds() / 3600.0).round().astype(int)
    stated_leads = df_aligned["lead_hours"].astype(int)
    lead_mismatches = int((calc_leads != stated_leads).sum())

    print(f"    -> Total Samples Checked: {len(df_aligned):,}")
    print(f"    -> Lead-Hour Mismatches:  {lead_mismatches} (Expected: 0)")
    assert lead_mismatches == 0, f"Critical integrity failure: {lead_mismatches} lead mismatches detected!"

    unique_leads = sorted([int(x) for x in df_aligned["lead_hours"].unique()])
    print(f"    -> Unique Lead Horizons Present: {unique_leads}")
    print(f"    -> Medium-Range (Days 3–7) Present: {[h for h in unique_leads if h >= 72]}")

    # Document Days 8–10 Archive Availability Status
    missing_days_8_10 = [h for h in [192, 216, 240] if h not in unique_leads]
    if missing_days_8_10:
        print(f"\n[!] SCIENTIFIC DISCLOSURE: Horizons {missing_days_8_10} (Days 8–10) are unpopulated in the free Open-Meteo Previous Runs archive.")
        print(f"    In adherence to Rule 17, zero synthetic values were fabricated.")

    # 3. Scientific Dynamic Lead-Time Bust Labeling
    print("\n[+] Applying dynamic lead-time forecast bust labeling...")
    labeler = BustLabeler(strategy="lead_time_dynamic")
    df_labeled = labeler.label_dataframe(df_aligned)

    training_file = "datasets/training/dataset_real_v002.csv"
    df_labeled.to_csv(training_file, index=False)
    bust_pct = round((df_labeled["is_bust"].sum() / len(df_labeled)) * 100, 2)
    print(f"    -> Real Training Dataset v002 Created: {len(df_labeled):,} rows ({bust_pct}% bust rate)")
    print(f"    -> Saved to {training_file}")

    # 4. Data Quality & Thermodynamic Assessment
    print("\n[+] Executing Data Quality & Thermodynamic Assessment...")
    qc_report = assess_dataframe_quality(
        df_labeled,
        dataset_name="dataset_real_v002.csv",
        alignment_stats=stats
    )
    with open("datasets/metadata/quality_report_real_v002.json", "w") as f:
        json.dump(qc_report, f, indent=2)
    print(f"    -> QC Status: {qc_report['status']} (Lead coverage: {qc_report['lead_time_coverage_percentage']}%)")

    # 5. Save Dataset Version Metadata Catalog
    metadata = {
        "version": "dataset_real_v002",
        "data_type": "REAL",
        "forecast_source": "Open-Meteo Previous Runs NWP Archive (GFS / ECMWF IFS)",
        "reference_source": "ECMWF ERA5 Reanalysis (Copernicus CDS)",
        "start_date": sampling_windows[0]["start"],
        "end_date": sampling_windows[-1]["end"],
        "stations_count": len(stations),
        "lead_hours": unique_leads,
        "lead_hours_days": [int(h // 24) for h in unique_leads],
        "days_8_to_10_status": "Archival limitation of free public endpoint (requires MARS / NCMRWF institutional access). Zero synthetic data generated.",
        "total_records": len(df_labeled),
        "bust_records": int(df_labeled["is_bust"].sum()),
        "bust_rate_percentage": bust_pct,
        "lead_consistency_mismatches": lead_mismatches,
        "alignment_metrics": stats,
        "qc_status": qc_report["status"],
        "created_at": datetime.utcnow().isoformat()
    }
    with open("datasets/metadata/dataset_real_v002.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print("\n[+] Real dataset v002 preparation completed successfully!")
    print("==================================================\n")
    return training_file


if __name__ == "__main__":
    asyncio.run(generate_real_dataset_v002())
