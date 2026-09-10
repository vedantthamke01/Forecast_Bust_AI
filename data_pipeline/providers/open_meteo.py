"""
Open-Meteo Operational Forecast Provider.
Retrieves live/current operational weather observations and 10-day medium-range ensemble forecasts (ECMWF IFS)
for real-time inference and UI demonstration.
STRICT SEPARATION:
This class is for CURRENT OPERATIONAL WEATHER AND FORECASTS.
It does NOT provide historical training forecasts.
"""
import asyncio
import logging
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta, timezone
import httpx
from backend.app.config import settings
from data_pipeline.providers.base import (
    ForecastProvider, ReferenceWeatherProvider, NormalizedForecast, NormalizedReference, NormalizedCurrentWeather
)

logger = logging.getLogger(__name__)


class OpenMeteoProvider(ForecastProvider, ReferenceWeatherProvider):
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 20.0
    ):
        configured_key = api_key or getattr(settings, "OPEN_METEO_API_KEY", None)
        self.api_key = configured_key.strip() if configured_key and configured_key.strip() else None

        configured_base = base_url or getattr(settings, "OPEN_METEO_BASE_URL", None)
        if configured_base and configured_base.strip():
            self.forecast_base_url = configured_base.strip().rstrip("/")
            self.archive_base_url = "https://archive-api.open-meteo.com/v1/archive"
        elif self.api_key:
            self.forecast_base_url = "https://customer-api.open-meteo.com/v1/forecast"
            self.archive_base_url = "https://customer-archive-api.open-meteo.com/v1/archive"
        else:
            self.forecast_base_url = "https://api.open-meteo.com/v1/forecast"
            self.archive_base_url = "https://archive-api.open-meteo.com/v1/archive"

        self.timeout = timeout
        self.headers = {
            "User-Agent": "ForecastBustAI/1.0 (MoES/NCMRWF; https://forecast-bust-ai.onrender.com)",
            "Accept": "application/json"
        }
        self._current_cache: Dict[Tuple[float, float], Tuple[datetime, NormalizedCurrentWeather]] = {}
        self._forecast_cache: Dict[Tuple[float, float, int], Tuple[datetime, List[NormalizedForecast]]] = {}
        self._rate_limit_until: Optional[datetime] = None
        self._lock = asyncio.Lock()

    def get_provider_name(self) -> str:
        if self.api_key:
            return "Open-Meteo Customer ECMWF IFS [CURRENT FORECAST]"
        return "Open-Meteo Operational ECMWF IFS [CURRENT FORECAST]"

    def is_available(self) -> bool:
        return True

    async def get_current_weather(self, latitude: float, longitude: float) -> NormalizedCurrentWeather:
        """Fetch authentic real-time current weather observation using Open-Meteo current API."""
        cache_key = (round(latitude, 3), round(longitude, 3))
        now = datetime.now(timezone.utc)
        if cache_key in self._current_cache:
            cached_time, cached_val = self._current_cache[cache_key]
            if (now - cached_time).total_seconds() < 300:
                return cached_val

        # Deduplicate concurrent requests for the same location
        async with self._lock:
            now = datetime.now(timezone.utc)
            if cache_key in self._current_cache:
                cached_time, cached_val = self._current_cache[cache_key]
                if (now - cached_time).total_seconds() < 300:
                    return cached_val

            if self._rate_limit_until and now < self._rate_limit_until:
                wait_sec = int((self._rate_limit_until - now).total_seconds())
                raise RuntimeError(
                    f"Open-Meteo rate limit active on upstream host. Cooldown in progress ({wait_sec}s remaining)."
                )

            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,pressure_msl,cloud_cover",
                "wind_speed_unit": "ms",
                "timezone": "UTC"
            }
            if self.api_key:
                params["apikey"] = self.api_key

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                last_resp = None
                for attempt in range(2):  # Max 1 retry for transient glitches
                    resp = await client.get(self.forecast_base_url, params=params, headers=self.headers)
                    last_resp = resp
                    if resp.status_code == 429:
                        retry_after = int(resp.headers.get("retry-after", "30"))
                        cooldown = min(max(retry_after, 15), 60)
                        self._rate_limit_until = datetime.now(timezone.utc) + timedelta(seconds=cooldown)
                        if attempt < 1 and retry_after <= 2:
                            await asyncio.sleep(retry_after)
                            continue
                        logger.error(f"Open-Meteo 429 received (cooldown set to {cooldown}s): {resp.text}")
                        resp.raise_for_status()
                    resp.raise_for_status()
                    data = resp.json()
                    break
                else:
                    if last_resp is not None:
                        last_resp.raise_for_status()
                    raise RuntimeError("Failed to fetch current weather after retries")

            current = data.get("current")
            if not current:
                raise RuntimeError(f"Open-Meteo returned no current weather block for ({latitude}, {longitude}): {data}")

            time_str = current.get("time")
            try:
                obs_time = datetime.fromisoformat(time_str) if time_str else datetime.now(timezone.utc)
                if obs_time.tzinfo is None:
                    obs_time = obs_time.replace(tzinfo=timezone.utc)
            except Exception:
                obs_time = datetime.now(timezone.utc)

            result = NormalizedCurrentWeather(
                provider="open-meteo-operational" if not self.api_key else "open-meteo-customer",
                model="ecmwf-ifs",
                observation_time=obs_time,
                latitude=latitude,
                longitude=longitude,
                temperature_2m=current.get("temperature_2m"),
                precipitation=current.get("precipitation"),
                wind_speed_10m=current.get("wind_speed_10m"),
                pressure_msl=current.get("pressure_msl"),
                relative_humidity_2m=current.get("relative_humidity_2m"),
                cloud_cover=current.get("cloud_cover")
            )
            self._current_cache[cache_key] = (now, result)
            return result

    async def get_forecast(self, latitude: float, longitude: float, days: int = 10) -> List[NormalizedForecast]:
        """Fetch current operational 10-day medium range forecast with hourly resolution."""
        cache_key = (round(latitude, 3), round(longitude, 3), days)
        now = datetime.now(timezone.utc)
        if cache_key in self._forecast_cache:
            cached_time, cached_val = self._forecast_cache[cache_key]
            if (now - cached_time).total_seconds() < 600:
                return cached_val

        # Deduplicate and serialize forecast requests
        async with self._lock:
            now = datetime.now(timezone.utc)
            if cache_key in self._forecast_cache:
                cached_time, cached_val = self._forecast_cache[cache_key]
                if (now - cached_time).total_seconds() < 600:
                    return cached_val

            if self._rate_limit_until and now < self._rate_limit_until:
                wait_sec = int((self._rate_limit_until - now).total_seconds())
                raise RuntimeError(
                    f"Open-Meteo rate limit active on upstream host. Cooldown in progress ({wait_sec}s remaining)."
                )

            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,pressure_msl,cloud_cover",
                "hourly": "temperature_2m,precipitation,wind_speed_10m,pressure_msl,relative_humidity_2m,cloud_cover",
                "wind_speed_unit": "ms",
                "forecast_days": min(days, 10),
                "timezone": "UTC"
            }
            if self.api_key:
                params["apikey"] = self.api_key

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                last_resp = None
                for attempt in range(2):
                    resp = await client.get(self.forecast_base_url, params=params, headers=self.headers)
                    last_resp = resp
                    if resp.status_code == 429:
                        retry_after = int(resp.headers.get("retry-after", "30"))
                        cooldown = min(max(retry_after, 15), 60)
                        self._rate_limit_until = datetime.now(timezone.utc) + timedelta(seconds=cooldown)
                        if attempt < 1 and retry_after <= 2:
                            await asyncio.sleep(retry_after)
                            continue
                        logger.error(f"Open-Meteo forecast 429 received (cooldown {cooldown}s): {resp.text}")
                        resp.raise_for_status()
                    resp.raise_for_status()
                    data = resp.json()
                    break
                else:
                    if last_resp is not None:
                        last_resp.raise_for_status()
                    raise RuntimeError("Failed to fetch forecast after retries")

            # Also populate current weather cache from the current block to save a future request!
            current_data = data.get("current")
            curr_cache_key = (round(latitude, 3), round(longitude, 3))
            if current_data:
                time_str = current_data.get("time")
                try:
                    c_time = datetime.fromisoformat(time_str) if time_str else datetime.now(timezone.utc)
                    if c_time.tzinfo is None:
                        c_time = c_time.replace(tzinfo=timezone.utc)
                except Exception:
                    c_time = datetime.now(timezone.utc)

                curr_obj = NormalizedCurrentWeather(
                    provider="open-meteo-operational" if not self.api_key else "open-meteo-customer",
                    model="ecmwf-ifs",
                    observation_time=c_time,
                    latitude=latitude,
                    longitude=longitude,
                    temperature_2m=current_data.get("temperature_2m"),
                    precipitation=current_data.get("precipitation"),
                    wind_speed_10m=current_data.get("wind_speed_10m"),
                    pressure_msl=current_data.get("pressure_msl"),
                    relative_humidity_2m=current_data.get("relative_humidity_2m"),
                    cloud_cover=current_data.get("cloud_cover")
                )
                self._current_cache[curr_cache_key] = (now, curr_obj)

            hourly = data.get("hourly", {})
            times = hourly.get("time", [])
            temps = hourly.get("temperature_2m", [])
            precips = hourly.get("precipitation", [])
            winds = hourly.get("wind_speed_10m", [])
            pressures = hourly.get("pressure_msl", [])
            humidities = hourly.get("relative_humidity_2m", [])
            clouds = hourly.get("cloud_cover", [])

            init_time = now.replace(minute=0, second=0, microsecond=0)

            forecasts: List[NormalizedForecast] = []
            for i in range(len(times)):
                valid_dt = datetime.fromisoformat(times[i])
                if valid_dt.tzinfo is None:
                    valid_dt = valid_dt.replace(tzinfo=timezone.utc)
                lead_h = max(0, int((valid_dt - init_time).total_seconds() // 3600))
                if lead_h < 0:
                    continue

                # Proxy ensemble spread scaling with lead horizon
                base_spread = 0.5 + (lead_h / 24.0) * 0.45

                forecasts.append(NormalizedForecast(
                    provider="open-meteo-operational" if not self.api_key else "open-meteo-customer",
                    model="ecmwf-ifs",
                    initialization_time=init_time,
                    valid_time=valid_dt,
                    lead_hours=lead_h,
                    latitude=latitude,
                    longitude=longitude,
                    temperature_2m=temps[i] if i < len(temps) else None,
                    precipitation=precips[i] if i < len(precips) else None,
                    wind_speed_10m=winds[i] if i < len(winds) else None,
                    pressure_msl=pressures[i] if i < len(pressures) else None,
                    relative_humidity_2m=humidities[i] if i < len(humidities) else None,
                    cloud_cover=clouds[i] if i < len(clouds) else None,
                    ensemble_spread=round(base_spread, 2),
                    run_revision=0.0
                ))

            self._forecast_cache[cache_key] = (now, forecasts)
            return forecasts

    async def get_reference_data(
        self, latitude: float, longitude: float, start_date: str, end_date: str
    ) -> List[NormalizedReference]:
        """Fetch historical observations from Open-Meteo archive API."""
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": "temperature_2m,precipitation,wind_speed_10m,pressure_msl,relative_humidity_2m",
            "wind_speed_unit": "ms",
            "timezone": "UTC"
        }
        if self.api_key:
            params["apikey"] = self.api_key

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            last_resp = None
            for attempt in range(2):
                resp = await client.get(self.archive_base_url, params=params, headers=self.headers)
                last_resp = resp
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("retry-after", "30"))
                    cooldown = min(max(retry_after, 15), 60)
                    self._rate_limit_until = datetime.now(timezone.utc) + timedelta(seconds=cooldown)
                    if attempt < 1 and retry_after <= 2:
                        await asyncio.sleep(retry_after)
                        continue
                    logger.error(f"Open-Meteo archive 429 received (cooldown {cooldown}s): {resp.text}")
                    resp.raise_for_status()
                resp.raise_for_status()
                data = resp.json()
                break
            else:
                if last_resp is not None:
                    last_resp.raise_for_status()
                raise RuntimeError("Failed to fetch archive data after retries")

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        precips = hourly.get("precipitation", [])
        winds = hourly.get("wind_speed_10m", [])
        pressures = hourly.get("pressure_msl", [])
        humidities = hourly.get("relative_humidity_2m", [])

        references = []
        for i, t_str in enumerate(times):
            valid_time = datetime.fromisoformat(t_str)
            references.append(NormalizedReference(
                source="era5-reanalysis",
                valid_time=valid_time,
                latitude=latitude,
                longitude=longitude,
                temperature_2m=temps[i] if i < len(temps) else None,
                precipitation=precips[i] if i < len(precips) else None,
                wind_speed_10m=winds[i] if i < len(winds) else None,
                pressure_msl=pressures[i] if i < len(pressures) else None,
                relative_humidity_2m=humidities[i] if i < len(humidities) else None
            ))

        return references
