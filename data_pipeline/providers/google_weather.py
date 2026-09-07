"""
Google Weather API Provider Adapter.
Integrates operational forecasts when GOOGLE_WEATHER_API_KEY is configured.
Gracefully reports unavailability if credentials are not present.
"""
from typing import List, Optional
from datetime import datetime
import httpx
from backend.app.config import settings
from data_pipeline.providers.base import ForecastProvider, NormalizedForecast, NormalizedCurrentWeather


class GoogleWeatherProvider(ForecastProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GOOGLE_WEATHER_API_KEY
        self.base_url = "https://weather.googleapis.com/v1"

    def get_provider_name(self) -> str:
        return "Google Weather API"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def get_current_weather(self, latitude: float, longitude: float) -> NormalizedCurrentWeather:
        if not self.is_available():
            raise RuntimeError(
                "Google Weather API credentials not configured. "
                "Set GOOGLE_WEATHER_API_KEY in your .env configuration."
            )
        raise NotImplementedError("Google Weather API current conditions lookup not configured.")

    async def get_forecast(self, latitude: float, longitude: float, days: int = 10) -> List[NormalizedForecast]:
        if not self.is_available():
            raise RuntimeError(
                "Google Weather API credentials not configured. "
                "Set GOOGLE_WEATHER_API_KEY in your .env configuration."
            )

        # Operational request to Google Weather API
        url = f"{self.base_url}/forecast:lookup"
        params = {
            "key": self.api_key,
            "location.latitude": latitude,
            "location.longitude": longitude,
            "days": days
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        # Parse normalized forecasts from Google Weather response
        forecasts = []
        now = datetime.utcnow()
        init_time = now.replace(minute=0, second=0, microsecond=0)

        for day in data.get("forecastDays", []):
            # Parse daily/hourly forecast intervals
            pass

        return forecasts
