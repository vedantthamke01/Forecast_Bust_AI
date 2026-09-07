"""
Abstract Base Classes for Data Providers.
Decouples operational weather retrieval, reanalysis observations,
and geocoding from specific third-party APIs.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class NormalizedForecast(BaseModel):
    provider: str
    model: str
    initialization_time: datetime
    valid_time: datetime
    lead_hours: int
    latitude: float
    longitude: float
    temperature_2m: Optional[float] = None          # °C
    precipitation: Optional[float] = None           # mm
    wind_speed_10m: Optional[float] = None          # m/s
    pressure_msl: Optional[float] = None            # hPa
    relative_humidity_2m: Optional[float] = None    # %
    cloud_cover: Optional[float] = None             # %
    ensemble_spread: float = 0.0
    run_revision: float = 0.0


class NormalizedReference(BaseModel):
    source: str
    valid_time: datetime
    latitude: float
    longitude: float
    temperature_2m: Optional[float] = None          # °C
    precipitation: Optional[float] = None           # mm
    wind_speed_10m: Optional[float] = None          # m/s
    pressure_msl: Optional[float] = None            # hPa
    relative_humidity_2m: Optional[float] = None    # %


class GeocodedLocation(BaseModel):
    name: str
    latitude: float
    longitude: float
    district: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    elevation: float = 0.0


class NormalizedCurrentWeather(BaseModel):
    provider: str
    model: str
    observation_time: datetime
    latitude: float
    longitude: float
    temperature_2m: Optional[float] = None          # °C
    precipitation: Optional[float] = None           # mm
    wind_speed_10m: Optional[float] = None          # m/s (guaranteed)
    pressure_msl: Optional[float] = None            # hPa
    relative_humidity_2m: Optional[float] = None    # %
    cloud_cover: Optional[float] = None             # %


class ForecastProvider(ABC):
    """Interface for operational and live Numerical Weather Prediction forecasts."""

    @abstractmethod
    async def get_forecast(self, latitude: float, longitude: float, days: int = 10) -> List[NormalizedForecast]:
        """Retrieve operational multi-day forecast up to 240 hours."""
        pass

    @abstractmethod
    async def get_current_weather(self, latitude: float, longitude: float) -> NormalizedCurrentWeather:
        """Retrieve authentic real-time current weather observation."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider credentials or endpoint are operational."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Provider identification string."""
        pass


class HistoricalForecastProvider(ABC):
    """Interface for archived NWP model runs issued at initialization time T."""

    @abstractmethod
    async def get_historical_forecast(
        self, latitude: float, longitude: float, start_date: str, end_date: str
    ) -> List[NormalizedForecast]:
        """Fetch past forecast runs with their original lead times."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass


class ReferenceWeatherProvider(ABC):
    """Interface for ground truth observation and reanalysis datasets (ERA5, IMD)."""

    @abstractmethod
    async def get_reference_data(
        self, latitude: float, longitude: float, start_date: str, end_date: str
    ) -> List[NormalizedReference]:
        """Fetch historical observations or reanalysis corresponding to valid times."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass


class GeocodingProvider(ABC):
    """Interface for forward and reverse geocoding."""

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[GeocodedLocation]:
        pass

    @abstractmethod
    async def reverse(self, latitude: float, longitude: float) -> Optional[GeocodedLocation]:
        pass
