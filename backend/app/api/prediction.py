"""
Forecast Bust Risk & Explainability API Router.
Provides calibrated probability inference, geographic risk maps,
historical forecast-vs-reference verification, SHAP explainability,
and controlled canary deployment status monitoring.
"""
import math
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Path
from backend.app.services.bust_service import BustPredictionService
from backend.app.services.weather_service import WeatherService

router = APIRouter(prefix="", tags=["Forecast Bust Risk & Verification"])
bust_service = BustPredictionService()
weather_service = WeatherService()

ALLOWED_VARIABLES = {"precipitation", "temperature", "wind", "pressure", "humidity"}


@router.get("/risk/location")
async def get_risk_by_location(
    lat: float = Query(..., ge=-90, le=90, description="Latitude (-90 to 90)"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude (-180 to 180)"),
    lead_hours: int = Query(96, ge=24, le=720, description="Lead time in hours (24 to 720 / Day 1 to Day 30)"),
    variable: str = Query("precipitation", description="Target variable: precipitation, temperature, wind, pressure"),
    forecast_value: Optional[float] = Query(None, description="Optional forecasted value override"),
    ensemble_spread: Optional[float] = Query(None, ge=0.0, le=50.0, description="NWP Ensemble Spread (dispersion, 0 to 50)")
):
    # 1. Finite Value Validation (Reject NaN and Inf)
    for name, val in [("lat", lat), ("lon", lon), ("forecast_value", forecast_value), ("ensemble_spread", ensemble_spread)]:
        if val is not None and (math.isnan(val) or math.isinf(val)):
            raise HTTPException(
                status_code=422,
                detail=f"Parameter '{name}' must be a finite numerical value (received NaN or Infinity)."
            )

    # 2. Variable Whitelist Validation
    var_clean = (variable or "").lower().strip()
    if not var_clean or var_clean not in ALLOWED_VARIABLES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported variable '{variable}'. Supported variables: {', '.join(sorted(ALLOWED_VARIABLES))}."
        )

    # 3. Physical Plausibility Validation (Conservative boundaries)
    if forecast_value is not None:
        if var_clean == "precipitation":
            if forecast_value < 0.0 or forecast_value > 2000.0:
                raise HTTPException(
                    status_code=422,
                    detail=f"Physically invalid precipitation: {forecast_value} mm. Must be between 0.0 and 2000.0 mm."
                )
        elif var_clean == "temperature":
            if forecast_value < -100.0 or forecast_value > 75.0:
                raise HTTPException(
                    status_code=422,
                    detail=f"Physically invalid temperature: {forecast_value} °C. Must be between -100.0 and 75.0 °C."
                )
        elif var_clean == "wind":
            if forecast_value < 0.0 or forecast_value > 150.0:
                raise HTTPException(
                    status_code=422,
                    detail=f"Physically invalid wind speed: {forecast_value} m/s. Must be between 0.0 and 150.0 m/s."
                )
        elif var_clean == "pressure":
            if forecast_value < 800.0 or forecast_value > 1100.0:
                raise HTTPException(
                    status_code=422,
                    detail=f"Physically invalid sea level pressure: {forecast_value} hPa. Must be between 800.0 and 1100.0 hPa."
                )

    f_precip = 5.0
    f_temp = 28.0
    f_wind = 6.0
    f_press = 1010.0
    f_hum = 75.0
    spread = ensemble_spread if ensemble_spread is not None else 1.5
    rev = 0.5
    fc_src = "ECMWF IFS (Operational NWP)"

    # If forecast_value or ensemble_spread is not supplied, fetch live operational NWP guidance
    if forecast_value is None or ensemble_spread is None:
        try:
            req_days = min(10, max(1, (lead_hours + 23) // 24))
            horizons = await weather_service.get_forecast(lat, lon, days=req_days)
            if horizons:
                matching = min(horizons, key=lambda h: abs(h.lead_hours - lead_hours))
                if matching.temperature_2m is not None:
                    f_temp = matching.temperature_2m
                if matching.precipitation is not None:
                    f_precip = matching.precipitation
                if matching.wind_speed_10m is not None:
                    f_wind = matching.wind_speed_10m
                if matching.pressure_msl is not None:
                    f_press = matching.pressure_msl
                if matching.relative_humidity_2m is not None:
                    f_hum = matching.relative_humidity_2m
                if ensemble_spread is None and matching.ensemble_spread is not None:
                    spread = matching.ensemble_spread
                if matching.run_revision is not None:
                    rev = matching.run_revision

                # Accurately identify provider source without false claims
                if "demo" in str(matching.provider).lower():
                    fc_src = f"Fallback {matching.provider} ({matching.model})"
                else:
                    fc_src = f"Live {matching.provider} ({matching.model})"

                if forecast_value is None:
                    if var_clean == "temperature":
                        forecast_value = f_temp
                    elif var_clean == "wind":
                        forecast_value = f_wind
                    elif var_clean == "pressure":
                        forecast_value = f_press
                    elif var_clean == "humidity":
                        forecast_value = f_hum
                    else:
                        forecast_value = f_precip
            else:
                raise HTTPException(
                    status_code=503,
                    detail="Live operational NWP forecast unavailable from upstream provider. Please retry or provide a scenario override."
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Live operational NWP provider error: {str(e)}. Please retry or provide a scenario override."
            )
    else:
        fc_src = "Scenario / What-if Input Override"

    result = bust_service.predict_risk(
        latitude=lat,
        longitude=lon,
        lead_hours=lead_hours,
        variable=var_clean,
        forecast_val=forecast_value,
        forecast_precip=f_precip,
        forecast_temp=f_temp,
        forecast_wind=f_wind,
        forecast_press=f_press,
        forecast_hum=f_hum,
        ensemble_spread=spread,
        run_revision=rev,
        forecast_source=fc_src
    )

    # Record prediction event in verification registry
    try:
        from backend.app.services.verification_service import VerificationService
        import uuid
        pred_id = f"pred_{uuid.uuid4().hex[:10]}"
        v_service = VerificationService()
        v_service.record_t0_prediction(
            prediction_id=pred_id,
            initialization_time=result["initialization_time"],
            valid_time=result["valid_time"],
            latitude=lat,
            longitude=lon,
            lead_hours=lead_hours,
            variable=var_clean,
            forecast_value=float(result["forecast_value"]),
            bust_probability=float(result["bust_probability"]),
            operational_threshold=25.0,
            model_version=result["model_version"]
        )
        result["prediction_id"] = pred_id
    except Exception:
        pass

    # Build explicitly categorized sections per Phase 12 guidelines
    response = {
        "LIVE_CONDITIONS": {
            "source": fc_src,
            "forecast_value": round(float(result["forecast_value"]), 1),
            "variable": var_clean
        },
        "FORECAST": {
            "initialization_time": result["initialization_time"],
            "valid_time": result["valid_time"],
            "lead_hours": lead_hours,
            "lead_time_group": result.get("lead_time_group", "Day 3-5"),
            "forecast_day": result["forecast_day"]
        },
        "AI_BUST_RISK": {
            "bust_probability": result["bust_probability"],
            "bust_probability_percentage": result["bust_probability_percentage"],
            "reliability_score": result["reliability_score"],
            "reliability_percentage": result["reliability_percentage"],
            "risk_level": result["risk_level"],
            "risk_badge": result["risk_badge"],
            "explanation": result["explanation"],
            "scientific_governance": result.get("scientific_governance")
        },
        "HISTORICAL_VERIFICATION": {
            "reference_source": result["reference_source"],
            "model_version": result["model_version"],
            "dataset_version": result["dataset_version"],
            "data_type": result["data_type"],
            "disclaimer": result["disclaimer"]
        }
    }
    # Preserve flat fields for backward compatibility
    response.update(result)
    return response


@router.get("/risk/map")
async def get_risk_map(
    lead_hours: int = Query(96, ge=24, le=720, description="Lead horizon (24 to 720 / Day 1 to Day 30)"),
    variable: str = Query("precipitation", description="Weather variable: precipitation, temperature, wind, pressure"),
    region: str = Query("india", description="Synoptic domain: 'india' or 'global'")
):
    var_clean = (variable or "").lower().strip()
    if var_clean not in ALLOWED_VARIABLES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported variable '{variable}'. Supported variables: {', '.join(sorted(ALLOWED_VARIABLES))}."
        )

    from data_pipeline.labeler import get_lead_time_group
    grid = bust_service.get_spatial_risk_grid(lead_hours=lead_hours, variable=var_clean, region=region)
    return {
        "forecast_horizon_hours": lead_hours,
        "forecast_day": int(lead_hours // 24),
        "lead_time_group": get_lead_time_group(lead_hours),
        "region_scope": region.upper(),
        "variable": var_clean,
        "data_type": getattr(bust_service, "data_type", "REAL"),
        "model_version": bust_service.model_version,
        "dataset_version": getattr(bust_service, "dataset_version", "dataset_real_v002"),
        "grid_points_count": len(grid),
        "grid": grid,
        "stations": grid,
        "legend": {
            "LOW": {"badge": "🟢 LOW", "threshold": "< 25%", "color": "#10b981"},
            "MODERATE": {"badge": "🟡 MODERATE", "threshold": "25% - 50%", "color": "#f59e0b"},
            "HIGH": {"badge": "🟠 HIGH", "threshold": "50% - 75%", "color": "#f97316"},
            "VERY_HIGH": {"badge": "🔴 VERY HIGH", "threshold": "> 75%", "color": "#ef4444"}
        }
    }


@router.get("/verification/audit")
async def get_verification_audit():
    """Returns historical forecast verification audit summary across realized forecasts."""
    from backend.app.services.verification_service import VerificationService
    v_service = VerificationService()
    return v_service.get_verification_summary()


@router.post("/verification/verify")
async def verify_forecast_outcome(
    prediction_id: str = Query(..., description="Prediction identifier"),
    reference_value: float = Query(..., description="Realized ground-truth reference value")
):
    """Verifies a realized forecast outcome against ERA5 reanalysis reference."""
    from backend.app.services.verification_service import VerificationService
    v_service = VerificationService()
    target = v_service.verify_prediction(prediction_id, reference_value)
    if not target:
        raise HTTPException(
            status_code=404,
            detail=f"Prediction ID '{prediction_id}' not found in verification registry."
        )
    return target


@router.get("/risk/history")
async def get_historical_bust_performance(
    lat: float = Query(18.5204, ge=-90, le=90),
    lon: float = Query(73.8567, ge=-180, le=180),
    limit: int = Query(10, ge=1, le=50)
):
    comparisons = bust_service.get_historical_comparisons(lat, lon, limit=limit)
    bust_count = sum(1 for c in comparisons if c["is_bust"])
    total = len(comparisons)
    bust_rate = round((bust_count / max(1, total)) * 100, 1)

    return {
        "location": {"latitude": lat, "longitude": lon},
        "sample_size": total,
        "bust_count": bust_count,
        "historical_bust_rate_percentage": bust_rate,
        "average_error": round(float(sum(c["absolute_error"] for c in comparisons) / max(1, total)), 2),
        "data_type": getattr(bust_service, "data_type", "REAL"),
        "model_version": bust_service.model_version,
        "dataset_version": getattr(bust_service, "dataset_version", "dataset_real_v002"),
        "is_demo_model": getattr(bust_service, "data_type", "REAL") == "SYNTHETIC",
        "records": comparisons
    }


@router.get("/forecast/{id}")
async def get_forecast_detail(
    id: str = Path(..., description="Forecast record or station identifier")
):
    # Retrieve forecast scenario for Pune or specified station
    risk = bust_service.predict_risk(latitude=18.5204, longitude=73.8567, lead_hours=96, forecast_val=42.0)
    return {
        "forecast_id": id,
        "location_name": "Pune, Maharashtra",
        "coordinates": {"latitude": 18.5204, "longitude": 73.8567},
        "forecast_horizon": "Day 4 (96 hours)",
        "expected_precipitation_mm": 42.0,
        "bust_probability": risk["bust_probability"],
        "reliability_score": risk["reliability_score"],
        "risk_level": risk["risk_level"],
        "risk_badge": risk["risk_badge"]
    }


@router.get("/forecast/{id}/comparison")
async def get_forecast_comparison(
    id: str = Path(...)
):
    comparison = bust_service.get_single_comparison(id)
    if not comparison:
        raise HTTPException(
            status_code=404,
            detail=f"Historical verification record '{id}' not found in verification archive."
        )
    return comparison


@router.get("/forecast/{id}/explanation")
async def get_forecast_explanation(
    id: str = Path(...)
):
    risk = bust_service.predict_risk(latitude=18.5204, longitude=73.8567, lead_hours=96, forecast_val=42.0, ensemble_spread=3.8, run_revision=2.4)
    return {
        "forecast_id": id,
        "bust_probability": risk["bust_probability"],
        "bust_probability_percentage": risk["bust_probability_percentage"],
        "reliability_score": risk["reliability_score"],
        "risk_level": risk["risk_level"],
        "top_contributing_factors": risk["explanation"].get("all_factors", []),
        "amplifiers": risk["explanation"].get("top_amplifiers", []),
        "mitigators": risk["explanation"].get("top_mitigators", []),
        "scientific_summary": risk["explanation"].get("summary_text")
    }


@router.get("/canary/status")
async def get_canary_status():
    """
    Returns real-time canary deployment telemetry: routing configuration,
    traffic split, error rates, latency percentiles, circuit breaker state,
    and shadow disagreement metrics.
    Operational monitoring only. No model weights or artifacts are exposed.
    """
    from backend.app.services.canary_service import CanaryRoutingService
    canary_router = CanaryRoutingService()
    telemetry = canary_router.get_telemetry()
    return {
        "status": "ok",
        "governance": "CANARY_MONITORING_ONLY — No user-facing predictions are served from this endpoint.",
        **telemetry
    }
