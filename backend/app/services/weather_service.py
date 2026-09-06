"""
Weather Service.
Coordinates operational NWP forecasts, current weather observations,
and geocoding through configured provider adapters (Open-Meteo, Google Weather, Demo).
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from backend.app.config import settings
from data_pipeline.providers.open_meteo import OpenMeteoProvider
from data_pipeline.providers.google_weather import GoogleWeatherProvider
from data_pipeline.providers.demo_provider import DemoProvider
from data_pipeline.providers.geocoding import CompositeGeocodingProvider, GeocodedLocation
from data_pipeline.providers.base import NormalizedForecast, NormalizedReference


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

    async def get_forecast(self, lat: float, lon: float, days: int = 10, demo_mode: bool = False) -> List[NormalizedForecast]:
        provider = self.get_active_provider(force_demo=demo_mode)
        try:
            return await provider.get_forecast(lat, lon, days=days)
        except Exception:
            # Automatic graceful fallback to verified benchmark demo provider
            return await self.demo_provider.get_forecast(lat, lon, days=days)

    async def get_reference_history(
        self, lat: float, lon: float, start_date: str, end_date: str, demo_mode: bool = False
    ) -> List[NormalizedReference]:
        provider = self.get_active_provider(force_demo=demo_mode)
        try:
            return await provider.get_reference_data(lat, lon, start_date, end_date)
        except Exception:
            return await self.demo_provider.get_reference_data(lat, lon, start_date, end_date)
