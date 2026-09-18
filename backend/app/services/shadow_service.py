"""
Shadow Mode Inference & Logging Service for Candidate Model Evaluation.
SIH26079 - AI-Based Forecast Bust Detection.

Executes candidate model (global_v001) in strict shadow mode alongside production (model_real_v002).
CRITICAL SAFETY CONSTRAINTS:
1. Zero impact on production API response, probabilities, reliability scores, or UI.
2. Candidate model is completely isolated: never serves user requests.
3. Both models receive the identical T0-available inputs.
4. Non-blocking / fault-tolerant: any shadow error is logged without failing the production request.
5. All shadow inferences are recorded to versioned log: data/shadow/global_v001_shadow_v001.jsonl.
"""
import os
import time
import json
import uuid
import joblib
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

from ml_pipeline.features import extract_features, GLOBAL_FEATURE_COLUMNS


class ShadowInferenceService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ShadowInferenceService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        candidate_bundle_path: str = os.path.join("models", "global_v001", "model_bundle.joblib"),
        log_path: str = os.path.join("data", "shadow", "global_v001_shadow_v001.jsonl")
    ):
        if self._initialized:
            return
        self.candidate_bundle_path = candidate_bundle_path
        self.log_path = log_path
        self.candidate_bundle = None
        self.candidate_model = None
        self.candidate_version = "global_v001"
        self._load_candidate()
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        self._initialized = True

    def _load_candidate(self):
        if os.path.exists(self.candidate_bundle_path):
            try:
                self.candidate_bundle = joblib.load(self.candidate_bundle_path)
                self.candidate_model = self.candidate_bundle.get("calibrated_model")
                self.candidate_version = self.candidate_bundle.get("model_version", "global_v001")
                print(f"[+] ShadowInferenceService: Loaded candidate bundle {self.candidate_version} in SHADOW MODE.")
            except Exception as e:
                print(f"[!] Warning: Could not load candidate shadow model: {e}")
                self.candidate_bundle = None
                self.candidate_model = None
        else:
            self.candidate_bundle = None
            self.candidate_model = None

    def is_available(self) -> bool:
        return self.candidate_model is not None

    def record_shadow_prediction(
        self,
        input_df: pd.DataFrame,
        prod_probability: float,
        prod_latency_ms: float,
        cycle_id: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Executes parallel candidate model inference on identical inputs and logs result.
        Strictly guarded against throwing exceptions to guarantee zero disruption to production.
        """
        if not self.is_available():
            return None

        try:
            t_start = time.perf_counter()
            X_cand, _ = extract_features(
                input_df,
                is_training=False,
                feature_columns=GLOBAL_FEATURE_COLUMNS
            )
            probs = self.candidate_model.predict_proba(X_cand)[:, 1]
            t_end = time.perf_counter()
            shadow_latency_ms = round((t_end - t_start) * 1000.0, 3)

            cand_prob = round(float(probs[0]), 4)
            row = input_df.iloc[0]

            log_entry = {
                "request_id": request_id or f"req_{uuid.uuid4().hex[:12]}",
                "cycle_id": cycle_id or "OPERATIONAL_API_REQUEST",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "latitude": float(row.get("latitude", 0.0)),
                "longitude": float(row.get("longitude", 0.0)),
                "lead_hours": int(row.get("lead_hours", 24)),
                "initialization_time": str(row.get("initialization_time", "")),
                "production_model": "model_real_v002",
                "production_probability": round(float(prod_probability), 4),
                "production_latency_ms": round(float(prod_latency_ms), 3),
                "shadow_model": self.candidate_version,
                "shadow_probability": cand_prob,
                "shadow_latency_ms": shadow_latency_ms,
                "total_added_latency_ms": shadow_latency_ms,
                "delta_probability": round(cand_prob - float(prod_probability), 4),
                "abs_delta_probability": round(abs(cand_prob - float(prod_probability)), 4)
            }

            if metadata:
                for k, v in metadata.items():
                    if k not in log_entry:
                        log_entry[k] = v

            # Append to versioned shadow log
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")

            return log_entry
        except Exception as e:
            # Safe degradation: log failure to console, never propagate error to caller
            print(f"[!] Shadow inference error (safely ignored): {e}")
            return None
