"""
Automated Meteorological Dataset Downloader CLI.
Retrieves authentic NWP forecasts, ERA5 reanalysis observations, or benchmark scenarios.
STRICT SEPARATION:
- source 'era5': Downloads genuine ERA5 reanalysis references ONLY.
- source 'historical_nwp': Downloads genuine past NWP model runs (GFS / ECMWF IFS) with real initializations.
- source 'openmeteo': Downloads current operational 10-day forecast.
- source 'demo': Synthetic benchmark generator for air-gapped demo only.
"""
import argparse
import asyncio
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta
import yaml

from data_pipeline.providers.base import NormalizedForecast, NormalizedReference
from data_pipeline.providers.open_meteo import OpenMeteoProvider
from data_pipeline.providers.demo_provider import DemoProvider
from data_pipeline.providers.era5 import ERA5CDSProvider
from data_pipeline.providers.historical_nwp import HistoricalNWPProvider
from data_pipeline.providers.geocoding import INDIAN_CITIES_DB


def load_config():
    cfg_path = os.path.join("config", "data_sources.yaml")
    if os.path.exists(cfg_path):
        with open(cfg_path, "r") as f:
            return yaml.safe_load(f)
    return {
        "regions": {
            "india": {"north": 37.5, "south": 6.5, "west": 68.0, "east": 97.5}
        },
        "variables": ["temperature_2m", "precipitation", "wind_speed_10m", "pressure_msl"]
    }


def estimate_download_size(days: int, stations_count: int, num_variables: int) -> float:
    """Estimate raw JSON/CSV size in Megabytes."""
    bytes_est = days * 24 * stations_count * num_variables * 120
    return round(bytes_est / (1024 * 1024), 2)


async def download_data(source: str, region_name: str, start_str: str, end_str: str, output_dir: str = "datasets/raw"):
    cfg = load_config()
    region_info = cfg.get("regions", {}).get(region_name, {"north": 37.5, "south": 6.5, "west": 68.0, "east": 97.5})

    start_date = datetime.strptime(start_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_str, "%Y-%m-%d")
    days_count = max(1, (end_date - start_date).days + 1)

    # Filter stations within region
    stations = [
        c for c in INDIAN_CITIES_DB
        if region_info["south"] <= c["lat"] <= region_info["north"] and
           region_info["west"] <= c["lon"] <= region_info["east"]
    ]

    variables = cfg.get("variables", ["temperature_2m", "precipitation", "wind_speed_10m", "pressure_msl"])
    est_mb = estimate_download_size(days_count, len(stations), len(variables))

    print(f"\n==================================================")
    print(f"[*] DATASET DOWNLOAD JOB INITIATED")
    print(f"==================================================")
    print(f" Source:           {source.upper()}")
    print(f" Region:           {region_name} (Stations: {len(stations)})")
    print(f" Date Range:       {start_str} to {end_str} ({days_count} days)")
    print(f" Variables ({len(variables)}):  {', '.join(variables)}")
    print(f" Target Directory: {output_dir}")
    print(f"==================================================\n")

    os.makedirs(output_dir, exist_ok=True)

    all_forecasts = []
    all_references = []

    print("[+] Ingesting meteorological series across observation stations...")

    if source.lower() == "demo":
        provider = DemoProvider()
        for station in stations:
            lat, lon = station["lat"], station["lon"]
            fc_list = await provider.get_forecast(lat, lon, days=min(10, days_count))
            ref_list = await provider.get_reference_data(lat, lon, start_str, end_str)
            all_forecasts.extend([fc.model_dump(mode="json") for fc in fc_list])
            all_references.extend([ref.model_dump(mode="json") for ref in ref_list])

    elif source.lower() == "era5":
        # Pure ERA5 reanalysis ground truth reference download
        provider = ERA5CDSProvider()
        for station in stations:
            lat, lon = station["lat"], station["lon"]
            print(f"    -> Retrieving ERA5 reference for {station['name']} ({lat:.2f}, {lon:.2f})...")
            ref_list = await provider.get_reference_data(lat, lon, start_str, end_str)
            all_references.extend([ref.model_dump(mode="json") for ref in ref_list])

    elif source.lower() == "historical_nwp":
        # Genuine Historical NWP model forecasts (Days 1 to 10)
        provider = HistoricalNWPProvider()
        for station in stations:
            lat, lon = station["lat"], station["lon"]
            print(f"    -> Retrieving NWP forecasts for {station['name']} ({lat:.2f}, {lon:.2f})...")
            fc_list = await provider.get_historical_forecast(lat, lon, start_str, end_str)
            all_forecasts.extend([fc.model_dump(mode="json") for fc in fc_list])

    elif source.lower() == "openmeteo":
        # Operational current 10-day forecast
        provider = OpenMeteoProvider()
        for station in stations:
            lat, lon = station["lat"], station["lon"]
            fc_list = await provider.get_forecast(lat, lon, days=min(10, days_count))
            all_forecasts.extend([fc.model_dump(mode="json") for fc in fc_list])

    else:
        raise ValueError(f"Unknown source: {source}. Choices: demo, era5, historical_nwp, openmeteo")

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    manifest = {
        "timestamp": timestamp,
        "source": source,
        "region": region_name,
        "start_date": start_str,
        "end_date": end_str,
        "stations_count": len(stations),
        "forecast_records": len(all_forecasts),
        "reference_records": len(all_references),
        "data_type": "SYNTHETIC" if source == "demo" else "REAL"
    }

    if all_forecasts:
        fc_file = os.path.join(output_dir, f"raw_forecasts_{source}_{timestamp}.json")
        with open(fc_file, "w") as f:
            json.dump(all_forecasts, f, indent=2, default=str)
        manifest["forecast_file"] = os.path.abspath(fc_file)

    if all_references:
        ref_file = os.path.join(output_dir, f"raw_references_{source}_{timestamp}.json")
        with open(ref_file, "w") as f:
            json.dump(all_references, f, indent=2, default=str)
        manifest["reference_file"] = os.path.abspath(ref_file)

    manifest_file = os.path.join(output_dir, f"manifest_{source}_{timestamp}.json")
    with open(manifest_file, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n[+] Download Completed Successfully!")
    print(f"    Forecast Records:  {len(all_forecasts):,}")
    print(f"    Reference Records: {len(all_references):,}")
    print(f"    Data Type:         {manifest['data_type']}")
    print(f"    Manifest Saved:    {manifest_file}\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description="NCMRWF Meteorological Dataset Downloader")
    parser.add_argument("--source", type=str, default="demo", choices=["demo", "openmeteo", "era5", "historical_nwp"],
                        help="Data source provider (demo, era5, historical_nwp, openmeteo)")
    parser.add_argument("--region", type=str, default="india", help="Region identifier (default: india)")
    parser.add_argument("--start", type=str, default="2024-06-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, default="2024-06-02", help="End date (YYYY-MM-DD)")
    parser.add_argument("--output", type=str, default="datasets/raw", help="Output directory")

    args = parser.parse_args()
    asyncio.run(download_data(args.source, args.region, args.start, args.end, args.output))


if __name__ == "__main__":
    main()
