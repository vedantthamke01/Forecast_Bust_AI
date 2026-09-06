"""
Configurable Forecast Bust Labeling Engine.
Implements the 4 scientific bust labeling strategies:
1. Absolute Error Thresholding
2. Climatological Percentile Thresholding
3. Lead-Time Dependent Dynamic Thresholding
4. Multi-Variable Compound Thresholding
Every output record explicitly records its labeling strategy and threshold value.
"""
import argparse
import glob
import os
import pandas as pd
import numpy as np


class BustLabeler:
    def __init__(
        self,
        strategy: str = "lead_time_dynamic",
        rain_thresh_base: float = 25.0,     # mm
        temp_thresh_base: float = 4.0,      # °C
        wind_thresh_base: float = 8.5,      # m/s
        lead_scaling_factor: float = 0.12,  # +12% threshold allowance per 24h lead
        percentile_cutoff: float = 95.0
    ):
        self.strategy = strategy
        self.rain_base = rain_thresh_base
        self.temp_base = temp_thresh_base
        self.wind_base = wind_thresh_base
        self.lead_scaling = lead_scaling_factor
        self.percentile = percentile_cutoff

    def get_dynamic_threshold(self, base_thresh: float, lead_hours: int) -> float:
        """Scales threshold with lead horizon tau (e.g., 24h to 240h)."""
        days_beyond_day1 = max(0, (lead_hours - 24) / 24.0)
        return round(base_thresh * (1.0 + self.lead_scaling * days_beyond_day1), 2)

    def label_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df

        df = df.copy()

        # Compute percentile cutoffs if strategy is percentile
        p95_rain = np.percentile(df["error_precipitation"].dropna(), self.percentile) if "error_precipitation" in df.columns and len(df["error_precipitation"].dropna()) > 0 else self.rain_base
        p95_temp = np.percentile(df["error_temperature"].dropna(), self.percentile) if "error_temperature" in df.columns and len(df["error_temperature"].dropna()) > 0 else self.temp_base
        p95_wind = np.percentile(df["error_wind"].dropna(), self.percentile) if "error_wind" in df.columns and len(df["error_wind"].dropna()) > 0 else self.wind_base

        is_bust_list = []
        severity_list = []
        method_list = []
        threshold_val_list = []

        for _, row in df.iterrows():
            lead_h = int(row.get("lead_hours", 24))
            p_err = row.get("error_precipitation") or 0.0
            t_err = row.get("error_temperature") or 0.0
            w_err = row.get("error_wind") or 0.0

            if self.strategy == "absolute":
                rain_th = self.rain_base
                temp_th = self.temp_base
                wind_th = self.wind_base
                method = "ABSOLUTE_THRESHOLD"
            elif self.strategy == "percentile":
                rain_th = float(p95_rain)
                temp_th = float(p95_temp)
                wind_th = float(p95_wind)
                method = f"PERCENTILE_{int(self.percentile)}TH"
            elif self.strategy == "lead_time_dynamic":
                rain_th = self.get_dynamic_threshold(self.rain_base, lead_h)
                temp_th = self.get_dynamic_threshold(self.temp_base, lead_h)
                wind_th = self.get_dynamic_threshold(self.wind_base, lead_h)
                method = f"DYNAMIC_HORIZON_SCALED"
            elif self.strategy == "compound":
                rain_th = self.get_dynamic_threshold(self.rain_base, lead_h)
                temp_th = self.get_dynamic_threshold(self.temp_base, lead_h)
                wind_th = self.get_dynamic_threshold(self.wind_base, lead_h)
                method = "MULTI_VARIABLE_COMPOUND"
            else:
                rain_th = self.rain_base
                temp_th = self.temp_base
                wind_th = self.wind_base
                method = "ABSOLUTE_THRESHOLD"

            # Check individual variable bust conditions
            bust_rain = p_err > rain_th
            bust_temp = t_err > temp_th
            bust_wind = w_err > wind_th

            # Bust determination logic
            if self.strategy == "compound":
                is_bust = bust_rain or (bust_temp and bust_wind)
            else:
                # By default in medium-range synoptic forecasts, rainfall is primary, with temp/wind high impact
                is_bust = bust_rain or bust_temp or bust_wind

            # Severity determination
            max_ratio = max(p_err / max(1e-3, rain_th), t_err / max(1e-3, temp_th), w_err / max(1e-3, wind_th))
            if not is_bust:
                severity = "NONE"
            elif max_ratio >= 2.0:
                severity = "EXTREME"
            elif max_ratio >= 1.5:
                severity = "SEVERE"
            else:
                severity = "MODERATE"

            is_bust_list.append(int(is_bust))
            severity_list.append(severity)
            method_list.append(method)
            threshold_val_list.append(rain_th)

        df["is_bust"] = is_bust_list
        df["bust_severity"] = severity_list
        df["labeling_method"] = method_list
        df["operational_threshold"] = threshold_val_list

        return df


def run_labeling(strategy: str = "lead_time_dynamic", input_path: str = None, output_path: str = None):
    print("\n==================================================")
    print(f"[*] BUST LABELING ENGINE: Strategy = {strategy.upper()}")
    print("==================================================")

    if not input_path:
        csv_files = glob.glob("datasets/processed/*.csv")
        if not csv_files:
            print("[-] No processed dataset found. Run setup_data or alignment first.")
            return
        input_path = csv_files[-1]

    df = pd.read_csv(input_path)
    labeler = BustLabeler(strategy=strategy)
    df_labeled = labeler.label_dataframe(df)

    if not output_path:
        os.makedirs("datasets/training", exist_ok=True)
        output_path = os.path.join("datasets", "training", f"training_labeled_{strategy}.csv")

    df_labeled.to_csv(output_path, index=False)
    bust_count = int(df_labeled["is_bust"].sum())
    total_count = len(df_labeled)
    bust_pct = round((bust_count / max(1, total_count)) * 100, 2)

    print(f"[+] Records Processed:     {total_count:,}")
    print(f"[+] Forecast Busts Flagged: {bust_count:,} ({bust_pct}%)")
    print(f"[+] Labeling Method Saved: {df_labeled['labeling_method'].iloc[0] if total_count > 0 else 'N/A'}")
    print(f"[+] Training Set Created:  {output_path}")
    print("==================================================\n")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Forecast Bust Labeling Engine")
    parser.add_argument("--strategy", type=str, default="lead_time_dynamic",
                        choices=["absolute", "percentile", "lead_time_dynamic", "compound"])
    parser.add_argument("--input", type=str, default=None)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()
    run_labeling(args.strategy, args.input, args.output)
