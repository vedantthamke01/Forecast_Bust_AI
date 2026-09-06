"""
Spatio-Temporal Forecast and Reference Alignment Engine.
Aligns operational forecast runs initialized at time T for valid time T + N hours
with realized ground truth observation/reanalysis at valid time T + N hours.
Supports:
1. Exact Coordinate / Station matching
2. Nearest-Neighbor spatial interpolation within tolerance radius (0.5 degrees)
"""
from typing import List, Dict, Any, Tuple
from datetime import datetime
import pandas as pd
import numpy as np


class ForecastReferenceAligner:
    def __init__(self, spatial_tolerance_deg: float = 0.5):
        self.spatial_tolerance = spatial_tolerance_deg
        self.method_used = "Nearest Neighbor with Euclidean distance <= 0.5°"

    def align(self, forecasts: List[Dict[str, Any]], references: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Aligns forecasts and references into unified tabular records.
        Calculates forecast errors for all shared variables.
        """
        if not forecasts or not references:
            return pd.DataFrame()

        df_fc = pd.DataFrame(forecasts)
        df_ref = pd.DataFrame(references)

        # Standardize timestamp formats
        df_fc["valid_time_dt"] = pd.to_datetime(df_fc["valid_time"])
        df_ref["valid_time_dt"] = pd.to_datetime(df_ref["valid_time"])

        aligned_rows = []

        # Group references by valid time for fast spatio-temporal lookup
        ref_by_time = df_ref.groupby("valid_time_dt")

        for _, fc_row in df_fc.iterrows():
            v_time = fc_row["valid_time_dt"]
            fc_lat = fc_row["latitude"]
            fc_lon = fc_row["longitude"]

            if v_time not in ref_by_time.groups:
                continue

            matching_refs = ref_by_time.get_group(v_time)

            # Spatial distance filter (Euclidean approximation for small distances)
            dists = np.sqrt(
                (matching_refs["latitude"] - fc_lat) ** 2 +
                (matching_refs["longitude"] - fc_lon) ** 2
            )

            min_idx = dists.idxmin()
            min_dist = dists.loc[min_idx]

            if min_dist <= self.spatial_tolerance:
                best_ref = matching_refs.loc[min_idx]

                # Compute forecast errors
                t_fc = fc_row.get("temperature_2m")
                t_ref = best_ref.get("temperature_2m")
                t_err = abs(t_fc - t_ref) if (t_fc is not None and t_ref is not None) else None

                p_fc = fc_row.get("precipitation")
                p_ref = best_ref.get("precipitation")
                p_err = abs(p_fc - p_ref) if (p_fc is not None and p_ref is not None) else None

                w_fc = fc_row.get("wind_speed_10m")
                w_ref = best_ref.get("wind_speed_10m")
                w_err = abs(w_fc - w_ref) if (w_fc is not None and w_ref is not None) else None

                mslp_fc = fc_row.get("pressure_msl")
                mslp_ref = best_ref.get("pressure_msl")
                mslp_err = abs(mslp_fc - mslp_ref) if (mslp_fc is not None and mslp_ref is not None) else None

                aligned_rows.append({
                    "initialization_time": str(fc_row["initialization_time"]),
                    "valid_time": str(v_time),
                    "lead_hours": int(fc_row["lead_hours"]),
                    "latitude": float(fc_lat),
                    "longitude": float(fc_lon),
                    # Forecasted features
                    "forecast_temperature": t_fc,
                    "forecast_precipitation": p_fc,
                    "forecast_wind": w_fc,
                    "forecast_pressure": mslp_fc,
                    "forecast_humidity": fc_row.get("relative_humidity_2m"),
                    "forecast_cloud_cover": fc_row.get("cloud_cover"),
                    "ensemble_spread": fc_row.get("ensemble_spread", 0.0),
                    "run_revision": fc_row.get("run_revision", 0.0),
                    # Realized Reference observations (for error calculation and labeling ONLY)
                    "reference_temperature": t_ref,
                    "reference_precipitation": p_ref,
                    "reference_wind": w_ref,
                    "reference_pressure": mslp_ref,
                    # Realized Errors
                    "error_temperature": t_err,
                    "error_precipitation": p_err,
                    "error_wind": w_err,
                    "error_pressure": mslp_err,
                    "alignment_method": self.method_used,
                    "spatial_offset_deg": round(float(min_dist), 4)
                })

        return pd.DataFrame(aligned_rows)
