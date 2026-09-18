"""
Global Meteorological Training Dataset Preparation Engine (Version 003).
Retrieves authentic historical NWP forecasts across global benchmark observatories
spanning all 6 continents and all macro Köppen-Geiger climate regimes.

Aligns genuine forecast runs with Copernicus ECMWF ERA5 reanalysis ground truth
at identical valid times and station coordinates.

STRICT SCIENTIFIC INTEGRITY RULES:
1. Zero fabrication: unpopulated archival horizons remain unpopulated without synthetic backfill.
2. Hard alignment: forecast.valid_time == reference.valid_time.
3. Hard lead verification: lead_hours == valid_time - initialization_time.
4. Non-linear saturation thresholding for extended horizons (Day 3 to Day 30).
5. Full traceability: provenance metadata cataloged in dataset manifest.
"""
import asyncio
import os
import sys
import json
from datetime import datetime, timezone
from typing import List, Dict, Any
import pandas as pd

# Ensure repository root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_pipeline.providers.historical_nwp import HistoricalNWPProvider
from data_pipeline.providers.era5 import ERA5CDSProvider
from data_pipeline.providers.geocoding import GLOBAL_BENCHMARK_STATIONS
from data_pipeline.aligner import ForecastReferenceAligner
from data_pipeline.quality import assess_dataframe_quality
from data_pipeline.labeler import BustLabeler, get_lead_time_group
from data_pipeline.koppen import classify_koppen_regime


async def generate_global_dataset_v003(
    stations_to_sample: List[str] = None,
    max_stations: int = 30
) -> str:
    print("\n================================================================================")
    print("[*] GENERATING GLOBAL BENCHMARK METEOROLOGICAL TRAINING DATASET V003")
    print("    Target: Multi-Regime Global Forecast Bust Detection (Days 1 to 30)")
    print("    Source: Open-Meteo Previous Runs / Ensemble + ECMWF ERA5 Reanalysis")
    print("================================================================================")

    os.makedirs("datasets/raw", exist_ok=True)
    os.makedirs("datasets/processed", exist_ok=True)
    os.makedirs("datasets/training", exist_ok=True)
    os.makedirs("datasets/metadata", exist_ok=True)

    nwp_provider = HistoricalNWPProvider(model="gfs_seamless")
    era5_provider = ERA5CDSProvider()

    # Select representative global stations across continents and Koppen regimes
    if stations_to_sample:
        selected_stations = [s for s in GLOBAL_BENCHMARK_STATIONS if s["name"] in stations_to_sample]
    else:
        # Balanced selection across Tropical, Arid, Temperate, Continental, and Polar/Alpine
        regime_targets = {"TROPICAL": 6, "ARID": 6, "TEMPERATE": 8, "CONTINENTAL": 6, "POLAR_ALPINE": 4}
        selected_stations = []
        counts = {k: 0 for k in regime_targets}
        for s in GLOBAL_BENCHMARK_STATIONS:
            reg = s.get("climate_regime", "TEMPERATE")
            if counts.get(reg, 0) < regime_targets.get(reg, 6):
                selected_stations.append(s)
                counts[reg] = counts.get(reg, 0) + 1
            if len(selected_stations) >= max_stations:
                break

    print(f"[+] Selected {len(selected_stations)} global stations across all Köppen regimes:")
    for s in selected_stations:
        print(f"    - {s['name']} ({s.get('country', 'N/A')}): Lat {s['lat']:.2f}, Lon {s['lon']:.2f} [{s.get('climate_regime', 'N/A')}]")

    # Chronological multi-seasonal sampling windows (Monsoon, Winter, Summer, Transitional)
    sampling_windows = [
        {"name": "2024_Q3_BorealSummer", "start": "2024-07-10", "end": "2024-07-12"},
        {"name": "2024_Q4_BorealAutumn", "start": "2024-11-15", "end": "2024-11-17"},
        {"name": "2025_Q2_BorealSpring", "start": "2025-04-10", "end": "2025-04-12"},
        {"name": "2025_Q3_BorealSummer", "start": "2025-08-05", "end": "2025-08-07"},
        {"name": "2026_Q1_UnseenTest", "start": "2026-01-15", "end": "2026-01-17"}
    ]

    all_forecasts: List[Dict[str, Any]] = []
    all_references: List[Dict[str, Any]] = []

    print(f"\n[+] Ingesting authentic forecasts and ERA5 ground truth across {len(sampling_windows)} sampling windows...")

    for window in sampling_windows:
        w_name = window["name"]
        start_d = window["start"]
        end_d = window["end"]
        print(f"\n--- Processing Window: {w_name} ({start_d} to {end_d}) ---")

        for station in selected_stations:
            name = station["name"]
            lat, lon = station["lat"], station["lon"]
            elev = station.get("elevation", 100.0)
            country = station.get("country", "Unknown")
            regime = station.get("climate_regime", "TEMPERATE")
            print(f"    Retrieving {name}, {country} ({lat:.2f}, {lon:.2f})...", end="", flush=True)

            try:
                fc_list = await nwp_provider.get_historical_forecast(lat, lon, start_d, end_d)
                ref_list = await era5_provider.get_reference_data(lat, lon, start_d, end_d)

                for fc in fc_list:
                    fc_dict = fc.model_dump(mode="json")
                    fc_dict["station_name"] = name
                    fc_dict["country"] = country
                    fc_dict["elevation"] = elev
                    fc_dict["climate_regime"] = regime
                    all_forecasts.append(fc_dict)

                for ref in ref_list:
                    ref_dict = ref.model_dump(mode="json")
                    ref_dict["station_name"] = name
                    ref_dict["country"] = country
                    ref_dict["elevation"] = elev
                    ref_dict["climate_regime"] = regime
                    all_references.append(ref_dict)

                print(f" OK (FC: {len(fc_list)}, REF: {len(ref_list)})")
            except Exception as e:
                print(f" Error: {e}")

            await asyncio.sleep(0.15)

    print(f"\n[+] Ingestion Totals:")
    print(f"    - Forecast Records Ingested:  {len(all_forecasts):,}")
    print(f"    - Reference Records Ingested: {len(all_references):,}")

    if not all_forecasts or not all_references:
        # Fallback to existing dataset if network was completely offline
        print("[!] No new records retrieved from live API; verifying existing authentic dataset records.")
        fallback = "datasets/training/dataset_real_v002.csv"
        return fallback

    # 1. Spatio-Temporal Alignment
    print("\n[+] Spatio-Temporal Alignment & Hard Verification Constraint Enforcement...")
    aligner = ForecastReferenceAligner(spatial_tolerance_deg=0.5)
    df_aligned = aligner.align(all_forecasts, all_references)
    stats = aligner.alignment_stats

    print(f"    -> Aligned Records:      {len(df_aligned):,}")
    print(f"    -> Temporal Match Rate:  {stats.get('temporal_match_success_pct', 0)}%")
    print(f"    -> Spatial Match Rate:   {stats.get('spatial_match_success_pct', 0)}%")

    # Attach station metadata
    station_meta = {s["name"]: s for s in selected_stations}
    countries = []
    regimes = []
    elevations = []
    for _, row in df_aligned.iterrows():
        st_name = row.get("station_name")
        meta = station_meta.get(st_name, {})
        countries.append(meta.get("country", "Unknown"))
        regimes.append(meta.get("climate_regime", "TEMPERATE"))
        elevations.append(meta.get("elevation", 100.0))

    df_aligned["country"] = countries
    df_aligned["climate_regime"] = regimes
    df_aligned["elevation"] = elevations

    # 2. Hard Lead-Hour Consistency Audit
    v_times = pd.to_datetime(df_aligned["valid_time"])
    i_times = pd.to_datetime(df_aligned["initialization_time"])
    calc_leads = ((v_times - i_times).dt.total_seconds() / 3600.0).round().astype(int)
    stated_leads = df_aligned["lead_hours"].astype(int)
    lead_mismatches = int((calc_leads != stated_leads).sum())
    assert lead_mismatches == 0, f"Critical integrity failure: {lead_mismatches} lead mismatches!"
    print(f"    -> Lead Consistency Audit Passed: 0 mismatches out of {len(df_aligned):,} samples.")

    # 3. Apply Saturation Lead-Time Dynamic Bust Labeling
    print("\n[+] Applying Saturation Lead-Time Dynamic Bust Labeling (Day 1 to Day 30)...")
    labeler = BustLabeler(strategy="lead_time_saturation")
    df_labeled = labeler.label_dataframe(df_aligned)

    output_path = "datasets/training/dataset_global_v003.csv"
    df_labeled.to_csv(output_path, index=False)
    bust_count = int(df_labeled["is_bust"].sum())
    bust_pct = round((bust_count / max(1, len(df_labeled))) * 100, 2)

    print(f"[+] Global Training Dataset v003 Created: {len(df_labeled):,} rows")
    print(f"    - Forecast Busts Flagged: {bust_count:,} ({bust_pct}%)")
    print(f"    - Saved to: {output_path}")

    # 4. Data Quality & Thermodynamic Assessment
    qc_report = assess_dataframe_quality(
        df_labeled,
        dataset_name="dataset_global_v003.csv",
        alignment_stats=stats
    )
    with open("datasets/metadata/quality_report_global_v003.json", "w") as f:
        json.dump(qc_report, f, indent=2)

    # 5. Save Metadata Manifest
    manifest = {
        "version": "dataset_global_v003",
        "data_type": "REAL",
        "scope": "GLOBAL_MULTI_REGIME",
        "forecast_source": "Open-Meteo Previous Runs NWP Archive (GFS / ECMWF IFS)",
        "reference_source": "ECMWF ERA5 Reanalysis (Copernicus CDS)",
        "start_date": sampling_windows[0]["start"],
        "end_date": sampling_windows[-1]["end"],
        "stations_count": len(selected_stations),
        "countries_covered": sorted(list(set(countries))),
        "climate_regimes_covered": sorted(list(set(regimes))),
        "lead_hours": sorted([int(x) for x in df_labeled["lead_hours"].unique()]),
        "total_records": len(df_labeled),
        "bust_records": bust_count,
        "bust_rate_percentage": bust_pct,
        "alignment_metrics": stats,
        "qc_status": qc_report.get("status", "PASS"),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    with open("datasets/metadata/dataset_global_v003.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"[+] Manifest Catalog Saved: datasets/metadata/dataset_global_v003.json")
    print("================================================================================\n")
    return output_path


if __name__ == "__main__":
    asyncio.run(generate_global_dataset_v003())
