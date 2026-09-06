"""
Spatio-Temporal Forecast and Reference Alignment Engine.
Aligns genuine NWP forecasts initialized at time T for valid time T + tau
with realized ground truth observation/reanalysis at valid time T + tau.
Enforces strict date and spatial validation:
1. Hard constraint: reference.valid_time == forecast.valid_time
2. Hard constraint: lead_hours == (valid_time - initialization_time)
3. Spatial nearest-neighbor matching within <= 0.5 degrees tolerance
4. Tracks unmatched forecasts and match percentages for QC certification
"""
from typing import List, Dict, Any, Tuple
from datetime import datetime
import pandas as pd
import numpy as np


class ForecastReferenceAligner:
    def __init__(self, spatial_tolerance_deg: float = 0.5):
        self.spatial_tolerance = spatial_tolerance_deg
        self.method_used = f"Nearest Neighbor within <= {spatial_tolerance_deg}°"
        self.alignment_stats = {}

    def align(self, forecasts: List[Dict[str, Any]], references: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Aligns forecasts and references into unified tabular records.
        Calculates authentic forecast errors for all verified variables.
        """
        if not forecasts or not references:
            self.alignment_stats = {
                "total_forecasts": len(forecasts),
                "total_references": len(references),
                "matched_records": 0,
                "unmatched_forecasts": len(forecasts),
                "temporal_match_success_pct": 0.0,
                "spatial_match_success_pct": 0.0
            }
            return pd.DataFrame()

        df_fc = pd.DataFrame(forecasts)
        df_ref = pd.DataFrame(references)

        # Standardize timestamp formats
        df_fc["valid_time_dt"] = pd.to_datetime(df_fc["valid_time"])
        df_ref["valid_time_dt"] = pd.to_datetime(df_ref["valid_time"])

        if "initialization_time" in df_fc.columns:
            df_fc["init_time_dt"] = pd.to_datetime(df_fc["initialization_time"])

        aligned_rows = []
        unmatched_temporal = 0
        unmatched_spatial = 0
        unmatched_lead = 0

        # Group references by valid time for fast spatio-temporal lookup
        ref_by_time = df_ref.groupby("valid_time_dt")

        for _, fc_row in df_fc.iterrows():
            v_time = fc_row["valid_time_dt"]
            fc_lat = float(fc_row["latitude"])
            fc_lon = float(fc_row["longitude"])
            fc_lead = int(fc_row["lead_hours"])

            # 1. Hard Temporal Validation
            if v_time not in ref_by_time.groups:
                unmatched_temporal += 1
                continue

            # 2. Hard Lead-Time Consistency Check
            if "init_time_dt" in fc_row and pd.notnull(fc_row["init_time_dt"]):
                lead_calc = int((v_time - fc_row["init_time_dt"]).total_seconds() // 3600)
                # Must match within 1 hour tolerance (accounting for daylight saving or rounding)
                if abs(lead_calc - fc_lead) > 1:
                    unmatched_lead += 1
                    continue

            matching_refs = ref_by_time.get_group(v_time)

            # 3. Spatial Distance Filter (Euclidean approximation for small regional offsets)
            dists = np.sqrt(
                (matching_refs["latitude"] - fc_lat) ** 2 +
                (matching_refs["longitude"] - fc_lon) ** 2
            )

            min_idx = dists.idxmin()
            min_dist = dists.loc[min_idx]

            if min_dist > self.spatial_tolerance:
                unmatched_spatial += 1
                continue

            best_ref = matching_refs.loc[min_idx]

            # 4. Calculate Real Forecast Errors
            t_fc = fc_row.get("temperature_2m")
            t_ref = best_ref.get("temperature_2m")
            t_err = round(abs(t_fc - t_ref), 3) if (t_fc is not None and t_ref is not None) else None

            p_fc = fc_row.get("precipitation")
            p_ref = best_ref.get("precipitation")
            p_err = round(abs(p_fc - p_ref), 3) if (p_fc is not None and p_ref is not None) else None

            w_fc = fc_row.get("wind_speed_10m")
            w_ref = best_ref.get("wind_speed_10m")
            w_err = round(abs(w_fc - w_ref), 3) if (w_fc is not None and w_ref is not None) else None

            mslp_fc = fc_row.get("pressure_msl")
            mslp_ref = best_ref.get("pressure_msl")
            mslp_err = round(abs(mslp_fc - mslp_ref), 3) if (mslp_fc is not None and mslp_ref is not None) else None

            rh_fc = fc_row.get("relative_humidity_2m")
            rh_ref = best_ref.get("relative_humidity_2m")
            rh_err = round(abs(rh_fc - rh_ref), 3) if (rh_fc is not None and rh_ref is not None) else None

            # Determine Data Provenance
            fc_provider = fc_row.get("provider", "unknown")
            ref_source = best_ref.get("source", "unknown")
            data_type = "SYNTHETIC" if "demo" in fc_provider.lower() else "REAL"

            aligned_rows.append({
                "initialization_time": str(fc_row["initialization_time"]),
                "valid_time": str(v_time),
                "lead_hours": fc_lead,
                "latitude": fc_lat,
                "longitude": fc_lon,
                # Provenance tags
                "forecast_provider": fc_provider,
                "forecast_model": fc_row.get("model", "nwp"),
                "reference_source": ref_source,
                "data_type": data_type,
                # Forecasted features (available at initialization)
                "forecast_temperature": t_fc,
                "forecast_precipitation": p_fc,
                "forecast_wind": w_fc,
                "forecast_pressure": mslp_fc,
                "forecast_humidity": rh_fc,
                "forecast_cloud_cover": fc_row.get("cloud_cover"),
                "ensemble_spread": fc_row.get("ensemble_spread", 0.0),
                "run_revision": fc_row.get("run_revision", 0.0),
                # Ground truth Reference values (for error & bust labeling ONLY)
                "reference_temperature": t_ref,
                "reference_precipitation": p_ref,
                "reference_wind": w_ref,
                "reference_pressure": mslp_ref,
                "reference_humidity": rh_ref,
                # Real Errors
                "error_temperature": t_err,
                "error_precipitation": p_err,
                "error_wind": w_err,
                "error_pressure": mslp_err,
                "error_humidity": rh_err,
                "alignment_method": self.method_used,
                "spatial_offset_deg": round(float(min_dist), 4)
            })

        matched_count = len(aligned_rows)
        total_fc = len(df_fc)
        total_ref = len(df_ref)
        unmatched_total = total_fc - matched_count

        self.alignment_stats = {
            "total_forecasts": total_fc,
            "total_references": total_ref,
            "matched_records": matched_count,
            "unmatched_forecasts": unmatched_total,
            "unmatched_temporal": unmatched_temporal,
            "unmatched_spatial": unmatched_spatial,
            "unmatched_lead_inconsistency": unmatched_lead,
            "temporal_match_success_pct": round((1 - unmatched_temporal / max(1, total_fc)) * 100, 2),
            "spatial_match_success_pct": round((1 - unmatched_spatial / max(1, total_fc)) * 100, 2)
        }

        return pd.DataFrame(aligned_rows)
