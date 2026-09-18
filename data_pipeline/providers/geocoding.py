"""
Geocoding Provider Implementations.
Combines OpenStreetMap Nominatim for live online searching with a rich
embedded database of Indian synoptic weather stations and major cities
for instantaneous, reliable, offline-capable operation.
"""
from typing import List, Optional
import httpx
import math
from data_pipeline.providers.base import GeocodingProvider, GeocodedLocation

# Pre-seeded Indian meteorological and synoptic observatories
INDIAN_CITIES_DB = [
    {"name": "Pune", "district": "Pune", "state": "Maharashtra", "lat": 18.5204, "lon": 73.8567, "elevation": 560.0, "country": "India", "climate_regime": "TROPICAL"},
    {"name": "New Delhi", "district": "New Delhi", "state": "Delhi", "lat": 28.6139, "lon": 77.2090, "elevation": 216.0, "country": "India", "climate_regime": "ARID"},
    {"name": "Noida (NCMRWF HQ)", "district": "Gautam Buddha Nagar", "state": "Uttar Pradesh", "lat": 28.5355, "lon": 77.3910, "elevation": 200.0, "country": "India", "climate_regime": "ARID"},
    {"name": "Mumbai", "district": "Mumbai City", "state": "Maharashtra", "lat": 19.0760, "lon": 72.8777, "elevation": 14.0, "country": "India", "climate_regime": "TROPICAL"},
    {"name": "Bengaluru", "district": "Bengaluru Urban", "state": "Karnataka", "lat": 12.9716, "lon": 77.5946, "elevation": 920.0, "country": "India", "climate_regime": "TROPICAL"},
    {"name": "Chennai", "district": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lon": 80.2707, "elevation": 6.0, "country": "India", "climate_regime": "TROPICAL"},
    {"name": "Kolkata", "district": "Kolkata", "state": "West Bengal", "lat": 22.5726, "lon": 88.3639, "elevation": 9.0, "country": "India", "climate_regime": "TROPICAL"},
    {"name": "Hyderabad", "district": "Hyderabad", "state": "Telangana", "lat": 17.3850, "lon": 78.4867, "elevation": 505.0, "country": "India", "climate_regime": "TROPICAL"},
    {"name": "Ahmedabad", "district": "Ahmedabad", "state": "Gujarat", "lat": 23.0225, "lon": 72.5714, "elevation": 53.0, "country": "India", "climate_regime": "ARID"},
    {"name": "Jaipur", "district": "Jaipur", "state": "Rajasthan", "lat": 26.9124, "lon": 75.7873, "elevation": 431.0, "country": "India", "climate_regime": "ARID"},
    {"name": "Shimla", "district": "Shimla", "state": "Himachal Pradesh", "lat": 31.1048, "lon": 77.1734, "elevation": 2276.0, "country": "India", "climate_regime": "POLAR_ALPINE"},
    {"name": "Guwahati", "district": "Kamrup Metropolitan", "state": "Assam", "lat": 26.1445, "lon": 91.7362, "elevation": 55.0, "country": "India", "climate_regime": "TROPICAL"},
    {"name": "Srinagar", "district": "Srinagar", "state": "Jammu and Kashmir", "lat": 34.0837, "lon": 74.7973, "elevation": 1585.0, "country": "India", "climate_regime": "POLAR_ALPINE"},
    {"name": "Thiruvananthapuram", "district": "Thiruvananthapuram", "state": "Kerala", "lat": 8.5241, "lon": 76.9366, "elevation": 10.0, "country": "India", "climate_regime": "TROPICAL"},
    {"name": "Bhubaneswar", "district": "Khordha", "state": "Odisha", "lat": 20.2961, "lon": 85.8245, "elevation": 45.0, "country": "India", "climate_regime": "TROPICAL"},
    {"name": "Bhopal", "district": "Bhopal", "state": "Madhya Pradesh", "lat": 23.2599, "lon": 77.4126, "elevation": 527.0, "country": "India", "climate_regime": "TROPICAL"},
    {"name": "Visakhapatnam", "district": "Visakhapatnam", "state": "Andhra Pradesh", "lat": 17.6868, "lon": 83.2185, "elevation": 45.0, "country": "India", "climate_regime": "TROPICAL"},
    {"name": "Patna", "district": "Patna", "state": "Bihar", "lat": 25.5941, "lon": 85.1376, "elevation": 53.0, "country": "India", "climate_regime": "TROPICAL"},
    {"name": "Lucknow", "district": "Lucknow", "state": "Uttar Pradesh", "lat": 26.8467, "lon": 80.9462, "elevation": 123.0, "country": "India", "climate_regime": "TROPICAL"},
    {"name": "Nagpur", "district": "Nagpur", "state": "Maharashtra", "lat": 21.1458, "lon": 79.0882, "elevation": 310.0, "country": "India", "climate_regime": "TROPICAL"},
    {"name": "Dehradun", "district": "Dehradun", "state": "Uttarakhand", "lat": 30.3165, "lon": 78.0322, "elevation": 640.0, "country": "India", "climate_regime": "TEMPERATE"},
    {"name": "Ranchi", "district": "Ranchi", "state": "Jharkhand", "lat": 23.3441, "lon": 85.3096, "elevation": 651.0, "country": "India", "climate_regime": "TROPICAL"},
    {"name": "Chandigarh", "district": "Chandigarh", "state": "Chandigarh", "lat": 30.7333, "lon": 76.7794, "elevation": 321.0, "country": "India", "climate_regime": "TEMPERATE"},
    {"name": "Panaji", "district": "North Goa", "state": "Goa", "lat": 15.4909, "lon": 73.8278, "elevation": 7.0, "country": "India", "climate_regime": "TROPICAL"},
    {"name": "Shillong", "district": "East Khasi Hills", "state": "Meghalaya", "lat": 25.5788, "lon": 91.8933, "elevation": 1525.0, "country": "India", "climate_regime": "POLAR_ALPINE"},
]

# Global benchmark synoptic observatories representing all Köppen climate regimes
GLOBAL_BENCHMARK_STATIONS = INDIAN_CITIES_DB + [
    # Europe (Temperate, Mediterranean, Continental)
    {"name": "London", "district": "Greater London", "state": "England", "lat": 51.5074, "lon": -0.1278, "elevation": 25.0, "country": "United Kingdom", "climate_regime": "TEMPERATE"},
    {"name": "Paris", "district": "Île-de-France", "state": "France", "lat": 48.8566, "lon": 2.3522, "elevation": 35.0, "country": "France", "climate_regime": "TEMPERATE"},
    {"name": "Frankfurt", "district": "Hesse", "state": "Germany", "lat": 50.1109, "lon": 8.6821, "elevation": 112.0, "country": "Germany", "climate_regime": "TEMPERATE"},
    {"name": "Rome", "district": "Lazio", "state": "Italy", "lat": 41.9028, "lon": 12.4964, "elevation": 21.0, "country": "Italy", "climate_regime": "TEMPERATE"},
    {"name": "Athens", "district": "Attica", "state": "Greece", "lat": 37.9838, "lon": 23.7275, "elevation": 170.0, "country": "Greece", "climate_regime": "TEMPERATE"},
    {"name": "Warsaw", "district": "Mazovia", "state": "Poland", "lat": 52.2297, "lon": 21.0122, "elevation": 100.0, "country": "Poland", "climate_regime": "CONTINENTAL"},
    {"name": "Zurich", "district": "Zurich", "state": "Switzerland", "lat": 47.3769, "lon": 8.5417, "elevation": 408.0, "country": "Switzerland", "climate_regime": "TEMPERATE"},
    {"name": "Madrid", "district": "Community of Madrid", "state": "Spain", "lat": 40.4168, "lon": -3.7038, "elevation": 667.0, "country": "Spain", "climate_regime": "TEMPERATE"},
    {"name": "Oslo", "district": "Oslo", "state": "Norway", "lat": 59.9139, "lon": 10.7522, "elevation": 23.0, "country": "Norway", "climate_regime": "CONTINENTAL"},

    # North America (Continental, Arid, Subtropical, Marine)
    {"name": "New York", "district": "New York City", "state": "New York", "lat": 40.7128, "lon": -74.0060, "elevation": 10.0, "country": "USA", "climate_regime": "TEMPERATE"},
    {"name": "Chicago", "district": "Cook County", "state": "Illinois", "lat": 41.8781, "lon": -87.6298, "elevation": 181.0, "country": "USA", "climate_regime": "CONTINENTAL"},
    {"name": "Miami", "district": "Miami-Dade County", "state": "Florida", "lat": 25.7617, "lon": -80.1918, "elevation": 2.0, "country": "USA", "climate_regime": "TROPICAL"},
    {"name": "Los Angeles", "district": "Los Angeles County", "state": "California", "lat": 34.0522, "lon": -118.2437, "elevation": 87.0, "country": "USA", "climate_regime": "TEMPERATE"},
    {"name": "Seattle", "district": "King County", "state": "Washington", "lat": 47.6062, "lon": -122.3321, "elevation": 53.0, "country": "USA", "climate_regime": "TEMPERATE"},
    {"name": "Denver", "district": "Denver County", "state": "Colorado", "lat": 39.7392, "lon": -104.9903, "elevation": 1609.0, "country": "USA", "climate_regime": "POLAR_ALPINE"},
    {"name": "Phoenix", "district": "Maricopa County", "state": "Arizona", "lat": 33.4484, "lon": -112.0740, "elevation": 331.0, "country": "USA", "climate_regime": "ARID"},
    {"name": "Montreal", "district": "Quebec", "state": "Quebec", "lat": 45.5017, "lon": -73.5673, "elevation": 36.0, "country": "Canada", "climate_regime": "CONTINENTAL"},

    # South America (Tropical, Arid, Alpine)
    {"name": "Sao Paulo", "district": "Sao Paulo", "state": "Sao Paulo", "lat": -23.5505, "lon": -46.6333, "elevation": 760.0, "country": "Brazil", "climate_regime": "TEMPERATE"},
    {"name": "Manaus", "district": "Amazonas", "state": "Amazonas", "lat": -3.1190, "lon": -60.0217, "elevation": 92.0, "country": "Brazil", "climate_regime": "TROPICAL"},
    {"name": "Buenos Aires", "district": "Buenos Aires", "state": "Argentina", "lat": -34.6037, "lon": -58.3816, "elevation": 25.0, "country": "Argentina", "climate_regime": "TEMPERATE"},
    {"name": "Santiago", "district": "Santiago", "state": "Chile", "lat": -33.4489, "lon": -70.6693, "elevation": 570.0, "country": "Chile", "climate_regime": "TEMPERATE"},
    {"name": "Lima", "district": "Lima", "state": "Peru", "lat": -12.0464, "lon": -77.0428, "elevation": 154.0, "country": "Peru", "climate_regime": "ARID"},
    {"name": "La Paz", "district": "La Paz", "state": "Bolivia", "lat": -16.5000, "lon": -68.1500, "elevation": 3640.0, "country": "Bolivia", "climate_regime": "POLAR_ALPINE"},

    # Asia & Middle East (Tropical, Continental, Arid)
    {"name": "Tokyo", "district": "Kanto", "state": "Tokyo", "lat": 35.6762, "lon": 139.6503, "elevation": 40.0, "country": "Japan", "climate_regime": "TEMPERATE"},
    {"name": "Singapore", "district": "Singapore", "state": "Singapore", "lat": 1.3521, "lon": 103.8198, "elevation": 15.0, "country": "Singapore", "climate_regime": "TROPICAL"},
    {"name": "Jakarta", "district": "Java", "state": "Indonesia", "lat": -6.2088, "lon": 106.8456, "elevation": 8.0, "country": "Indonesia", "climate_regime": "TROPICAL"},
    {"name": "Bangkok", "district": "Bangkok", "state": "Thailand", "lat": 13.7563, "lon": 100.5018, "elevation": 1.5, "country": "Thailand", "climate_regime": "TROPICAL"},
    {"name": "Seoul", "district": "Seoul", "state": "South Korea", "lat": 37.5665, "lon": 126.9780, "elevation": 38.0, "country": "South Korea", "climate_regime": "CONTINENTAL"},
    {"name": "Riyadh", "district": "Riyadh", "state": "Saudi Arabia", "lat": 24.7136, "lon": 46.6753, "elevation": 612.0, "country": "Saudi Arabia", "climate_regime": "ARID"},
    {"name": "Dubai", "district": "Dubai", "state": "UAE", "lat": 25.2048, "lon": 55.2708, "elevation": 5.0, "country": "UAE", "climate_regime": "ARID"},

    # Africa (Tropical, Desert, Mediterranean, Highland)
    {"name": "Cairo", "district": "Cairo", "state": "Egypt", "lat": 30.0444, "lon": 31.2357, "elevation": 23.0, "country": "Egypt", "climate_regime": "ARID"},
    {"name": "Lagos", "district": "Lagos", "state": "Nigeria", "lat": 6.5244, "lon": 3.3792, "elevation": 41.0, "country": "Nigeria", "climate_regime": "TROPICAL"},
    {"name": "Nairobi", "district": "Nairobi", "state": "Kenya", "lat": -1.2921, "lon": 36.8219, "elevation": 1795.0, "country": "Kenya", "climate_regime": "TEMPERATE"},
    {"name": "Johannesburg", "district": "Gauteng", "state": "South Africa", "lat": -26.2041, "lon": 28.0473, "elevation": 1753.0, "country": "South Africa", "climate_regime": "TEMPERATE"},
    {"name": "Cape Town", "district": "Western Cape", "state": "South Africa", "lat": -33.9249, "lon": 18.4241, "elevation": 12.0, "country": "South Africa", "climate_regime": "TEMPERATE"},
    {"name": "Addis Ababa", "district": "Addis Ababa", "state": "Ethiopia", "lat": 9.0320, "lon": 38.7469, "elevation": 2355.0, "country": "Ethiopia", "climate_regime": "POLAR_ALPINE"},

    # Oceania (Maritime, Arid, Tropical)
    {"name": "Sydney", "district": "New South Wales", "state": "Australia", "lat": -33.8688, "lon": 151.2093, "elevation": 19.0, "country": "Australia", "climate_regime": "TEMPERATE"},
    {"name": "Melbourne", "district": "Victoria", "state": "Australia", "lat": -37.8136, "lon": 144.9631, "elevation": 31.0, "country": "Australia", "climate_regime": "TEMPERATE"},
    {"name": "Alice Springs", "district": "Northern Territory", "state": "Australia", "lat": -23.6980, "lon": 133.8807, "elevation": 545.0, "country": "Australia", "climate_regime": "ARID"},
    {"name": "Darwin", "district": "Northern Territory", "state": "Australia", "lat": -12.4634, "lon": 130.8456, "elevation": 30.0, "country": "Australia", "climate_regime": "TROPICAL"},
    {"name": "Auckland", "district": "Auckland", "state": "New Zealand", "lat": -36.8485, "lon": 174.7633, "elevation": 20.0, "country": "New Zealand", "climate_regime": "TEMPERATE"},
]


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class CompositeGeocodingProvider(GeocodingProvider):
    """Combines Nominatim online lookup with global benchmark synoptic observatories database."""

    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.nominatim_url = "https://nominatim.openstreetmap.org/search"
        self.reverse_url = "https://nominatim.openstreetmap.org/reverse"

    async def search(self, query: str, limit: int = 10) -> List[GeocodedLocation]:
        query_clean = query.strip().lower()
        results: List[GeocodedLocation] = []

        # 1. Search embedded global benchmark stations database first
        for city in GLOBAL_BENCHMARK_STATIONS:
            if (query_clean in city["name"].lower() or
                (city.get("district") and query_clean in city["district"].lower()) or
                (city.get("state") and query_clean in city["state"].lower()) or
                (city.get("country") and query_clean in city["country"].lower())):
                results.append(GeocodedLocation(
                    name=city["name"],
                    latitude=city["lat"],
                    longitude=city["lon"],
                    district=city.get("district"),
                    state=city.get("state"),
                    elevation=city.get("elevation", 0.0)
                ))
                if len(results) >= limit:
                    return results

        # 2. If results found in local DB, return them
        if results:
            return results

        # 3. Fallback to OpenStreetMap Nominatim for broader worldwide search
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {"User-Agent": "ForecastBustAI/2.0 (Global-Observatory)"}
                params = {
                    "q": query,
                    "format": "json",
                    "limit": limit
                }
                resp = await client.get(self.nominatim_url, params=params, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data:
                        display = item.get("display_name", "").split(",")
                        name = display[0].strip() if display else item.get("name", query)
                        results.append(GeocodedLocation(
                            name=name,
                            latitude=float(item["lat"]),
                            longitude=float(item["lon"]),
                            district=display[1].strip() if len(display) > 1 else None,
                            state=display[-2].strip() if len(display) > 2 else None,
                            elevation=0.0
                        ))
        except Exception:
            # Network fallback if offline: return nearest or partial match from DB
            pass

        return results

    async def reverse(self, latitude: float, longitude: float) -> Optional[GeocodedLocation]:
        # 1. Find nearest synoptic station in our global database
        nearest_city = None
        min_dist = float("inf")
        for city in GLOBAL_BENCHMARK_STATIONS:
            dist = _haversine_distance(latitude, longitude, city["lat"], city["lon"])
            if dist < min_dist:
                min_dist = dist
                nearest_city = city

        if nearest_city and min_dist <= 100.0:  # Within 100 km
            return GeocodedLocation(
                name=nearest_city["name"],
                latitude=latitude,
                longitude=longitude,
                district=nearest_city.get("district"),
                state=nearest_city.get("state"),
                elevation=nearest_city.get("elevation", 0.0)
            )

        # 2. Try online reverse geocoding
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {"User-Agent": "SIH26079-NCMRWF-ForecastBustDetector/1.0"}
                params = {
                    "lat": latitude,
                    "lon": longitude,
                    "format": "json"
                }
                resp = await client.get(self.reverse_url, params=params, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    addr = data.get("address", {})
                    name = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county") or "Observation Point"
                    return GeocodedLocation(
                        name=name,
                        latitude=latitude,
                        longitude=longitude,
                        district=addr.get("county"),
                        state=addr.get("state"),
                        elevation=0.0
                    )
        except Exception:
            pass

        # Fallback to coordinates descriptor
        return GeocodedLocation(
            name=f"Lat {latitude:.2f}°, Lon {longitude:.2f}°",
            latitude=latitude,
            longitude=longitude,
            elevation=0.0
        )
