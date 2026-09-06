"""
ECMWF Climate Data Store (CDS) Configuration Helper CLI.
Creates %USERPROFILE%/.cdsapirc with official Copernicus credentials.
Usage:
    python -m data_pipeline.setup_cds --key YOUR_PERSONAL_ACCESS_TOKEN
"""
import argparse
import os
from data_pipeline.providers.era5 import write_cdsapirc, check_cdsapirc_exists


def configure_cds(key: str, url: str = "https://cds.climate.copernicus.eu/api"):
    path = write_cdsapirc(url, key)
    print("\n==================================================")
    print("[+] ECMWF CLIMATE DATA STORE (CDS) CONFIGURED")
    print("==================================================")
    print(f" File created: {path}")
    print(f" Endpoint:     {url}")
    print(f" Key length:   {len(key)} chars")
    print("[+] You can now programmatically retrieve ERA5 reanalysis data.")
    print("==================================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Configure ECMWF CDS credentials (.cdsapirc)")
    parser.add_argument("--key", type=str, required=True, help="Your CDS Personal Access Token")
    parser.add_argument("--url", type=str, default="https://cds.climate.copernicus.eu/api", help="CDS API URL")
    args = parser.parse_args()
    configure_cds(args.key, args.url)
