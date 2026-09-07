"""
Weather Service.
Coordinates operational NWP forecasts, current weather observations,
and geocoding through configured provider adapters (Open-Meteo, Google Weather, Demo).
Enforces strict scientific data provenance with NO silent synthetic demo fallbacks.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException

from backend.app.config import settings
from data_pipeline.providers.open_meteo import OpenMeteoProvider
from data_pipeline.providers.google_weather import GoogleWeatherProvider
from data_pipeline.providers.demo_provider import DemoProvider
from data_pipeline.providers.geocoding import CompositeGeocodingProvider, GeocodedLocation
from data_pipeline.providers.base import NormalizedForecast, NormalizedReference, NormalizedCurrentWeather

logger = logging.getLogger(__name__)


class WeatherService:
    def __init__(self):
        self.geocoder = CompositeGeocodingProvider()
        self.open_meteo = OpenMeteoProvider()
        self.google_weather = GoogleWeatherProvider()
        self.demo_provider = DemoProvider()

    def get_active_provider(self, force_demo: bool = False):
        if force_demo or settings.DEMO_MODE:
            return self.demo_provider
        if self.google_weather.is_available():
            return self.google_weather
        return self.open_meteo

    async def search_locations(self, query: str) -> List[GeocodedLocation]:
        return await self.geocoder.search(query)

    async def reverse_geocode(self, lat: float, lon: float) -> Optional[GeocodedLocation]:
        return await self.geocoder.reverse(lat, lon)

    async def get_current_weather(
        self, lat: float, lon: float, demo_mode: bool = False
    ) -> NormalizedCurrentWeather:
        """Fetch current weather conditions adhering strictly to DEMO_MODE and explicit demo requests.

        Never silently falls back to synthetic DemoProvider when DEMO_MODE=false.
        """
        if demo_mode or settings.DEMO_MODE:
            logger.info(f"Serving demo current weather for ({lat}, {lon}) (demo_mode={demo_mode}, settings.DEMO_MODE={settings.DEMO_MODE})")
            return await self.demo_provider.get_current_weather(lat, lon)

        provider = self.get_active_provider(force_demo=False)
        try:
            return await provider.get_current_weather(lat, lon)
        except Exception as e:
            logger.error(
                f"Live current weather provider ({provider.get_provider_name()}) failed for ({lat}, {lon}): {e}",
                exc_info=True
            )
            # NEVER silently substitute synthetic DemoProvider when DEMO_MODE=false
            raise HTTPException(
                status_code=503,
                detail=f"Live weather observation unavailable from {provider.get_provider_name()}: {type(e).__name__} ({str(e)}). External operational service unreachable."
            )

    async def get_forecast(
        self, lat: float, lon: float, days: int = 10, demo_mode: bool = False
    ) -> List[NormalizedForecast]:
        """Fetch operational multi-day medium range forecast horizons.

        Never silently falls back to synthetic DemoProvider when DEMO_MODE=false.
        """
        if demo_mode or settings.DEMO_MODE:
            logger.info(f"Serving demo forecast for ({lat}, {lon}) (demo_mode={demo_mode}, settings.DEMO_MODE={settings.DEMO_MODE})")
            return await self.demo_provider.get_forecast(lat, lon, days=days)

        provider = self.get_active_provider(force_demo=False)
        try:
            return await provider.get_forecast(lat, lon, days=days)
        except Exception as e:
            logger.error(
                f"Operational forecast provider ({provider.get_provider_name()}) failed for ({lat}, {lon}): {e}",
                exc_info=True
            )
            # NEVER silently substitute synthetic DemoProvider when DEMO_MODE=false
            raise HTTPException(
                status_code=503,
                detail=f"Operational forecast unavailable from {provider.get_provider_name()}: {type(e).__name__} ({str(e)}). External NWP service unreachable."
            )

    async def get_reference_history(
        self, lat: float, lon: float, start_date: str, end_date: str, demo_mode: bool = False
    ) -> List[NormalizedReference]:
        """Fetch historical ground-truth reference data.

        Never silently falls back to synthetic DemoProvider when DEMO_MODE=false.
        """
        if demo_mode or settings.DEMO_MODE:
            logger.info(f"Serving demo reference history for ({lat}, {lon}) (demo_mode={demo_mode}, settings.DEMO_MODE={settings.DEMO_MODE})")
            return await self.demo_provider.get_reference_data(lat, lon, start_date, end_date)

        provider = self.get_active_provider(force_demo=False)
        try:
            return await provider.get_reference_data(lat, lon, start_date, end_date)
        except Exception as e:
            logger.error(
                f"Reference weather provider ({provider.get_provider_name()}) failed for ({lat}, {lon}): {e}",
                exc_info=True
            )
            raise HTTPException(
                status_code=503,
                detail=f"Reference weather observations unavailable from {provider.get_provider_name()}: {type(e).__name__} ({str(e)})."
            )
