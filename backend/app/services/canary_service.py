"""
Controlled Canary Deployment & Routing Service.
SIH26079 – AI-Based Forecast Bust Detection for Medium-Range Weather Forecasts.

Routes operational forecast traffic between:
- Production: model_real_v002 (90% by default when enabled, 100% when disabled)
- Canary: global_v001 (10% by default when enabled)

Key Safety & Architecture Constraints:
1. Production model remains model_real_v002; registry.json is never overwritten.
2. Deterministic SHA-256 hash routing ensures the same request context consistently routes to the same model.
3. Disabled by default (CANARY_ENABLED=False).
4. Both models loaded in total isolation via distinct prediction bundles.
5. Strict output validation: probabilities must be finite and within [0.0, 1.0].
6. Automatic rollback / circuit breaker on error rate > 1%, repeated exceptions, or sustained > 2x latency degradation.
7. Safe, immediate fallback to model_real_v002 on any canary failure.
8. Non-sensitive operational audit logging (zero credentials, tokens, or PII).
9. Real-time shadow comparison for candidate requests (|ΔP| metrics).
"""
import os
import time
import json
import uuid
import math
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from collections import deque
import numpy as np

# Shared background executor for non-blocking shadow comparisons and audit logging.
# Max 4 workers is intentional: shadow calls are I/O-bound (model inference) and
# we want to bound memory usage; canary traffic is capped at 10% anyway.
_SHADOW_EXECUTOR: ThreadPoolExecutor = ThreadPoolExecutor(
    max_workers=4, thread_name_prefix="canary_shadow"
)


def flush_shadow_executor(timeout: float = 5.0) -> None:
    """Block until all pending shadow comparison tasks have completed.

    FOR TESTING USE ONLY.  Never call this on the hot path.
    Allows unit tests that immediately inspect shadow_deltas after predict_risk
    to synchronize with the background thread pool.
    """
    global _SHADOW_EXECUTOR
    _SHADOW_EXECUTOR.shutdown(wait=True, cancel_futures=False)
    # Re-initialize the executor so subsequent calls still work
    import concurrent.futures as _cf
    _SHADOW_EXECUTOR = _cf.ThreadPoolExecutor(
        max_workers=4, thread_name_prefix="canary_shadow"
    )

from backend.app.config import settings


class CanaryHealthMonitor:
    """
    Tracks real-time operational health, error rates, latency distributions,
    and governs the automatic circuit-breaker rollback.
    """
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.canary_requests: int = 0
        self.canary_errors: int = 0
        self.canary_fallbacks: int = 0
        self.canary_consecutive_exceptions: int = 0
        self.prod_requests: int = 0
        self.prod_errors: int = 0

        self.canary_latencies: deque = deque(maxlen=max_history)
        self.prod_latencies: deque = deque(maxlen=max_history)
        self.shadow_deltas: deque = deque(maxlen=max_history)

        self.consecutive_latency_breach_count: int = 0
        self.circuit_broken: bool = False
        self.circuit_break_reason: Optional[str] = None
        self.circuit_break_timestamp: Optional[str] = None

    def record_canary_success(self, latency_ms: float, abs_delta_p: Optional[float] = None):
        self.canary_requests += 1
        self.canary_consecutive_exceptions = 0
        self.canary_latencies.append(latency_ms)
        if abs_delta_p is not None:
            self.shadow_deltas.append(abs_delta_p)
        self._evaluate_latency_health()

    def record_canary_error(self, error_type: str, detail: str) -> bool:
        """Records a canary error and returns True if circuit breaker tripped."""
        self.canary_requests += 1
        self.canary_errors += 1
        self.canary_fallbacks += 1
        self.canary_consecutive_exceptions += 1

        # Check Trigger 1: Error rate > 1% (evaluated after at least 10 canary calls)
        if self.canary_requests >= 10:
            error_rate = self.canary_errors / self.canary_requests
            if error_rate > settings.CANARY_MAX_ERROR_RATE:
                return self.trip(f"Canary error rate exceeded 1.0% threshold: {error_rate*100:.2f}% ({self.canary_errors}/{self.canary_requests})")

        # Check Trigger 2: Repeated unhandled exceptions (>= 3 consecutive)
        if self.canary_consecutive_exceptions >= 3:
            return self.trip(f"Canary triggered {self.canary_consecutive_exceptions} consecutive exceptions: {detail}")

        # Check Trigger 3/4: Critical output corruption
        if "NaN" in error_type or "Inf" in error_type or "out_of_bounds" in error_type or "schema" in error_type:
            return self.trip(f"Canary produced invalid output: {error_type} - {detail}")

        return False

    def record_prod_request(self, latency_ms: float, is_error: bool = False):
        self.prod_requests += 1
        if is_error:
            self.prod_errors += 1
        self.prod_latencies.append(latency_ms)

    def _evaluate_latency_health(self):
        """Checks for sustained severe latency degradation: p95 > 2x prod for 3 consecutive windows."""
        if len(self.canary_latencies) < 20 or len(self.prod_latencies) < 20:
            return

        canary_p95 = float(np.percentile(list(self.canary_latencies)[-50:], 95))
        prod_p95 = float(np.percentile(list(self.prod_latencies)[-50:], 95))

        if prod_p95 > 0 and canary_p95 > (settings.CANARY_MAX_P95_LATENCY_MULTIPLIER * prod_p95):
            self.consecutive_latency_breach_count += 1
            if self.consecutive_latency_breach_count >= settings.CANARY_LATENCY_BREACH_WINDOW:
                self.trip(
                    f"Sustained severe latency degradation: Canary p95 ({canary_p95:.2f}ms) > "
                    f"{settings.CANARY_MAX_P95_LATENCY_MULTIPLIER}x Prod p95 ({prod_p95:.2f}ms) "
                    f"for {self.consecutive_latency_breach_count} consecutive windows."
                )
        else:
            self.consecutive_latency_breach_count = 0

    def trip(self, reason: str) -> bool:
        self.circuit_broken = True
        self.circuit_break_reason = reason
        self.circuit_break_timestamp = datetime.now(timezone.utc).isoformat()
        print(f"[!] CANARY CIRCUIT BREAKER TRIPPED: {reason}")
        return True

    def reset(self):
        self.circuit_broken = False
        self.circuit_break_reason = None
        self.circuit_break_timestamp = None
        self.canary_consecutive_exceptions = 0
        self.consecutive_latency_breach_count = 0


class CanaryRoutingService:
    """
    Manages dual-model isolation, deterministic request routing,
    canary safety execution, shadow delta computation, and automatic rollback.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(CanaryRoutingService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.production_model_name = getattr(settings, "PRODUCTION_MODEL", "model_real_v002")
        self.canary_model_name = getattr(settings, "CANARY_MODEL", "global_v001")
        self.canary_enabled = getattr(settings, "CANARY_ENABLED", False)
        self.canary_percentage = getattr(settings, "CANARY_PERCENTAGE", 10.0)

        self.prod_service = None
        self.canary_service = None
        self.health_monitor = CanaryHealthMonitor()
        self.audit_log_path = os.path.join("data", "canary", "canary_audit.jsonl")
        os.makedirs(os.path.dirname(self.audit_log_path), exist_ok=True)

        self._load_models()
        self._initialized = True

    def _load_models(self):
        from backend.app.services.bust_service import BustPredictionService

        # 1. Load active production model
        prod_bundle = os.path.join("models", self.production_model_name, "model_bundle.joblib")
        if os.path.exists(prod_bundle):
            self.prod_service = BustPredictionService(bundle_path=prod_bundle)
            print(f"[+] CanaryRoutingService: Production model loaded: {self.production_model_name}")
        else:
            print(f"[!] Warning: Production bundle not found at {prod_bundle}, using default loading.")
            self.prod_service = BustPredictionService()

        # 2. Load candidate canary model independently
        canary_bundle = os.path.join("models", self.canary_model_name, "model_bundle.joblib")
        if os.path.exists(canary_bundle):
            try:
                self.canary_service = BustPredictionService(bundle_path=canary_bundle)
                print(f"[+] CanaryRoutingService: Canary model loaded: {self.canary_model_name}")
            except Exception as e:
                print(f"[!] Warning: Could not load canary bundle {self.canary_model_name}: {e}")
                self.canary_service = None
        else:
            print(f"[-] CanaryRoutingService: Canary bundle not found at {canary_bundle}.")
            self.canary_service = None

    def route_request(
        self,
        latitude: float,
        longitude: float,
        lead_hours: int,
        variable: str,
        request_id: Optional[str] = None
    ) -> str:
        """
        Determines target model ('canary' or 'production') using deterministic SHA-256 hash.
        Guarantees that identical input context consistently maps to the same model.
        """
        if not self.canary_enabled:
            return "production"

        if self.health_monitor.circuit_broken:
            return "production"

        if self.canary_service is None:
            return "production"

        # Construct deterministic hash key
        lat_norm = round(float(latitude), 3)
        lon_norm = round(float(longitude), 3)
        var_norm = str(variable or "precipitation").lower().strip()
        key = f"canary:{lat_norm}:{lon_norm}:{int(lead_hours)}:{var_norm}"
        if request_id:
            key = f"{key}:{request_id}"

        # Map SHA-256 hash to bucket [0.0, 99.9]
        hash_digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        bucket = (int(hash_digest[:8], 16) % 1000) / 10.0

        if bucket < self.canary_percentage:
            return "canary"
        return "production"

    def validate_canary_output(self, result: Any) -> Optional[str]:
        """Validates canary output schema, probability boundaries, and finite values."""
        if not isinstance(result, dict):
            return "Output is not a dictionary"

        required_keys = [
            "bust_probability", "reliability_score", "risk_level",
            "model_version", "location", "forecast_horizon_hours"
        ]
        for k in required_keys:
            if k not in result:
                return f"Missing required response key: '{k}'"

        prob = result.get("bust_probability")
        if prob is None or not isinstance(prob, (int, float)):
            return f"Invalid probability type: {type(prob)}"

        if math.isnan(prob) or math.isinf(prob):
            return f"Non-finite probability received: {prob}"

        if prob < 0.0 or prob > 1.0:
            return f"Probability outside valid [0.0, 1.0] interval: {prob}"

        reliability = result.get("reliability_score")
        if reliability is not None:
            if math.isnan(reliability) or math.isinf(reliability) or reliability < 0.0 or reliability > 1.0:
                return f"Invalid reliability score: {reliability}"

        return None

    def predict_risk(
        self,
        latitude: float,
        longitude: float,
        lead_hours: int,
        variable: str = "precipitation",
        forecast_val: Optional[float] = None,
        forecast_precip: float = 5.0,
        forecast_temp: float = 28.0,
        forecast_wind: float = 6.0,
        forecast_press: float = 1010.0,
        forecast_hum: float = 75.0,
        ensemble_spread: float = 1.2,
        run_revision: float = 0.5,
        include_explanation: bool = True,
        forecast_source: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for risk prediction. Handles routing, execution,
        output verification, automatic rollback circuit breaker, shadow comparison,
        and sanitized non-sensitive audit logging.
        """
        route = self.route_request(
            latitude=latitude,
            longitude=longitude,
            lead_hours=lead_hours,
            variable=variable,
            request_id=request_id
        )

        # -------------------------------------------------------------
        # Path A: Canary Execution (Candidate: global_v001)
        # -------------------------------------------------------------
        if route == "canary" and self.canary_service is not None:
            t0 = time.perf_counter()
            canary_error_occurred = False
            canary_result = None

            try:
                canary_result = self.canary_service.predict_risk(
                    latitude=latitude,
                    longitude=longitude,
                    lead_hours=lead_hours,
                    variable=variable,
                    forecast_val=forecast_val,
                    forecast_precip=forecast_precip,
                    forecast_temp=forecast_temp,
                    forecast_wind=forecast_wind,
                    forecast_press=forecast_press,
                    forecast_hum=forecast_hum,
                    ensemble_spread=ensemble_spread,
                    run_revision=run_revision,
                    include_explanation=include_explanation,
                    forecast_source=forecast_source
                )
                t1 = time.perf_counter()
                canary_lat_ms = (t1 - t0) * 1000.0

                validation_err = self.validate_canary_output(canary_result)
                if validation_err:
                    canary_error_occurred = True
                    self.health_monitor.record_canary_error("invalid_output", validation_err)
                else:
                    # -------------------------------------------------------
                    # LATENCY OPTIMIZATION: record the success immediately and
                    # return the canary result to the caller WITHOUT waiting
                    # for the shadow comparison to complete.
                    #
                    # The shadow prod inference and audit log are dispatched to
                    # a background thread pool so they never block the hot path.
                    # -------------------------------------------------------
                    self.health_monitor.record_canary_success(canary_lat_ms, abs_delta_p=None)

                    # Snapshot all values needed by the background task before
                    # we release the reference (avoids closure mutation hazards).
                    _snap_request_id = request_id or f"canary_{uuid.uuid4().hex[:10]}"
                    _snap_canary_prob = float(canary_result["bust_probability"])
                    _snap_lat_ms = round(canary_lat_ms, 3)
                    _snap_model_name = self.canary_model_name

                    def _background_shadow_and_audit(
                        prod_svc,
                        health_mon,
                        log_fn,
                        req_id,
                        cand_prob,
                        lat_ms,
                        model_name,
                        lat, lon, lhrs, var,
                        fval, fprec, ftemp, fwind, fpress, fhum,
                        ens_spread, run_rev, fsrc
                    ):
                        """Non-blocking shadow comparison + audit write executed off the hot path."""
                        abs_delta_p = None
                        delta_p = None
                        prod_prob = None
                        try:
                            shadow_prod = prod_svc.predict_risk(
                                latitude=lat,
                                longitude=lon,
                                lead_hours=lhrs,
                                variable=var,
                                forecast_val=fval,
                                forecast_precip=fprec,
                                forecast_temp=ftemp,
                                forecast_wind=fwind,
                                forecast_press=fpress,
                                forecast_hum=fhum,
                                ensemble_spread=ens_spread,
                                run_revision=run_rev,
                                include_explanation=False,
                                forecast_source=fsrc
                            )
                            prod_prob = float(shadow_prod.get("bust_probability", 0.0))
                            delta_p = round(cand_prob - prod_prob, 4)
                            abs_delta_p = round(abs(cand_prob - prod_prob), 4)
                            # Backfill the shadow delta into the health monitor
                            if abs_delta_p is not None:
                                health_mon.shadow_deltas.append(abs_delta_p)
                        except Exception as e:
                            print(f"[-] Shadow comparison (background) non-fatal error: {e}")

                        try:
                            log_fn(
                                request_id=req_id,
                                model_version=model_name,
                                latitude=lat,
                                longitude=lon,
                                lead_hours=lhrs,
                                variable=var,
                                bust_probability=cand_prob,
                                latency_ms=lat_ms,
                                success=True,
                                prod_probability=prod_prob,
                                delta_p=delta_p,
                                abs_delta_p=abs_delta_p
                            )
                        except Exception as e:
                            print(f"[-] Audit log (background) non-fatal error: {e}")

                    _SHADOW_EXECUTOR.submit(
                        _background_shadow_and_audit,
                        self.prod_service,
                        self.health_monitor,
                        self._log_audit_record,
                        _snap_request_id,
                        _snap_canary_prob,
                        _snap_lat_ms,
                        _snap_model_name,
                        latitude, longitude, lead_hours, variable,
                        forecast_val, forecast_precip, forecast_temp,
                        forecast_wind, forecast_press, forecast_hum,
                        ensemble_spread, run_revision, forecast_source
                    )

                    return canary_result

            except Exception as e:
                canary_error_occurred = True
                self.health_monitor.record_canary_error("exception", str(e))
                print(f"[!] Canary inference exception: {e}. Executing immediate fail-safe fallback.")

            # If canary execution or validation failed -> Fall back to production model
            if canary_error_occurred or canary_result is None:
                print("[-] Routing fail-safe fallback to production model_real_v002.")

        # -------------------------------------------------------------
        # Path B: Production Execution (model_real_v002)
        # -------------------------------------------------------------
        t_prod_0 = time.perf_counter()
        try:
            prod_result = self.prod_service.predict_risk(
                latitude=latitude,
                longitude=longitude,
                lead_hours=lead_hours,
                variable=variable,
                forecast_val=forecast_val,
                forecast_precip=forecast_precip,
                forecast_temp=forecast_temp,
                forecast_wind=forecast_wind,
                forecast_press=forecast_press,
                forecast_hum=forecast_hum,
                ensemble_spread=ensemble_spread,
                run_revision=run_revision,
                include_explanation=include_explanation,
                forecast_source=forecast_source
            )
            t_prod_1 = time.perf_counter()
            prod_lat_ms = (t_prod_1 - t_prod_0) * 1000.0
            self.health_monitor.record_prod_request(prod_lat_ms, is_error=False)
            return prod_result
        except Exception as e:
            t_prod_1 = time.perf_counter()
            prod_lat_ms = (t_prod_1 - t_prod_0) * 1000.0
            self.health_monitor.record_prod_request(prod_lat_ms, is_error=True)
            raise e

    def _log_audit_record(
        self,
        request_id: str,
        model_version: str,
        latitude: float,
        longitude: float,
        lead_hours: int,
        variable: str,
        bust_probability: float,
        latency_ms: float,
        success: bool,
        prod_probability: Optional[float] = None,
        delta_p: Optional[float] = None,
        abs_delta_p: Optional[float] = None
    ):
        """Appends sanitized operational metadata to canary audit log (zero secrets, zero PII)."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id,
            "model_version": model_version,
            "lead_hours": lead_hours,
            "variable": variable,
            "latitude": round(float(latitude), 4),
            "longitude": round(float(longitude), 4),
            "predicted_bust_probability": bust_probability,
            "latency_ms": latency_ms,
            "success": success,
            "production_probability": prod_probability,
            "delta_probability": delta_p,
            "abs_delta_probability": abs_delta_p
        }
        try:
            with open(self.audit_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"[!] Warning: Failed to write canary audit record: {e}")

    # Administrative Controls & Observability
    def enable_canary(self, percentage: float = 10.0):
        self.canary_percentage = min(100.0, max(0.0, percentage))
        self.canary_enabled = True
        self.health_monitor.reset()
        print(f"[+] Canary enabled at {self.canary_percentage}% traffic.")

    def disable_canary(self, reason: str = "Manual operator disable"):
        self.canary_enabled = False
        print(f"[-] Canary disabled: {reason}")

    def trip_circuit_breaker(self, reason: str):
        self.health_monitor.trip(reason)

    def reset_circuit_breaker(self):
        self.health_monitor.reset()

    def get_telemetry(self) -> Dict[str, Any]:
        """Calculates comprehensive real-time operational telemetry and shadow comparison metrics."""
        hm = self.health_monitor
        c_lats = list(hm.canary_latencies)
        p_lats = list(hm.prod_latencies)
        deltas = list(hm.shadow_deltas)

        total_reqs = hm.canary_requests + hm.prod_requests
        canary_pct = round((hm.canary_requests / max(1, total_reqs)) * 100.0, 2)
        canary_err_rate = round((hm.canary_errors / max(1, hm.canary_requests)), 4)
        canary_succ_rate = round(1.0 - canary_err_rate, 4)

        # Disagreement statistics
        if deltas:
            mean_abs_diff = round(float(np.mean(deltas)), 4)
            p50_diff = round(float(np.percentile(deltas, 50)), 4)
            p95_diff = round(float(np.percentile(deltas, 95)), 4)
            p99_diff = round(float(np.percentile(deltas, 99)), 4)
            pct_ge_5pp = round(float(np.mean([d >= 0.05 for d in deltas]) * 100.0), 2)
            pct_ge_10pp = round(float(np.mean([d >= 0.10 for d in deltas]) * 100.0), 2)
            pct_ge_20pp = round(float(np.mean([d >= 0.20 for d in deltas]) * 100.0), 2)
        else:
            mean_abs_diff = 0.0
            p50_diff = 0.0
            p95_diff = 0.0
            p99_diff = 0.0
            pct_ge_5pp = 0.0
            pct_ge_10pp = 0.0
            pct_ge_20pp = 0.0

        return {
            "routing_configuration": {
                "canary_enabled": self.canary_enabled,
                "canary_percentage": self.canary_percentage,
                "production_model": self.production_model_name,
                "canary_model": self.canary_model_name,
                "circuit_broken": hm.circuit_broken,
                "circuit_break_reason": hm.circuit_break_reason,
                "circuit_break_timestamp": hm.circuit_break_timestamp
            },
            "traffic_statistics": {
                "total_requests": total_reqs,
                "production_requests": hm.prod_requests,
                "canary_requests": hm.canary_requests,
                "canary_fallbacks": hm.canary_fallbacks,
                "canary_traffic_percentage": canary_pct
            },
            "health_and_reliability": {
                "canary_success_rate": canary_succ_rate,
                "canary_error_rate": canary_err_rate,
                "canary_consecutive_exceptions": hm.canary_consecutive_exceptions,
                "production_errors": hm.prod_errors
            },
            "latency_benchmarks": {
                "production": {
                    "count": len(p_lats),
                    "mean_ms": round(float(np.mean(p_lats)), 2) if p_lats else 0.0,
                    "p50_ms": round(float(np.percentile(p_lats, 50)), 2) if p_lats else 0.0,
                    "p95_ms": round(float(np.percentile(p_lats, 95)), 2) if p_lats else 0.0,
                    "p99_ms": round(float(np.percentile(p_lats, 99)), 2) if p_lats else 0.0
                },
                "canary": {
                    "count": len(c_lats),
                    "mean_ms": round(float(np.mean(c_lats)), 2) if c_lats else 0.0,
                    "p50_ms": round(float(np.percentile(c_lats, 50)), 2) if c_lats else 0.0,
                    "p95_ms": round(float(np.percentile(c_lats, 95)), 2) if c_lats else 0.0,
                    "p99_ms": round(float(np.percentile(c_lats, 99)), 2) if c_lats else 0.0
                }
            },
            "shadow_disagreement_analysis": {
                "sample_size": len(deltas),
                "mean_absolute_difference": mean_abs_diff,
                "p50_difference": p50_diff,
                "p95_difference": p95_diff,
                "p99_difference": p99_diff,
                "pct_ge_5pp": pct_ge_5pp,
                "pct_ge_10pp": pct_ge_10pp,
                "pct_ge_20pp": pct_ge_20pp
            }
        }
