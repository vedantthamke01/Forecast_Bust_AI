"""
ECMWF Climate Data Store (CDS) ERA5 Provider Adapter.
Connects to Copernicus CDS using the official `cdsapi` client for reference reanalysis data.
Supports credentials via %USERPROFILE%/.cdsapirc or environment variables (CDS_API_URL, CDS_API_KEY).
"""
from typing import List, Optional
import os
from datetime import datetime
from backend.app.config import settings
from data_pipeline.providers.base import ReferenceWeatherProvider, NormalizedReference

try:
    import cdsapi
    CDSAPI_INSTALLED = True
except ImportError:
    CDSAPI_INSTALLED = False


def check_cdsapirc_exists() -> bool:
    """Checks if .cdsapirc exists in user's home directory."""
    home_dir = os.path.expanduser("~")
    cdsapirc_path = os.path.join(home_dir, ".cdsapirc")
    return os.path.exists(cdsapirc_path)


def write_cdsapirc(url: str, key: str) -> str:
    """Creates %USERPROFILE%/.cdsapirc with url and personal access token."""
    home_dir = os.path.expanduser("~")
    cdsapirc_path = os.path.join(home_dir, ".cdsapirc")
    content = f"url: {url.strip()}\nkey: {key.strip()}\n"
    with open(cdsapirc_path, "w") as f:
        f.write(content)
    return cdsapirc_path


class ERA5CDSProvider(ReferenceWeatherProvider):
    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        self.api_url = api_url or settings.CDS_API_URL or "https://cds.climate.copernicus.eu/api"
        self.api_key = api_key or settings.CDS_API_KEY

    def get_provider_name(self) -> str:
        return "ECMWF ERA5 (Copernicus CDS API)"

    def is_available(self) -> bool:
        if not CDSAPI_INSTALLED:
            return False
        # Available if .cdsapirc file exists or API key is passed
        return check_cdsapirc_exists() or bool(self.api_key and self.api_key.strip())

    def get_client(self):
        if not self.is_available():
            raise RuntimeError(
                "ECMWF CDS credentials are not configured. "
                "Set your key in %USERPROFILE%/.cdsapirc or configure CDS_API_KEY in .env."
            )
        if self.api_key:
            return cdsapi.Client(url=self.api_url, key=self.api_key)
        return cdsapi.Client()

    async def get_reference_data(
        self, latitude: float, longitude: float, start_date: str, end_date: str
    ) -> List[NormalizedReference]:
        if not self.is_available():
            raise RuntimeError(
                "ECMWF CDS credentials (CDS_API_KEY or .cdsapirc) not found. "
                "System is operating in verified ₹0 fallback mode."
            )

        client = self.get_client()
        # Parse date range
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        # Example bounding box query for synoptic India
        area_bounds = [
            min(38.0, latitude + 0.25),
            max(68.0, longitude - 0.25),
            max(6.0, latitude - 0.25),
            min(98.0, longitude + 0.25)
        ]

        target_file = os.path.join("datasets", "raw", f"era5_{start_date}_{end_date}.nc")
        os.makedirs(os.path.dirname(target_file), exist_ok=True)

        try:
            # Request reanalysis-era5-single-levels
            client.retrieve(
                "reanalysis-era5-single-levels",
                {
                    "product_type": "reanalysis",
                    "variable": [
                        "2m_temperature",
                        "total_precipitation",
                        "10m_u_component_of_wind",
                        "10m_v_component_of_wind",
                        "mean_sea_level_pressure"
                    ],
                    "year": str(start_dt.year),
                    "month": f"{start_dt.month:02d}",
                    "day": f"{start_dt.day:02d}",
                    "time": ["00:00", "06:00", "12:00", "18:00"],
                    "area": area_bounds,
                    "format": "netcdf"
                },
                target_file
            )
        except Exception as e:
            print(f"[!] CDS API download error: {e}")

        return []
