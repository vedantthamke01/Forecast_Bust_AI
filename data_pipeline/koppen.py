"""
Global Köppen-Geiger Macro-Climate Classifier & Solar Astronomical Engine.
Provides standardized, mathematically robust climate regime classification and
hemisphere-aware astronomical solar angle features strictly available at forecast initialization T0.

Features derived:
1. Macro-Climate Regime (Tropical, Arid, Temperate, Continental, Polar/Alpine)
2. Latitude-adjusted Solar Declination Angle (δ)
3. Solar Noon Zenith Angle Proxy (Z_noon = |lat - δ|)
4. Hemisphere-aware seasonal phase features
"""
import math
from typing import Dict, Any


# Macro Climate Regime Definitions
REGIME_TROPICAL = "TROPICAL"          # Zone A: Equatorial, Monsoon, Savanna
REGIME_ARID = "ARID"                  # Zone B: Desert, Semi-Arid, Steppe
REGIME_TEMPERATE = "TEMPERATE"        # Zone C: Mediterranean, Marine West Coast, Humid Subtropical
REGIME_CONTINENTAL = "CONTINENTAL"    # Zone D: Warm Summer, Continental Subarctic
REGIME_POLAR_ALPINE = "POLAR_ALPINE"  # Zone E: Tundra, Ice Cap, High Elevation Alpine

REGIME_ENCODINGS = {
    REGIME_TROPICAL: 0,
    REGIME_ARID: 1,
    REGIME_TEMPERATE: 2,
    REGIME_CONTINENTAL: 3,
    REGIME_POLAR_ALPINE: 4
}


def calculate_solar_declination(day_of_year: int) -> float:
    """
    Computes Earth's solar declination angle in degrees for a given day of the year (1-366).
    Cooper's approximation: delta = -23.44 * cos(2 * pi * (day + 10) / 365.25)
    Strictly deterministic and computable at initialization T0 anywhere on Earth.
    """
    rad = 2.0 * math.pi * (float(day_of_year) + 10.0) / 365.25
    return -23.44 * math.cos(rad)


def calculate_solar_zenith_proxy(latitude: float, day_of_year: int) -> float:
    """
    Calculates solar noon zenith angle proxy in degrees: Z_noon = |latitude - delta|.
    Ranges from 0° (overhead sun at noon) to ~113.4° (polar winter).
    """
    delta = calculate_solar_declination(day_of_year)
    return round(abs(latitude - delta), 2)


def calculate_seasonality_features(latitude: float, day_of_year: int) -> Dict[str, float]:
    """
    Computes hemisphere-aware astronomical cyclical features at T0.
    In the Southern Hemisphere (latitude < 0), seasons are phase-shifted by 180° (6 months).
    """
    # Base fractional year angle
    phase_rad = 2.0 * math.pi * (float(day_of_year) - 1.0) / 365.25
    if latitude < 0:
        # Southern hemisphere: add pi phase shift so that max solar insolation corresponds to Dec-Feb
        phase_rad = (phase_rad + math.pi) % (2.0 * math.pi)

    sin_seasonal = round(math.sin(phase_rad), 4)
    cos_seasonal = round(math.cos(phase_rad), 4)
    zenith_proxy = calculate_solar_zenith_proxy(latitude, day_of_year)

    # Approximate daylight hours proxy based on latitude and declination
    delta_rad = math.radians(calculate_solar_declination(day_of_year))
    lat_rad = math.radians(max(-89.9, min(89.9, latitude)))
    
    # Hour angle at sunrise/sunset: cos(omega) = -tan(phi) * tan(delta)
    tan_prod = -math.tan(lat_rad) * math.tan(delta_rad)
    if tan_prod >= 1.0:
        day_length = 0.0  # Polar night
    elif tan_prod <= -1.0:
        day_length = 24.0  # Midnight sun
    else:
        omega = math.acos(tan_prod)
        day_length = round(24.0 * omega / math.pi, 2)

    return {
        "sin_seasonal_phase": sin_seasonal,
        "cos_seasonal_phase": cos_seasonal,
        "solar_zenith_noon": zenith_proxy,
        "daylight_hours_proxy": day_length
    }


def classify_koppen_regime(
    latitude: float,
    longitude: float,
    elevation: float = 0.0,
    annual_precip_est: float = 800.0,
    mean_temp_est: float = 20.0
) -> Dict[str, Any]:
    """
    Determines the macro Köppen-Geiger climate regime using geographic,
    orographic (elevation), and thermal parameters.
    """
    abs_lat = abs(latitude)

    # 1. Polar / High Alpine check
    if abs_lat >= 66.5 or elevation >= 2500.0:
        regime = REGIME_POLAR_ALPINE
    elif elevation >= 1500.0 and abs_lat >= 30.0:
        regime = REGIME_POLAR_ALPINE
    # 2. Tropical Zone (equatorial band without severe dry anomaly)
    elif abs_lat <= 23.5 and elevation < 1500.0:
        # Check for tropical deserts (e.g. Sahara / Arabian / Thar fringes)
        if 15.0 <= abs_lat <= 23.5 and ((10.0 <= longitude <= 55.0) or (68.0 <= longitude <= 75.0 and latitude > 24.0)):
            regime = REGIME_ARID
        else:
            regime = REGIME_TROPICAL
    # 3. Arid / Desert belts (15° to 35° latitude in continental dry zones)
    elif 15.0 <= abs_lat <= 38.0 and (
        # North Africa / Middle East
        (-15.0 <= longitude <= 60.0 and latitude > 12.0) or
        # Central Asia / Gobi / Thar
        (65.0 <= longitude <= 105.0 and 24.0 <= latitude <= 45.0) or
        # North American Southwest
        (-120.0 <= longitude <= -100.0 and 25.0 <= latitude <= 38.0) or
        # Australia Outback
        (115.0 <= longitude <= 145.0 and -35.0 <= latitude <= -18.0) or
        # Atacama / Patagonia
        (-75.0 <= longitude <= -65.0 and -35.0 <= latitude <= -18.0)
    ):
        regime = REGIME_ARID
    # 4. Continental Zone (dominated by Northern Hemisphere vast landmasses)
    elif latitude >= 40.0 and not (-15.0 <= longitude <= 5.0):  # Exclude maritime Western Europe
        regime = REGIME_CONTINENTAL
    # 5. Temperate Zone (default mid-latitude maritime, subtropical humid, Mediterranean)
    else:
        regime = REGIME_TEMPERATE

    # Geographic feature proxies
    is_mountain = elevation >= 1000.0
    is_tropical = regime == REGIME_TROPICAL
    is_arid = regime == REGIME_ARID

    return {
        "macro_regime": regime,
        "regime_code": REGIME_ENCODINGS[regime],
        "is_mountain": int(is_mountain),
        "is_tropical": int(is_tropical),
        "is_arid": int(is_arid)
    }
