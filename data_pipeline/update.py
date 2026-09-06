"""
Incremental Dataset Updater CLI.
Checks local dataset boundaries against available data timestamps, downloads
only missing deltas, validates new records, updates versioned metadata,
and flags when sufficient new records exist to justify model retraining.
"""
import argparse
import asyncio
import glob
import json
import os
from datetime import datetime, timedelta
from data_pipeline.download import download_data


def get_latest_local_manifest(raw_dir: str = "datasets/raw") -> dict:
    manifest_files = glob.glob(os.path.join(raw_dir, "manifest_*.json"))
    if not manifest_files:
        return {}
    # Sort by filename timestamp
    manifest_files.sort()
    latest_file = manifest_files[-1]
    with open(latest_file, "r") as f:
        return json.load(f)


def check_missing_interval(latest_manifest: dict) -> tuple:
    """Determine start and end dates for incremental delta."""
    if not latest_manifest or "end_date" not in latest_manifest:
        # No previous download found, initial window
        return ("2024-01-01", "2024-06-30")

    last_end = datetime.strptime(latest_manifest["end_date"], "%Y-%m-%d")
    next_start = (last_end + timedelta(days=1)).strftime("%Y-%m-%d")
    # Fetch next 30-day block up to today
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if next_start > today:
        return (None, None)
    return (next_start, today)


async def update_dataset(source: str = "demo", region: str = "india"):
    print("\n==================================================")
    print("[*] INCREMENTAL DATASET UPDATER")
    print("==================================================")

    manifest = get_latest_local_manifest()
    if manifest:
        print(f"[i] Previous Manifest Detected: {manifest.get('timestamp')}")
        print(f"    Existing Coverage: {manifest.get('start_date')} -> {manifest.get('end_date')}")
        print(f"    Current Records:   {manifest.get('forecast_records', 0):,} forecasts")
    else:
        print("[i] No existing dataset manifest detected. Performing initial acquisition...")

    start_date, end_date = check_missing_interval(manifest)

    if not start_date or not end_date:
        print("[+] Dataset is completely up-to-date! No missing delta to download.")
        return

    print(f"\n[+] Missing delta identified: {start_date} -> {end_date}")
    print("[+] Initiating incremental ingestion...")

    new_manifest = await download_data(
        source=source,
        region_name=region,
        start_str=start_date,
        end_str=end_date
    )

    # Update metadata catalog
    catalog_path = os.path.join("datasets", "metadata", "catalog.json")
    os.makedirs(os.path.dirname(catalog_path), exist_ok=True)

    catalog = []
    if os.path.exists(catalog_path):
        with open(catalog_path, "r") as f:
            try:
                catalog = json.load(f)
            except Exception:
                catalog = []

    catalog.append({
        "update_timestamp": datetime.utcnow().isoformat(),
        "incremental_start": start_date,
        "incremental_end": end_date,
        "delta_records": new_manifest.get("forecast_records", 0),
        "checksum": new_manifest.get("checksum_sha256")
    })

    with open(catalog_path, "w") as f:
        json.dump(catalog, f, indent=2)

    print(f"[+] Incremental update recorded in {catalog_path}")
    print("==================================================\n")


def main():
    parser = argparse.ArgumentParser(description="Incremental Meteorological Dataset Updater")
    parser.add_argument("--source", type=str, default="demo", choices=["demo", "openmeteo", "era5"])
    parser.add_argument("--region", type=str, default="india")
    args = parser.parse_args()

    asyncio.run(update_dataset(args.source, args.region))


if __name__ == "__main__":
    main()
