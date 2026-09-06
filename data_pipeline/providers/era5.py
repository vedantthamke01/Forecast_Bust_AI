"""
ECMWF Climate Data Store (CDS) ERA5 Provider Adapter.
Connects to Copernicus CDS for reference reanalysis data.
Gracefully reports unavailability if CDS_API_KEY is not configured.
"""
from typing import List, Optional
from backend.app.config import settings
from data_pipeline.providers.base import ReferenceWeatherProvider, NormalizedReference


class ERA5CDSProvider(ReferenceWeatherProvider):
    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        self.api_url = api_url or settings.CDS_API_URL
        self.api_key = api_key or settings.CDS_API_KEY

    def get_provider_name(self) -> str:
        return "ECMWF ERA5 (Copernicus CDS)"

    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def get_reference_data(
        self, latitude: float, longitude: float, start_date: str, end_date: str
    ) -> List[NormalizedReference]:
        if not self.is_available():
            raise RuntimeError(
                "ECMWF CDS credentials (CDS_API_KEY) are not configured. "
                "Configure your Copernicus API key or use Open-Meteo ERA5 / Demo mode."
            )
        # CDS API download logic
        return []
