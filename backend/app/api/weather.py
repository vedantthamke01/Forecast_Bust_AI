"""
Weather and Geocoding API Router.
Provides location search, reverse geocoding, current weather, and multi-day NWP forecasts.
"""
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from backend.app.services.weather_service import WeatherService

router = APIRouter(prefix="", tags=["Weather & Locations"])
weather_service = WeatherService()


@router.get("/locations/search")
async def search_locations(q: str = Query(..., min_length=1, description="City, district, or observatory name")):
    results = await weather_service.search_locations(q)
    return {
        "query": q,
        "count": len(results),
        "results": [r.model_dump() for r in results]
    }


@router.get("/locations/reverse")
async def reverse_geocode(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180)
):
    loc = await weather_service.reverse_geocode(lat, lon)
    if not loc:
        raise HTTPException(status_code=404, detail="Location could not be geocoded.")
    return loc.model_dump()


@router.get("/weather/current")
async def get_current_weather(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    demo: bool = Query(False, description="Force demo mode benchmark")
):
    current = await weather_service.get_current_weather(lat, lon, demo_mode=demo)
    return {
        "location": {"latitude": lat, "longitude": lon},
        "observation_time": current.observation_time.isoformat(),
        "temperature_c": current.temperature_2m,
        "precipitation_mm": current.precipitation,
        "wind_speed_mps": current.wind_speed_10m,
        "pressure_hpa": current.pressure_msl,
        "humidity_percent": current.relative_humidity_2m,
        "cloud_cover_percent": current.cloud_cover,
        "provider": current.provider,
        "model": current.model
    }


@router.get("/weather/forecast")
async def get_medium_range_forecast(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    days: int = Query(10, ge=1, le=10, description="Forecast days (up to 10 days / 240 hours)"),
    demo: bool = Query(False)
):
    forecasts = await weather_service.get_forecast(lat, lon, days=days, demo_mode=demo)
    return {
        "location": {"latitude": lat, "longitude": lon},
        "forecast_days": days,
        "total_horizons": len(forecasts),
        "horizons": [f.model_dump(mode="json") for f in forecasts]
    }
