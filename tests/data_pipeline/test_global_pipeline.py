"""
Tests for Global Benchmark Observatories, Climate Regimes, and Astronomical Solar Engine.
Verifies worldwide coordinate handling across all major Köppen-Geiger zones.
"""
import pytest
from data_pipeline.providers.geocoding import GLOBAL_BENCHMARK_STATIONS, CompositeGeocodingProvider
from data_pipeline.koppen import (
    classify_koppen_regime,
    calculate_solar_declination,
    calculate_solar_zenith_proxy,
    calculate_seasonality_features,
    REGIME_TROPICAL,
    REGIME_ARID,
    REGIME_TEMPERATE,
    REGIME_CONTINENTAL,
    REGIME_POLAR_ALPINE
)


def test_global_benchmark_stations_coverage():
    """Verify that global benchmark stations database spans all continents and key regimes."""
    assert len(GLOBAL_BENCHMARK_STATIONS) >= 50

    countries = set(s.get("country") for s in GLOBAL_BENCHMARK_STATIONS)
    assert len(countries) >= 15

    regimes = set(s.get("climate_regime") for s in GLOBAL_BENCHMARK_STATIONS)
    assert {REGIME_TROPICAL, REGIME_ARID, REGIME_TEMPERATE, REGIME_CONTINENTAL, REGIME_POLAR_ALPINE}.issubset(regimes)

    # All coordinates must be valid
    for s in GLOBAL_BENCHMARK_STATIONS:
        assert -90 <= s["lat"] <= 90
        assert -180 <= s["lon"] <= 180
        assert s.get("elevation") is not None


@pytest.mark.parametrize("lat,lon,elev,expected_regime", [
    (1.35, 103.82, 15.0, REGIME_TROPICAL),         # Singapore (Equatorial)
    (-3.12, -60.02, 92.0, REGIME_TROPICAL),        # Manaus (Amazon)
    (30.04, 31.24, 23.0, REGIME_ARID),             # Cairo (Sahara/Arid)
    (24.71, 46.68, 612.0, REGIME_ARID),            # Riyadh (Arabian Desert)
    (51.51, -0.13, 25.0, REGIME_TEMPERATE),        # London (Maritime West Coast)
    (48.86, 2.35, 35.0, REGIME_TEMPERATE),         # Paris (Temperate)
    (41.88, -87.63, 181.0, REGIME_CONTINENTAL),    # Chicago (Humid Continental)
    (52.23, 21.01, 100.0, REGIME_CONTINENTAL),     # Warsaw (Continental Europe)
    (-16.50, -68.15, 3640.0, REGIME_POLAR_ALPINE), # La Paz (High Alpine Andes)
    (31.10, 77.17, 2276.0, REGIME_POLAR_ALPINE)    # Shimla (Himalayan Alpine)
])
def test_koppen_regime_classification(lat, lon, elev, expected_regime):
    """Verify macro climate classification across representative global coordinates."""
    res = classify_koppen_regime(latitude=lat, longitude=lon, elevation=elev)
    assert res["macro_regime"] == expected_regime
    assert 0 <= res["regime_code"] <= 4


def test_astronomical_solar_engine():
    """Verify solar declination and zenith angles across seasons and hemispheres."""
    # Equinox (around day 80): declination near 0°
    dec_equinox = calculate_solar_declination(80)
    assert abs(dec_equinox) <= 3.0

    # Summer solstice (day 172): declination near +23.44°
    dec_summer = calculate_solar_declination(172)
    assert 22.0 <= dec_summer <= 23.5

    # Winter solstice (day 355): declination near -23.44°
    dec_winter = calculate_solar_declination(355)
    assert -23.5 <= dec_winter <= -22.0

    # Zenith angle at equator on equinox is near 0°
    zenith_eq = calculate_solar_zenith_proxy(0.0, 80)
    assert zenith_eq <= 3.0

    # Hemisphere-aware seasonality
    nh_season = calculate_seasonality_features(latitude=45.0, day_of_year=172)
    sh_season = calculate_seasonality_features(latitude=-45.0, day_of_year=172)

    assert -1.0 <= nh_season["sin_seasonal_phase"] <= 1.0
    assert -1.0 <= sh_season["sin_seasonal_phase"] <= 1.0
    # Day length in NH summer is long (> 14h)
    assert nh_season["daylight_hours_proxy"] >= 14.0
    # Day length in SH winter is short (< 10h)
    assert sh_season["daylight_hours_proxy"] <= 10.0


@pytest.mark.asyncio
async def test_global_geocoding_search():
    """Verify offline and fallback search finds global benchmark cities."""
    provider = CompositeGeocodingProvider()

    for city in ["London", "Tokyo", "New York", "Cairo", "Sydney", "Pune"]:
        results = await provider.search(city, limit=3)
        assert len(results) > 0
        names = [r.name.lower() for r in results]
        assert any(city.lower() in n for n in names)
