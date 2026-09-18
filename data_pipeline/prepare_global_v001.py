"""
Global Authentic NWP-ERA5 Historical Dataset Expansion Engine (Version 001).
SIH26079 – AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts.

Expands historical training dataset from ~37,800 records to 500,000+ authentic records
across 200 globally distributed synoptic stations covering 6 continents,
5 Köppen climate regimes, and diverse geographic categories.

STRICT INTEGRITY RULES:
1. Zero synthetic or fabricated records.
2. Zero duplicates: verified via deterministic key (station_id + forecast_model + T0 + lead_hours).
3. Spatio-temporal alignment: forecast.valid_time == reference.valid_time, lead_hours == valid_time - T0.
4. Frozen test set (dataset_real_v002.csv) remains completely isolated and untouched.
5. ML models remain untouched.
"""
import os
import sys
import json
import time
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Set
import pandas as pd
import numpy as np

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_pipeline.providers.historical_nwp import HistoricalNWPProvider
from data_pipeline.providers.era5 import ERA5CDSProvider
from data_pipeline.quality import assess_dataframe_quality
from data_pipeline.labeler import BustLabeler, get_lead_time_group


# 5 Multi-year seasonal windows spanning 2024, 2025, and 2026
SAMPLING_WINDOWS = [
    {"name": "2024_Monsoon_Summer", "start": "2024-07-10", "end": "2024-07-12"},
    {"name": "2024_PostMonsoon_Autumn", "start": "2024-11-15", "end": "2024-11-17"},
    {"name": "2025_PreMonsoon_Spring", "start": "2025-04-10", "end": "2025-04-12"},
    {"name": "2025_PeakMonsoon_Summer", "start": "2025-08-05", "end": "2025-08-07"},
    {"name": "2026_Winter", "start": "2026-01-15", "end": "2026-01-17"}
]

# Forecast lead days to request (Days 1 to 7 = 24h to 168h)
LEAD_DAYS = [1, 2, 3, 4, 5, 6, 7]


class GlobalDatasetPipeline:
    def __init__(
        self,
        stations_config_path: str = "data_pipeline/config/stations_global_200.json",
        output_csv_path: str = "datasets/training/dataset_global_v001.csv",
        cache_dir: str = "datasets/raw/cache",
        num_workers: int = 4
    ):
        self.stations_config_path = stations_config_path
        self.output_csv_path = output_csv_path
        self.cache_dir = cache_dir
        self.num_workers = num_workers
        self.nwp_provider = HistoricalNWPProvider(model="gfs_seamless", timeout=30.0)
        self.era5_provider = ERA5CDSProvider(timeout=30.0)
        self.labeler = BustLabeler(strategy="lead_time_dynamic")
        self.seen_keys: Set[str] = set()
        self.duplicate_count: int = 0
        self.failure_log: List[Dict[str, Any]] = []
        self.total_written: int = 0
        self.stations_completed: int = 0
        self.write_lock = asyncio.Lock()
        self.seen_lock = asyncio.Lock()
        self.log_lock = asyncio.Lock()

        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.output_csv_path), exist_ok=True)
        os.makedirs("datasets/metadata", exist_ok=True)

    def load_stations(self) -> List[Dict[str, Any]]:
        with open(self.stations_config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    async def fetch_with_retry(self, coro_func, *args, retries: int = 4, backoff: float = 2.0):
        for attempt in range(1, retries + 1):
            try:
                res = await coro_func(*args)
                await asyncio.sleep(0.20)  # Polite pacing
                return res
            except Exception as e:
                err_str = str(e)
                if "429" in err_str:
                    print(f"\n[!] Rate Limit (429) encountered. Pausing for 65s cooldown (attempt {attempt}/{retries})...", flush=True)
                    await asyncio.sleep(65.0)
                    continue
                if attempt == retries:
                    raise e
                wait_time = backoff * (2 ** (attempt - 1))
                await asyncio.sleep(wait_time)

    async def get_station_window_forecasts(
        self, station: Dict[str, Any], window: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        sid = station["station_id"]
        w_name = window["name"]
        cache_file = os.path.join(self.cache_dir, f"nwp_{sid}_{w_name}.json")

        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        fc_objs = await self.fetch_with_retry(
            self.nwp_provider.get_historical_forecast,
            station["lat"], station["lon"], window["start"], window["end"]
        )
        fc_dicts = [fc.model_dump(mode="json") for fc in fc_objs]

        # Cache raw payload
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(fc_dicts, f)

        return fc_dicts

    async def get_station_window_references(
        self, station: Dict[str, Any], window: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        sid = station["station_id"]
        w_name = window["name"]
        cache_file = os.path.join(self.cache_dir, f"era5_{sid}_{w_name}.json")

        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        ref_objs = await self.fetch_with_retry(
            self.era5_provider.get_reference_data,
            station["lat"], station["lon"], window["start"], window["end"]
        )
        ref_dicts = [ref.model_dump(mode="json") for ref in ref_objs]

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(ref_dicts, f)

        return ref_dicts

    async def align_and_label_records(
        self,
        station: Dict[str, Any],
        forecasts: List[Dict[str, Any]],
        references: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        if not forecasts or not references:
            return pd.DataFrame()

        ref_map = {}
        for r in references:
            vt = r["valid_time"]
            ref_map[vt] = r

        aligned_rows = []

        for fc in forecasts:
            vt = fc["valid_time"]
            if vt not in ref_map:
                continue

            ref = ref_map[vt]
            lead_h = int(fc["lead_hours"])

            # 1. Deterministic Deduplication Check
            # Key: station_id + forecast_model + T0 + lead_hours
            init_t = fc["initialization_time"]
            model = fc.get("model", "gfs_seamless")
            dedup_key = f"{station['station_id']}_{model}_{init_t}_{lead_h}"

            async with self.seen_lock:
                if dedup_key in self.seen_keys:
                    self.duplicate_count += 1
                    continue
                self.seen_keys.add(dedup_key)

            # 2. Hard Temporal Alignment Audit
            vt_dt = datetime.fromisoformat(vt)
            it_dt = datetime.fromisoformat(init_t)
            calc_lead = int(round((vt_dt - it_dt).total_seconds() / 3600.0))
            if abs(calc_lead - lead_h) > 0:
                continue

            # 3. Forecast Errors
            t_fc = fc.get("temperature_2m")
            t_ref = ref.get("temperature_2m")
            t_err = round(abs(t_fc - t_ref), 3) if (t_fc is not None and t_ref is not None) else None

            p_fc = fc.get("precipitation")
            p_ref = ref.get("precipitation")
            p_err = round(abs(p_fc - p_ref), 3) if (p_fc is not None and p_ref is not None) else None

            w_fc = fc.get("wind_speed_10m")
            w_ref = ref.get("wind_speed_10m")
            w_err = round(abs(w_fc - w_ref), 3) if (w_fc is not None and w_ref is not None) else None

            mslp_fc = fc.get("pressure_msl")
            mslp_ref = ref.get("pressure_msl")
            mslp_err = round(abs(mslp_fc - mslp_ref), 3) if (mslp_fc is not None and mslp_ref is not None) else None

            rh_fc = fc.get("relative_humidity_2m")
            rh_ref = ref.get("relative_humidity_2m")
            rh_err = round(abs(rh_fc - rh_ref), 3) if (rh_fc is not None and rh_ref is not None) else None

            aligned_rows.append({
                "station_id": station["station_id"],
                "station_name": station["name"],
                "country": station["country"],
                "continent": station["continent"],
                "climate_category": station["climate_category"],
                "geographic_category": station["geographic_category"],
                "elevation": station["elevation"],
                "initialization_time": init_t,
                "valid_time": vt,
                "lead_hours": lead_h,
                "latitude": station["lat"],
                "longitude": station["lon"],
                "forecast_provider": fc.get("provider", "open-meteo-previous-runs"),
                "forecast_model": model,
                "reference_source": ref.get("source", "era5-reanalysis"),
                "data_type": "REAL",
                "forecast_temperature": t_fc,
                "forecast_precipitation": p_fc,
                "forecast_wind": w_fc,
                "forecast_pressure": mslp_fc,
                "forecast_humidity": rh_fc,
                "forecast_cloud_cover": fc.get("cloud_cover"),
                "ensemble_spread": fc.get("ensemble_spread", 0.0),
                "run_revision": fc.get("run_revision", 0.0),
                "reference_temperature": t_ref,
                "reference_precipitation": p_ref,
                "reference_wind": w_ref,
                "reference_pressure": mslp_ref,
                "reference_humidity": rh_ref,
                "error_temperature": t_err,
                "error_precipitation": p_err,
                "error_wind": w_err,
                "error_pressure": mslp_err,
                "error_humidity": rh_err,
                "alignment_method": "Exact Coordinate + Exact Valid Time Match",
                "spatial_offset_deg": 0.0
            })

        if not aligned_rows:
            return pd.DataFrame()

        df_chunk = pd.DataFrame(aligned_rows)
        df_labeled = self.labeler.label_dataframe(df_chunk)
        return df_labeled

    async def _station_worker(self, queue: asyncio.Queue, total_stations: int):
        while not queue.empty():
            try:
                s_idx, station = queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            s_name = station["name"]
            sid = station["station_id"]
            country = station["country"]
            cont = station["continent"]

            station_rows = []
            station_errors = 0

            for window in SAMPLING_WINDOWS:
                w_name = window["name"]
                try:
                    fcs = await self.get_station_window_forecasts(station, window)
                    refs = await self.get_station_window_references(station, window)
                    df_w = await self.align_and_label_records(station, fcs, refs)
                    if not df_w.empty:
                        station_rows.append(df_w)
                except Exception as e:
                    station_errors += 1
                    async with self.log_lock:
                        self.failure_log.append({
                            "station_id": sid,
                            "station_name": s_name,
                            "window": w_name,
                            "error": str(e),
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })

            if station_rows:
                df_station = pd.concat(station_rows, ignore_index=True)
                async with self.write_lock:
                    is_first = (self.total_written == 0)
                    df_station.to_csv(
                        self.output_csv_path,
                        mode="w" if is_first else "a",
                        header=is_first,
                        index=False
                    )
                    self.total_written += len(df_station)
                    self.stations_completed += 1
                    pct = (self.stations_completed / total_stations) * 100
                    print(f"[{self.stations_completed:3d}/{total_stations:3d} ({pct:5.1f}%)] "
                          f"Saved {s_name}, {country} ({cont}) -> +{len(df_station):,} rows | Total: {self.total_written:,}")
            else:
                async with self.write_lock:
                    self.stations_completed += 1
                    print(f"[{self.stations_completed:3d}/{total_stations:3d}] "
                          f"FAILED {s_name}, {country} ({station_errors} window errors)")

            queue.task_done()

    async def run_pipeline(self, max_stations: Optional[int] = None) -> str:
        t_start = time.time()
        stations = self.load_stations()
        if max_stations:
            stations = stations[:max_stations]

        total_stations = len(stations)
        total_windows = len(SAMPLING_WINDOWS)
        expected_records = total_stations * total_windows * 504

        print("\n" + "=" * 85)
        print("    MASSIVE AUTHENTIC DATASET EXPANSION (GLOBAL V001)")
        print(f"    Target Stations: {total_stations} stations across 6 continents")
        print(f"    Windows:         {total_windows} multi-year seasonal windows")
        print(f"    Expected Rows:   ~{expected_records:,} authentic records")
        print(f"    Concurrency:     {self.num_workers} parallel async workers")
        print(f"    Output Path:     {self.output_csv_path}")
        print("=" * 85 + "\n")

        # Reset output file
        if os.path.exists(self.output_csv_path):
            os.remove(self.output_csv_path)

        queue = asyncio.Queue()
        for idx, s in enumerate(stations, 1):
            queue.put_nowait((idx, s))

        workers = [
            asyncio.create_task(self._station_worker(queue, total_stations))
            for _ in range(self.num_workers)
        ]
        await asyncio.gather(*workers)

        elapsed = time.time() - t_start
        print("\n" + "=" * 85)
        print(f"[+] INGESTION COMPLETE in {elapsed:.1f}s ({elapsed / 60:.1f} min)")
        print(f"[+] Total Authentic Records Written: {self.total_written:,}")
        print(f"[+] Total Duplicate Records Found:    {self.duplicate_count}")
        assert self.duplicate_count == 0, f"Critical failure: {self.duplicate_count} duplicates detected!"
        print("=" * 85 + "\n")

        # Save Failure Log
        with open("datasets/metadata/failure_log_global_v001.json", "w", encoding="utf-8") as f:
            json.dump({
                "failure_count": len(self.failure_log),
                "failures": self.failure_log
            }, f, indent=2)

        # Generate Quality Audit & Manifest
        self.generate_audit_and_manifest(self.total_written, stations)

        return self.output_csv_path

    def generate_audit_and_manifest(self, total_records: int, stations: List[Dict[str, Any]]):
        print("[*] Generating Data Quality Audit & Metadata Manifest...")
        df = pd.read_csv(self.output_csv_path)

        # 1. Quality Assessment
        qc_report = assess_dataframe_quality(
            df,
            dataset_name="dataset_global_v001.csv",
            is_global=True
        )
        with open("datasets/metadata/quality_report_global_v001.json", "w", encoding="utf-8") as f:
            json.dump(qc_report, f, indent=2)

        # 2. Comprehensive Statistics for Final Report
        records_per_continent = df["continent"].value_counts().to_dict()
        records_per_country = df["country"].value_counts().to_dict()
        records_per_regime = df["climate_category"].value_counts().to_dict()
        records_per_geo = df["geographic_category"].value_counts().to_dict()
        records_per_lead = df["lead_hours"].value_counts().to_dict()
        df["_year"] = pd.to_datetime(df["valid_time"]).dt.year
        records_per_year = df["_year"].value_counts().to_dict()
        bust_records = int(df["is_bust"].sum())
        bust_rate = round((bust_records / max(1, len(df))) * 100, 2)

        # 3. Manifest
        manifest = {
            "dataset_version": "dataset_global_v001",
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
            "data_type": "AUTHENTIC_HISTORICAL_NWP_ERA5",
            "synthetic_records_count": 0,
            "forecast_source": "Open-Meteo Previous Runs NWP Archive (GFS Seamless)",
            "forecast_model": "gfs_seamless",
            "reference_source": "ECMWF ERA5 Reanalysis (Copernicus CDS)",
            "station_count": len(stations),
            "country_count": len(records_per_country),
            "continent_count": len(records_per_continent),
            "sampling_windows": SAMPLING_WINDOWS,
            "date_range": {
                "start": str(df["valid_time"].min()),
                "end": str(df["valid_time"].max())
            },
            "lead_hours_present": sorted([int(k) for k in records_per_lead.keys()]),
            "total_records": total_records,
            "duplicate_records": self.duplicate_count,
            "bust_records": bust_records,
            "natural_bust_prevalence_pct": bust_rate,
            "distribution": {
                "records_per_continent": {str(k): int(v) for k, v in records_per_continent.items()},
                "records_per_country": {str(k): int(v) for k, v in records_per_country.items()},
                "records_per_climate_regime": {str(k): int(v) for k, v in records_per_regime.items()},
                "records_per_geographic_category": {str(k): int(v) for k, v in records_per_geo.items()},
                "records_per_lead_time": {str(k): int(v) for k, v in records_per_lead.items()},
                "records_per_year": {str(k): int(v) for k, v in records_per_year.items()}
            },
            "qc_status": qc_report.get("status", "PASS")
        }

        with open("datasets/metadata/manifest_global_v001.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        print("[+] Manifest saved: datasets/metadata/manifest_global_v001.json")
        print("[+] Quality report saved: datasets/metadata/quality_report_global_v001.json")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Global NWP-ERA5 Dataset Generator")
    parser.add_argument("--max-stations", type=int, default=None, help="Limit number of stations (for testing)")
    parser.add_argument("--workers", type=int, default=4, help="Concurrent worker count")
    args = parser.parse_args()

    pipeline = GlobalDatasetPipeline(num_workers=args.workers)
    asyncio.run(pipeline.run_pipeline(max_stations=args.max_stations))
