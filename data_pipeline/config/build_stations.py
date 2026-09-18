"""
Curates, validates, and exports the 200 Global Synoptic Weather Stations Catalog
for Forecast Bust AI (SIH26079) dataset expansion.
Covers 6 inhabited continents, 5 Köppen climate regimes, and diverse geographic categories.
"""
import os
import json
from typing import List, Dict, Any

STATIONS: List[Dict[str, Any]] = [
    # =========================================================================
    # 1. ASIA (50 Stations: 25 India + 25 International Asia)
    # =========================================================================
    # India (Synoptic Network)
    {"station_id": "STN_IND_PUNE", "name": "Pune", "lat": 18.5204, "lon": 73.8567, "elevation": 560.0, "country": "India", "continent": "Asia", "climate_category": "TROPICAL", "geographic_category": "INLAND"},
    {"station_id": "STN_IND_NEWDELHI", "name": "New Delhi", "lat": 28.6139, "lon": 77.2090, "elevation": 216.0, "country": "India", "continent": "Asia", "climate_category": "ARID", "geographic_category": "INLAND"},
    {"station_id": "STN_IND_NOIDA", "name": "Noida (NCMRWF)", "lat": 28.5355, "lon": 77.3910, "elevation": 200.0, "country": "India", "continent": "Asia", "climate_category": "ARID", "geographic_category": "INLAND"},
    {"station_id": "STN_IND_MUMBAI", "name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "elevation": 14.0, "country": "India", "continent": "Asia", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_IND_BENGALURU", "name": "Bengaluru", "lat": 12.9716, "lon": 77.5946, "elevation": 920.0, "country": "India", "continent": "Asia", "climate_category": "TROPICAL", "geographic_category": "INLAND"},
    {"station_id": "STN_IND_CHENNAI", "name": "Chennai", "lat": 13.0827, "lon": 80.2707, "elevation": 6.0, "country": "India", "continent": "Asia", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_IND_KOLKATA", "name": "Kolkata", "lat": 22.5726, "lon": 88.3639, "elevation": 9.0, "country": "India", "continent": "Asia", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_IND_HYDERABAD", "name": "Hyderabad", "lat": 17.3850, "lon": 78.4867, "elevation": 505.0, "country": "India", "continent": "Asia", "climate_category": "TROPICAL", "geographic_category": "INLAND"},
    {"station_id": "STN_IND_AHMEDABAD", "name": "Ahmedabad", "lat": 23.0225, "lon": 72.5714, "elevation": 53.0, "country": "India", "continent": "Asia", "climate_category": "ARID", "geographic_category": "INLAND"},
    {"station_id": "STN_IND_JAIPUR", "name": "Jaipur", "lat": 26.9124, "lon": 75.7873, "elevation": 431.0, "country": "India", "continent": "Asia", "climate_category": "ARID", "geographic_category": "DESERT_ARID"},
    {"station_id": "STN_IND_SHIMLA", "name": "Shimla", "lat": 31.1048, "lon": 77.1734, "elevation": 2276.0, "country": "India", "continent": "Asia", "climate_category": "POLAR_ALPINE", "geographic_category": "MOUNTAIN_ALPINE"},
    {"station_id": "STN_IND_GUWAHATI", "name": "Guwahati", "lat": 26.1445, "lon": 91.7362, "elevation": 55.0, "country": "India", "continent": "Asia", "climate_category": "TROPICAL", "geographic_category": "INLAND"},
    {"station_id": "STN_IND_SRINAGAR", "name": "Srinagar", "lat": 34.0837, "lon": 74.7973, "elevation": 1585.0, "country": "India", "continent": "Asia", "climate_category": "POLAR_ALPINE", "geographic_category": "MOUNTAIN_ALPINE"},
    {"station_id": "STN_IND_THIRUVANANTHAPURAM", "name": "Thiruvananthapuram", "lat": 8.5241, "lon": 76.9366, "elevation": 10.0, "country": "India", "continent": "Asia", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_IND_BHUBANESWAR", "name": "Bhubaneswar", "lat": 20.2961, "lon": 85.8245, "elevation": 45.0, "country": "India", "continent": "Asia", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_IND_BHOPAL", "name": "Bhopal", "lat": 23.2599, "lon": 77.4126, "elevation": 527.0, "country": "India", "continent": "Asia", "climate_category": "TROPICAL", "geographic_category": "INLAND"},
    {"station_id": "STN_IND_VISAKHAPATNAM", "name": "Visakhapatnam", "lat": 17.6868, "lon": 83.2185, "elevation": 45.0, "country": "India", "continent": "Asia", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_IND_PATNA", "name": "Patna", "lat": 25.5941, "lon": 85.1376, "elevation": 53.0, "country": "India", "continent": "Asia", "climate_category": "TROPICAL", "geographic_category": "INLAND"},
    {"station_id": "STN_IND_LUCKNOW", "name": "Lucknow", "lat": 26.8467, "lon": 80.9462, "elevation": 123.0, "country": "India", "continent": "Asia", "climate_category": "TROPICAL", "geographic_category": "INLAND"},
    {"station_id": "STN_IND_NAGPUR", "name": "Nagpur", "lat": 21.1458, "lon": 79.0882, "elevation": 310.0, "country": "India", "continent": "Asia", "climate_category": "TROPICAL", "geographic_category": "INLAND"},
    {"station_id": "STN_IND_DEHRADUN", "name": "Dehradun", "lat": 30.3165, "lon": 78.0322, "elevation": 640.0, "country": "India", "continent": "Asia", "climate_category": "TEMPERATE", "geographic_category": "MOUNTAIN_ALPINE"},
    {"station_id": "STN_IND_RANCHI", "name": "Ranchi", "lat": 23.3441, "lon": 85.3096, "elevation": 651.0, "country": "India", "continent": "Asia", "climate_category": "TROPICAL", "geographic_category": "INLAND"},
    {"station_id": "STN_IND_CHANDIGARH", "name": "Chandigarh", "lat": 30.7333, "lon": 76.7794, "elevation": 321.0, "country": "India", "continent": "Asia", "climate_category": "TEMPERATE", "geographic_category": "INLAND"},
    {"station_id": "STN_IND_PANAJI", "name": "Panaji", "lat": 15.4909, "lon": 73.8278, "elevation": 7.0, "country": "India", "continent": "Asia", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_IND_SHILLONG", "name": "Shillong", "lat": 25.5788, "lon": 91.8933, "elevation": 1525.0, "country": "India", "continent": "Asia", "climate_category": "POLAR_ALPINE", "geographic_category": "MOUNTAIN_ALPINE"},
    # International Asia
    {"station_id": "STN_JPN_TOKYO", "name": "Tokyo", "lat": 35.6762, "lon": 139.6503, "elevation": 40.0, "country": "Japan", "continent": "Asia", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_JPN_OSAKA", "name": "Osaka", "lat": 34.6937, "lon": 135.5023, "elevation": 20.0, "country": "Japan", "continent": "Asia", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_JPN_SAPPORO", "name": "Sapporo", "lat": 43.0618, "lon": 141.3545, "elevation": 25.0, "country": "Japan", "continent": "Asia", "climate_category": "CONTINENTAL", "geographic_category": "INLAND"},
    {"station_id": "STN_KOR_SEOUL", "name": "Seoul", "lat": 37.5665, "lon": 126.9780, "elevation": 38.0, "country": "South Korea", "continent": "Asia", "climate_category": "CONTINENTAL", "geographic_category": "INLAND"},
    {"station_id": "STN_KOR_BUSAN", "name": "Busan", "lat": 35.1796, "lon": 129.0756, "elevation": 15.0, "country": "South Korea", "continent": "Asia", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_CHN_BEIJING", "name": "Beijing", "lat": 39.9042, "lon": 116.4074, "elevation": 44.0, "country": "China", "continent": "Asia", "climate_category": "CONTINENTAL", "geographic_category": "INLAND"},
    {"station_id": "STN_CHN_SHANGHAI", "name": "Shanghai", "lat": 31.2304, "lon": 121.4737, "elevation": 4.0, "country": "China", "continent": "Asia", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_CHN_GUANGZHOU", "name": "Guangzhou", "lat": 23.1291, "lon": 113.2644, "elevation": 21.0, "country": "China", "continent": "Asia", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_CHN_CHENGDU", "name": "Chengdu", "lat": 30.5728, "lon": 104.0668, "elevation": 500.0, "country": "China", "continent": "Asia", "climate_category": "TEMPERATE", "geographic_category": "INLAND"},
    {"station_id": "STN_CHN_URUMQI", "name": "Urumqi", "lat": 43.8256, "lon": 87.6168, "elevation": 800.0, "country": "China", "continent": "Asia", "climate_category": "ARID", "geographic_category": "DESERT_ARID"},
    {"station_id": "STN_SGP_SINGAPORE", "name": "Singapore", "lat": 1.3521, "lon": 103.8198, "elevation": 15.0, "country": "Singapore", "continent": "Asia", "climate_category": "TROPICAL", "geographic_category": "ISLAND"},
    {"station_id": "STN_THA_BANGKOK", "name": "Bangkok", "lat": 13.7563, "lon": 100.5018, "elevation": 2.0, "country": "Thailand", "continent": "Asia", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_IDN_JAKARTA", "name": "Jakarta", "lat": -6.2088, "lon": 106.8456, "elevation": 8.0, "country": "Indonesia", "continent": "Asia", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_MYS_KUALALUMPUR", "name": "Kuala Lumpur", "lat": 3.1390, "lon": 101.6869, "elevation": 22.0, "country": "Malaysia", "continent": "Asia", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_PHL_MANILA", "name": "Manila", "lat": 14.5995, "lon": 120.9842, "elevation": 16.0, "country": "Philippines", "continent": "Asia", "climate_category": "TROPICAL", "geographic_category": "ISLAND"},
    {"station_id": "STN_VNM_HANOI", "name": "Hanoi", "lat": 21.0285, "lon": 105.8542, "elevation": 10.0, "country": "Vietnam", "continent": "Asia", "climate_category": "TROPICAL", "geographic_category": "INLAND"},
    {"station_id": "STN_SAU_RIYADH", "name": "Riyadh", "lat": 24.7136, "lon": 46.6753, "elevation": 612.0, "country": "Saudi Arabia", "continent": "Asia", "climate_category": "ARID", "geographic_category": "DESERT_ARID"},
    {"station_id": "STN_SAU_JEDDAH", "name": "Jeddah", "lat": 21.4858, "lon": 39.1925, "elevation": 12.0, "country": "Saudi Arabia", "continent": "Asia", "climate_category": "ARID", "geographic_category": "COASTAL"},
    {"station_id": "STN_ARE_DUBAI", "name": "Dubai", "lat": 25.2048, "lon": 55.2708, "elevation": 5.0, "country": "United Arab Emirates", "continent": "Asia", "climate_category": "ARID", "geographic_category": "COASTAL"},
    {"station_id": "STN_KAZ_ALMATY", "name": "Almaty", "lat": 43.2220, "lon": 76.8512, "elevation": 785.0, "country": "Kazakhstan", "continent": "Asia", "climate_category": "CONTINENTAL", "geographic_category": "MOUNTAIN_ALPINE"},
    {"station_id": "STN_UZB_TASHKENT", "name": "Tashkent", "lat": 41.2995, "lon": 69.2401, "elevation": 455.0, "country": "Uzbekistan", "continent": "Asia", "climate_category": "ARID", "geographic_category": "INLAND"},
    {"station_id": "STN_NPL_KATHMANDU", "name": "Kathmandu", "lat": 27.7172, "lon": 85.3240, "elevation": 1400.0, "country": "Nepal", "continent": "Asia", "climate_category": "TEMPERATE", "geographic_category": "MOUNTAIN_ALPINE"},
    {"station_id": "STN_LKA_COLOMBO", "name": "Colombo", "lat": 6.9271, "lon": 79.8612, "elevation": 7.0, "country": "Sri Lanka", "continent": "Asia", "climate_category": "TROPICAL", "geographic_category": "ISLAND"},
    {"station_id": "STN_BGD_DHAKA", "name": "Dhaka", "lat": 23.8103, "lon": 90.4125, "elevation": 4.0, "country": "Bangladesh", "continent": "Asia", "climate_category": "TROPICAL", "geographic_category": "INLAND"},
    {"station_id": "STN_MNG_ULAANBAATAR", "name": "Ulaanbaatar", "lat": 47.8864, "lon": 106.9057, "elevation": 1350.0, "country": "Mongolia", "continent": "Asia", "climate_category": "POLAR_ALPINE", "geographic_category": "MOUNTAIN_ALPINE"},

    # =========================================================================
    # 2. EUROPE (45 Stations)
    # =========================================================================
    {"station_id": "STN_GBR_LONDON", "name": "London", "lat": 51.5074, "lon": -0.1278, "elevation": 25.0, "country": "United Kingdom", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "INLAND"},
    {"station_id": "STN_GBR_MANCHESTER", "name": "Manchester", "lat": 53.4808, "lon": -2.2426, "elevation": 38.0, "country": "United Kingdom", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "INLAND"},
    {"station_id": "STN_GBR_EDINBURGH", "name": "Edinburgh", "lat": 55.9533, "lon": -3.1883, "elevation": 47.0, "country": "United Kingdom", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_FRA_PARIS", "name": "Paris", "lat": 48.8566, "lon": 2.3522, "elevation": 35.0, "country": "France", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "INLAND"},
    {"station_id": "STN_FRA_MARSEILLE", "name": "Marseille", "lat": 43.2965, "lon": 5.3698, "elevation": 12.0, "country": "France", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_FRA_LYON", "name": "Lyon", "lat": 45.7640, "lon": 4.8357, "elevation": 173.0, "country": "France", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "INLAND"},
    {"station_id": "STN_DEU_FRANKFURT", "name": "Frankfurt", "lat": 50.1109, "lon": 8.6821, "elevation": 112.0, "country": "Germany", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "INLAND"},
    {"station_id": "STN_DEU_BERLIN", "name": "Berlin", "lat": 52.5200, "lon": 13.4050, "elevation": 34.0, "country": "Germany", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "INLAND"},
    {"station_id": "STN_DEU_MUNICH", "name": "Munich", "lat": 48.1351, "lon": 11.5820, "elevation": 519.0, "country": "Germany", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "INLAND"},
    {"station_id": "STN_DEU_HAMBURG", "name": "Hamburg", "lat": 53.5511, "lon": 9.9937, "elevation": 6.0, "country": "Germany", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_ITA_ROME", "name": "Rome", "lat": 41.9028, "lon": 12.4964, "elevation": 21.0, "country": "Italy", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_ITA_MILAN", "name": "Milan", "lat": 45.4642, "lon": 9.1900, "elevation": 120.0, "country": "Italy", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "INLAND"},
    {"station_id": "STN_ITA_NAPLES", "name": "Naples", "lat": 40.8518, "lon": 14.2681, "elevation": 17.0, "country": "Italy", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_ESP_MADRID", "name": "Madrid", "lat": 40.4168, "lon": -3.7038, "elevation": 667.0, "country": "Spain", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "INLAND"},
    {"station_id": "STN_ESP_BARCELONA", "name": "Barcelona", "lat": 41.3879, "lon": 2.1699, "elevation": 12.0, "country": "Spain", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_ESP_SEVILLE", "name": "Seville", "lat": 37.3891, "lon": -5.9845, "elevation": 7.0, "country": "Spain", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "INLAND"},
    {"station_id": "STN_GRC_ATHENS", "name": "Athens", "lat": 37.9838, "lon": 23.7275, "elevation": 170.0, "country": "Greece", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_GRC_THESSALONIKI", "name": "Thessaloniki", "lat": 40.6401, "lon": 22.9444, "elevation": 5.0, "country": "Greece", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_POL_WARSAW", "name": "Warsaw", "lat": 52.2297, "lon": 21.0122, "elevation": 100.0, "country": "Poland", "continent": "Europe", "climate_category": "CONTINENTAL", "geographic_category": "INLAND"},
    {"station_id": "STN_POL_KRAKOW", "name": "Krakow", "lat": 50.0647, "lon": 19.9450, "elevation": 219.0, "country": "Poland", "continent": "Europe", "climate_category": "CONTINENTAL", "geographic_category": "INLAND"},
    {"station_id": "STN_CHE_ZURICH", "name": "Zurich", "lat": 47.3769, "lon": 8.5417, "elevation": 408.0, "country": "Switzerland", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "MOUNTAIN_ALPINE"},
    {"station_id": "STN_CHE_GENEVA", "name": "Geneva", "lat": 46.2044, "lon": 6.1432, "elevation": 375.0, "country": "Switzerland", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "MOUNTAIN_ALPINE"},
    {"station_id": "STN_AUT_VIENNA", "name": "Vienna", "lat": 48.2082, "lon": 16.3738, "elevation": 171.0, "country": "Austria", "continent": "Europe", "climate_category": "CONTINENTAL", "geographic_category": "INLAND"},
    {"station_id": "STN_AUT_INNSBRUCK", "name": "Innsbruck", "lat": 47.2692, "lon": 11.4041, "elevation": 574.0, "country": "Austria", "continent": "Europe", "climate_category": "POLAR_ALPINE", "geographic_category": "MOUNTAIN_ALPINE"},
    {"station_id": "STN_NOR_OSLO", "name": "Oslo", "lat": 59.9139, "lon": 10.7522, "elevation": 23.0, "country": "Norway", "continent": "Europe", "climate_category": "CONTINENTAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_NOR_BERGEN", "name": "Bergen", "lat": 60.3913, "lon": 5.3221, "elevation": 12.0, "country": "Norway", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_SWE_STOCKHOLM", "name": "Stockholm", "lat": 59.3293, "lon": 18.0686, "elevation": 28.0, "country": "Sweden", "continent": "Europe", "climate_category": "CONTINENTAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_SWE_GOTHENBURG", "name": "Gothenburg", "lat": 57.7089, "lon": 11.9746, "elevation": 12.0, "country": "Sweden", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_FIN_HELSINKI", "name": "Helsinki", "lat": 60.1699, "lon": 24.9384, "elevation": 25.0, "country": "Finland", "continent": "Europe", "climate_category": "CONTINENTAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_IRL_DUBLIN", "name": "Dublin", "lat": 53.3498, "lon": -6.2603, "elevation": 20.0, "country": "Ireland", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "ISLAND"},
    {"station_id": "STN_PRT_LISBON", "name": "Lisbon", "lat": 38.7223, "lon": -9.1393, "elevation": 100.0, "country": "Portugal", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_PRT_PORTO", "name": "Porto", "lat": 41.1579, "lon": -8.6291, "elevation": 83.0, "country": "Portugal", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_NLD_AMSTERDAM", "name": "Amsterdam", "lat": 52.3676, "lon": 4.9041, "elevation": 2.0, "country": "Netherlands", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_BEL_BRUSSELS", "name": "Brussels", "lat": 50.8503, "lon": 4.3517, "elevation": 13.0, "country": "Belgium", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "INLAND"},
    {"station_id": "STN_CZE_PRAGUE", "name": "Prague", "lat": 50.0755, "lon": 14.4378, "elevation": 200.0, "country": "Czech Republic", "continent": "Europe", "climate_category": "CONTINENTAL", "geographic_category": "INLAND"},
    {"station_id": "STN_HUN_BUDAPEST", "name": "Budapest", "lat": 47.4979, "lon": 19.0402, "elevation": 96.0, "country": "Hungary", "continent": "Europe", "climate_category": "CONTINENTAL", "geographic_category": "INLAND"},
    {"station_id": "STN_ROU_BUCHAREST", "name": "Bucharest", "lat": 44.4268, "lon": 26.1025, "elevation": 70.0, "country": "Romania", "continent": "Europe", "climate_category": "CONTINENTAL", "geographic_category": "INLAND"},
    {"station_id": "STN_BGR_SOFIA", "name": "Sofia", "lat": 42.6977, "lon": 23.3219, "elevation": 550.0, "country": "Bulgaria", "continent": "Europe", "climate_category": "CONTINENTAL", "geographic_category": "MOUNTAIN_ALPINE"},
    {"station_id": "STN_UKR_KYIV", "name": "Kyiv", "lat": 50.4501, "lon": 30.5234, "elevation": 179.0, "country": "Ukraine", "continent": "Europe", "climate_category": "CONTINENTAL", "geographic_category": "INLAND"},
    {"station_id": "STN_ISL_REYKJAVIK", "name": "Reykjavik", "lat": 64.1466, "lon": -21.9426, "elevation": 15.0, "country": "Iceland", "continent": "Europe", "climate_category": "POLAR_ALPINE", "geographic_category": "ISLAND"},
    {"station_id": "STN_TUR_ISTANBUL", "name": "Istanbul", "lat": 41.0082, "lon": 28.9784, "elevation": 40.0, "country": "Turkey", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_TUR_ANKARA", "name": "Ankara", "lat": 39.9334, "lon": 32.8597, "elevation": 938.0, "country": "Turkey", "continent": "Europe", "climate_category": "CONTINENTAL", "geographic_category": "INLAND"},
    {"station_id": "STN_DNK_COPENHAGEN", "name": "Copenhagen", "lat": 55.6761, "lon": 12.5683, "elevation": 5.0, "country": "Denmark", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_HRV_ZAGREB", "name": "Zagreb", "lat": 45.8150, "lon": 15.9819, "elevation": 120.0, "country": "Croatia", "continent": "Europe", "climate_category": "TEMPERATE", "geographic_category": "INLAND"},
    {"station_id": "STN_SRB_BELGRADE", "name": "Belgrade", "lat": 44.7866, "lon": 20.4489, "elevation": 117.0, "country": "Serbia", "continent": "Europe", "climate_category": "CONTINENTAL", "geographic_category": "INLAND"},

    # =========================================================================
    # 3. NORTH AMERICA (40 Stations)
    # =========================================================================
    {"station_id": "STN_USA_NEWYORK", "name": "New York", "lat": 40.7128, "lon": -74.0060, "elevation": 10.0, "country": "United States", "continent": "North America", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_USA_CHICAGO", "name": "Chicago", "lat": 41.8781, "lon": -87.6298, "elevation": 181.0, "country": "United States", "continent": "North America", "climate_category": "CONTINENTAL", "geographic_category": "INLAND"},
    {"station_id": "STN_USA_MIAMI", "name": "Miami", "lat": 25.7617, "lon": -80.1918, "elevation": 2.0, "country": "United States", "continent": "North America", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_USA_LOSANGELES", "name": "Los Angeles", "lat": 34.0522, "lon": -118.2437, "elevation": 87.0, "country": "United States", "continent": "North America", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_USA_SEATTLE", "name": "Seattle", "lat": 47.6062, "lon": -122.3321, "elevation": 53.0, "country": "United States", "continent": "North America", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_USA_DENVER", "name": "Denver", "lat": 39.7392, "lon": -104.9903, "elevation": 1609.0, "country": "United States", "continent": "North America", "climate_category": "POLAR_ALPINE", "geographic_category": "MOUNTAIN_ALPINE"},
    {"station_id": "STN_USA_PHOENIX", "name": "Phoenix", "lat": 33.4484, "lon": -112.0740, "elevation": 331.0, "country": "United States", "continent": "North America", "climate_category": "ARID", "geographic_category": "DESERT_ARID"},
    {"station_id": "STN_USA_HOUSTON", "name": "Houston", "lat": 29.7604, "lon": -95.3698, "elevation": 15.0, "country": "United States", "continent": "North America", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_USA_ATLANTA", "name": "Atlanta", "lat": 33.7490, "lon": -84.3880, "elevation": 320.0, "country": "United States", "continent": "North America", "climate_category": "TEMPERATE", "geographic_category": "INLAND"},
    {"station_id": "STN_USA_BOSTON", "name": "Boston", "lat": 42.3601, "lon": -71.0589, "elevation": 14.0, "country": "United States", "continent": "North America", "climate_category": "CONTINENTAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_USA_SANFRANCISCO", "name": "San Francisco", "lat": 37.7749, "lon": -122.4194, "elevation": 16.0, "country": "United States", "continent": "North America", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_USA_WASHINGTON", "name": "Washington D.C.", "lat": 38.9072, "lon": -77.0369, "elevation": 20.0, "country": "United States", "continent": "North America", "climate_category": "TEMPERATE", "geographic_category": "INLAND"},
    {"station_id": "STN_USA_DALLAS", "name": "Dallas", "lat": 32.7767, "lon": -96.7970, "elevation": 131.0, "country": "United States", "continent": "North America", "climate_category": "TEMPERATE", "geographic_category": "INLAND"},
    {"station_id": "STN_USA_MINNEAPOLIS", "name": "Minneapolis", "lat": 44.9778, "lon": -93.2650, "elevation": 260.0, "country": "United States", "continent": "North America", "climate_category": "CONTINENTAL", "geographic_category": "INLAND"},
    {"station_id": "STN_USA_NEWORLEANS", "name": "New Orleans", "lat": 29.9511, "lon": -90.0715, "elevation": 1.0, "country": "United States", "continent": "North America", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_USA_LASVEGAS", "name": "Las Vegas", "lat": 36.1699, "lon": -115.1398, "elevation": 610.0, "country": "United States", "continent": "North America", "climate_category": "ARID", "geographic_category": "DESERT_ARID"},
    {"station_id": "STN_USA_ANCHORAGE", "name": "Anchorage", "lat": 61.2181, "lon": -149.9003, "elevation": 30.0, "country": "United States", "continent": "North America", "climate_category": "POLAR_ALPINE", "geographic_category": "COASTAL"},
    {"station_id": "STN_USA_HONOLULU", "name": "Honolulu", "lat": 21.3069, "lon": -157.8583, "elevation": 6.0, "country": "United States", "continent": "North America", "climate_category": "TROPICAL", "geographic_category": "ISLAND"},
    {"station_id": "STN_USA_SALT_LAKE", "name": "Salt Lake City", "lat": 40.7608, "lon": -111.8910, "elevation": 1288.0, "country": "United States", "continent": "North America", "climate_category": "ARID", "geographic_category": "MOUNTAIN_ALPINE"},
    {"station_id": "STN_CAN_MONTREAL", "name": "Montreal", "lat": 45.5017, "lon": -73.5673, "elevation": 36.0, "country": "Canada", "continent": "North America", "climate_category": "CONTINENTAL", "geographic_category": "INLAND"},
    {"station_id": "STN_CAN_TORONTO", "name": "Toronto", "lat": 43.6532, "lon": -79.3832, "elevation": 76.0, "country": "Canada", "continent": "North America", "climate_category": "CONTINENTAL", "geographic_category": "INLAND"},
    {"station_id": "STN_CAN_VANCOUVER", "name": "Vancouver", "lat": 49.2827, "lon": -123.1207, "elevation": 4.0, "country": "Canada", "continent": "North America", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_CAN_CALGARY", "name": "Calgary", "lat": 51.0447, "lon": -114.0719, "elevation": 1045.0, "country": "Canada", "continent": "North America", "climate_category": "CONTINENTAL", "geographic_category": "MOUNTAIN_ALPINE"},
    {"station_id": "STN_CAN_EDMONTON", "name": "Edmonton", "lat": 53.5461, "lon": -113.4938, "elevation": 671.0, "country": "Canada", "continent": "North America", "climate_category": "CONTINENTAL", "geographic_category": "INLAND"},
    {"station_id": "STN_CAN_WINNIPEG", "name": "Winnipeg", "lat": 49.8951, "lon": -97.1384, "elevation": 239.0, "country": "Canada", "continent": "North America", "climate_category": "CONTINENTAL", "geographic_category": "INLAND"},
    {"station_id": "STN_CAN_HALIFAX", "name": "Halifax", "lat": 44.6488, "lon": -63.5752, "elevation": 20.0, "country": "Canada", "continent": "North America", "climate_category": "CONTINENTAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_CAN_OTTAWA", "name": "Ottawa", "lat": 45.4215, "lon": -75.6972, "elevation": 70.0, "country": "Canada", "continent": "North America", "climate_category": "CONTINENTAL", "geographic_category": "INLAND"},
    {"station_id": "STN_MEX_MEXICOCITY", "name": "Mexico City", "lat": 19.4326, "lon": -99.1332, "elevation": 2240.0, "country": "Mexico", "continent": "North America", "climate_category": "TEMPERATE", "geographic_category": "MOUNTAIN_ALPINE"},
    {"station_id": "STN_MEX_GUADALAJARA", "name": "Guadalajara", "lat": 20.6597, "lon": -103.3496, "elevation": 1566.0, "country": "Mexico", "continent": "North America", "climate_category": "TEMPERATE", "geographic_category": "INLAND"},
    {"station_id": "STN_MEX_MONTERREY", "name": "Monterrey", "lat": 25.6866, "lon": -100.3161, "elevation": 540.0, "country": "Mexico", "continent": "North America", "climate_category": "ARID", "geographic_category": "INLAND"},
    {"station_id": "STN_MEX_CANCUN", "name": "Cancun", "lat": 21.1619, "lon": -86.8515, "elevation": 10.0, "country": "Mexico", "continent": "North America", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_MEX_TIJUANA", "name": "Tijuana", "lat": 32.5149, "lon": -117.0382, "elevation": 20.0, "country": "Mexico", "continent": "North America", "climate_category": "ARID", "geographic_category": "COASTAL"},
    {"station_id": "STN_CUB_HAVANA", "name": "Havana", "lat": 23.1136, "lon": -82.3666, "elevation": 5.0, "country": "Cuba", "continent": "North America", "climate_category": "TROPICAL", "geographic_category": "ISLAND"},
    {"station_id": "STN_DOM_SANTODOMINGO", "name": "Santo Domingo", "lat": 18.4861, "lon": -69.9312, "elevation": 14.0, "country": "Dominican Republic", "continent": "North America", "climate_category": "TROPICAL", "geographic_category": "ISLAND"},
    {"station_id": "STN_JAM_KINGSTON", "name": "Kingston", "lat": 17.9712, "lon": -76.7936, "elevation": 9.0, "country": "Jamaica", "continent": "North America", "climate_category": "TROPICAL", "geographic_category": "ISLAND"},
    {"station_id": "STN_PRI_SANJUAN", "name": "San Juan", "lat": 18.4655, "lon": -66.1057, "elevation": 8.0, "country": "Puerto Rico", "continent": "North America", "climate_category": "TROPICAL", "geographic_category": "ISLAND"},
    {"station_id": "STN_GTM_GUATEMALACITY", "name": "Guatemala City", "lat": 14.6349, "lon": -90.5069, "elevation": 1500.0, "country": "Guatemala", "continent": "North America", "climate_category": "TEMPERATE", "geographic_category": "MOUNTAIN_ALPINE"},
    {"station_id": "STN_CRI_SANJOSE", "name": "San Jose", "lat": 9.9281, "lon": -84.0907, "elevation": 1172.0, "country": "Costa Rica", "continent": "North America", "climate_category": "TROPICAL", "geographic_category": "MOUNTAIN_ALPINE"},
    {"station_id": "STN_PAN_PANAMACITY", "name": "Panama City", "lat": 8.9824, "lon": -79.5199, "elevation": 10.0, "country": "Panama", "continent": "North America", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_BHS_NASSAU", "name": "Nassau", "lat": 25.0443, "lon": -77.3504, "elevation": 5.0, "country": "Bahamas", "continent": "North America", "climate_category": "TROPICAL", "geographic_category": "ISLAND"},

    # =========================================================================
    # 4. SOUTH AMERICA (25 Stations)
    # =========================================================================
    {"station_id": "STN_BRA_SAOPAULO", "name": "Sao Paulo", "lat": -23.5505, "lon": -46.6333, "elevation": 760.0, "country": "Brazil", "continent": "South America", "climate_category": "TEMPERATE", "geographic_category": "INLAND"},
    {"station_id": "STN_BRA_RIODEJANEIRO", "name": "Rio de Janeiro", "lat": -22.9068, "lon": -43.1729, "elevation": 10.0, "country": "Brazil", "continent": "South America", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_BRA_MANAUS", "name": "Manaus", "lat": -3.1190, "lon": -60.0217, "elevation": 92.0, "country": "Brazil", "continent": "South America", "climate_category": "TROPICAL", "geographic_category": "INLAND"},
    {"station_id": "STN_BRA_BRASILIA", "name": "Brasilia", "lat": -15.7975, "lon": -47.8919, "elevation": 1172.0, "country": "Brazil", "continent": "South America", "climate_category": "TROPICAL", "geographic_category": "INLAND"},
    {"station_id": "STN_BRA_FORTALEZA", "name": "Fortaleza", "lat": -3.7327, "lon": -38.5270, "elevation": 16.0, "country": "Brazil", "continent": "South America", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_BRA_PORTOALEGRE", "name": "Porto Alegre", "lat": -30.0346, "lon": -51.2177, "elevation": 10.0, "country": "Brazil", "continent": "South America", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_BRA_SALVADOR", "name": "Salvador", "lat": -12.9777, "lon": -38.5016, "elevation": 8.0, "country": "Brazil", "continent": "South America", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_ARG_BUENOSAIRES", "name": "Buenos Aires", "lat": -34.6037, "lon": -58.3816, "elevation": 25.0, "country": "Argentina", "continent": "South America", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_ARG_CORDOBA", "name": "Cordoba", "lat": -31.4201, "lon": -64.1888, "elevation": 390.0, "country": "Argentina", "continent": "South America", "climate_category": "TEMPERATE", "geographic_category": "INLAND"},
    {"station_id": "STN_ARG_MENDOZA", "name": "Mendoza", "lat": -32.8895, "lon": -68.8458, "elevation": 746.0, "country": "Argentina", "continent": "South America", "climate_category": "ARID", "geographic_category": "MOUNTAIN_ALPINE"},
    {"station_id": "STN_ARG_USHUAIA", "name": "Ushuaia", "lat": -54.8019, "lon": -68.3030, "elevation": 6.0, "country": "Argentina", "continent": "South America", "climate_category": "POLAR_ALPINE", "geographic_category": "COASTAL"},
    {"station_id": "STN_CHL_SANTIAGO", "name": "Santiago", "lat": -33.4489, "lon": -70.6693, "elevation": 570.0, "country": "Chile", "continent": "South America", "climate_category": "TEMPERATE", "geographic_category": "INLAND"},
    {"station_id": "STN_CHL_ANTOFAGASTA", "name": "Antofagasta", "lat": -23.6509, "lon": -70.3975, "elevation": 20.0, "country": "Chile", "continent": "South America", "climate_category": "ARID", "geographic_category": "COASTAL"},
    {"station_id": "STN_CHL_PUNTAARENAS", "name": "Punta Arenas", "lat": -53.1638, "lon": -70.9171, "elevation": 34.0, "country": "Chile", "continent": "South America", "climate_category": "POLAR_ALPINE", "geographic_category": "COASTAL"},
    {"station_id": "STN_PER_LIMA", "name": "Lima", "lat": -12.0464, "lon": -77.0428, "elevation": 154.0, "country": "Peru", "continent": "South America", "climate_category": "ARID", "geographic_category": "COASTAL"},
    {"station_id": "STN_PER_CUSCO", "name": "Cusco", "lat": -13.5319, "lon": -71.9675, "elevation": 3399.0, "country": "Peru", "continent": "South America", "climate_category": "POLAR_ALPINE", "geographic_category": "MOUNTAIN_ALPINE"},
    {"station_id": "STN_COL_BOGOTA", "name": "Bogota", "lat": 4.7110, "lon": -74.0721, "elevation": 2640.0, "country": "Colombia", "continent": "South America", "climate_category": "TEMPERATE", "geographic_category": "MOUNTAIN_ALPINE"},
    {"station_id": "STN_COL_MEDELLIN", "name": "Medellin", "lat": 6.2442, "lon": -75.5812, "elevation": 1495.0, "country": "Colombia", "continent": "South America", "climate_category": "TROPICAL", "geographic_category": "MOUNTAIN_ALPINE"},
    {"station_id": "STN_ECU_QUITO", "name": "Quito", "lat": -0.1807, "lon": -78.4678, "elevation": 2850.0, "country": "Ecuador", "continent": "South America", "climate_category": "TEMPERATE", "geographic_category": "MOUNTAIN_ALPINE"},
    {"station_id": "STN_ECU_GUAYAQUIL", "name": "Guayaquil", "lat": -2.1894, "lon": -79.8891, "elevation": 4.0, "country": "Ecuador", "continent": "South America", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_BOL_LAPAZ", "name": "La Paz", "lat": -16.5000, "lon": -68.1500, "elevation": 3640.0, "country": "Bolivia", "continent": "South America", "climate_category": "POLAR_ALPINE", "geographic_category": "MOUNTAIN_ALPINE"},
    {"station_id": "STN_BOL_SANTACRUZ", "name": "Santa Cruz", "lat": -17.7833, "lon": -63.1821, "elevation": 416.0, "country": "Bolivia", "continent": "South America", "climate_category": "TROPICAL", "geographic_category": "INLAND"},
    {"station_id": "STN_URY_MONTEVIDEO", "name": "Montevideo", "lat": -34.9011, "lon": -56.1645, "elevation": 43.0, "country": "Uruguay", "continent": "South America", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_PRY_ASUNCION", "name": "Asuncion", "lat": -25.2637, "lon": -57.5759, "elevation": 43.0, "country": "Paraguay", "continent": "South America", "climate_category": "TROPICAL", "geographic_category": "INLAND"},
    {"station_id": "STN_VEN_CARACAS", "name": "Caracas", "lat": 10.4806, "lon": -66.9036, "elevation": 900.0, "country": "Venezuela", "continent": "South America", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},

    # =========================================================================
    # 5. AFRICA (25 Stations)
    # =========================================================================
    {"station_id": "STN_EGY_CAIRO", "name": "Cairo", "lat": 30.0444, "lon": 31.2357, "elevation": 23.0, "country": "Egypt", "continent": "Africa", "climate_category": "ARID", "geographic_category": "DESERT_ARID"},
    {"station_id": "STN_EGY_ALEXANDRIA", "name": "Alexandria", "lat": 31.2001, "lon": 29.9187, "elevation": 5.0, "country": "Egypt", "continent": "Africa", "climate_category": "ARID", "geographic_category": "COASTAL"},
    {"station_id": "STN_NGA_LAGOS", "name": "Lagos", "lat": 6.5244, "lon": 3.3792, "elevation": 41.0, "country": "Nigeria", "continent": "Africa", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_NGA_ABUJA", "name": "Abuja", "lat": 9.0765, "lon": 7.3986, "elevation": 476.0, "country": "Nigeria", "continent": "Africa", "climate_category": "TROPICAL", "geographic_category": "INLAND"},
    {"station_id": "STN_NGA_KANO", "name": "Kano", "lat": 12.0022, "lon": 8.5920, "elevation": 481.0, "country": "Nigeria", "continent": "Africa", "climate_category": "ARID", "geographic_category": "INLAND"},
    {"station_id": "STN_KEN_NAIROBI", "name": "Nairobi", "lat": -1.2921, "lon": 36.8219, "elevation": 1795.0, "country": "Kenya", "continent": "Africa", "climate_category": "TEMPERATE", "geographic_category": "MOUNTAIN_ALPINE"},
    {"station_id": "STN_KEN_MOMBASA", "name": "Mombasa", "lat": -4.0435, "lon": 39.6682, "elevation": 17.0, "country": "Kenya", "continent": "Africa", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_ZAF_JOHANNESBURG", "name": "Johannesburg", "lat": -26.2041, "lon": 28.0473, "elevation": 1753.0, "country": "South Africa", "continent": "Africa", "climate_category": "TEMPERATE", "geographic_category": "INLAND"},
    {"station_id": "STN_ZAF_CAPETOWN", "name": "Cape Town", "lat": -33.9249, "lon": 18.4241, "elevation": 12.0, "country": "South Africa", "continent": "Africa", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_ZAF_DURBAN", "name": "Durban", "lat": -29.8587, "lon": 31.0218, "elevation": 8.0, "country": "South Africa", "continent": "Africa", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_ETH_ADDISABABA", "name": "Addis Ababa", "lat": 9.0320, "lon": 38.7469, "elevation": 2355.0, "country": "Ethiopia", "continent": "Africa", "climate_category": "POLAR_ALPINE", "geographic_category": "MOUNTAIN_ALPINE"},
    {"station_id": "STN_MAR_CASABLANCA", "name": "Casablanca", "lat": 33.5731, "lon": -7.5898, "elevation": 27.0, "country": "Morocco", "continent": "Africa", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_MAR_MARRAKECH", "name": "Marrakech", "lat": 31.6295, "lon": -7.9811, "elevation": 466.0, "country": "Morocco", "continent": "Africa", "climate_category": "ARID", "geographic_category": "INLAND"},
    {"station_id": "STN_SEN_DAKAR", "name": "Dakar", "lat": 14.7167, "lon": -17.4677, "elevation": 22.0, "country": "Senegal", "continent": "Africa", "climate_category": "ARID", "geographic_category": "COASTAL"},
    {"station_id": "STN_GHA_ACCRA", "name": "Accra", "lat": 5.6037, "lon": -0.1870, "elevation": 61.0, "country": "Ghana", "continent": "Africa", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_COD_KINSHASA", "name": "Kinshasa", "lat": -4.4419, "lon": 15.2663, "elevation": 240.0, "country": "DR Congo", "continent": "Africa", "climate_category": "TROPICAL", "geographic_category": "INLAND"},
    {"station_id": "STN_AGO_LUANDA", "name": "Luanda", "lat": -8.8390, "lon": 13.2894, "elevation": 6.0, "country": "Angola", "continent": "Africa", "climate_category": "ARID", "geographic_category": "COASTAL"},
    {"station_id": "STN_TZA_DARESSALAAM", "name": "Dar es Salaam", "lat": -6.7924, "lon": 39.2083, "elevation": 12.0, "country": "Tanzania", "continent": "Africa", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_DZA_ALGIERS", "name": "Algiers", "lat": 36.7538, "lon": 3.0588, "elevation": 10.0, "country": "Algeria", "continent": "Africa", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_TUN_TUNIS", "name": "Tunis", "lat": 36.8065, "lon": 10.1815, "elevation": 4.0, "country": "Tunisia", "continent": "Africa", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_SDN_KHARTOUM", "name": "Khartoum", "lat": 15.5007, "lon": 32.5599, "elevation": 381.0, "country": "Sudan", "continent": "Africa", "climate_category": "ARID", "geographic_category": "DESERT_ARID"},
    {"station_id": "STN_NAM_WINDHOEK", "name": "Windhoek", "lat": -22.5609, "lon": 17.0658, "elevation": 1650.0, "country": "Namibia", "continent": "Africa", "climate_category": "ARID", "geographic_category": "DESERT_ARID"},
    {"station_id": "STN_MDG_ANTANANARIVO", "name": "Antananarivo", "lat": -18.8792, "lon": 47.5079, "elevation": 1280.0, "country": "Madagascar", "continent": "Africa", "climate_category": "TEMPERATE", "geographic_category": "ISLAND"},
    {"station_id": "STN_RWA_KIGALI", "name": "Kigali", "lat": -1.9706, "lon": 30.1044, "elevation": 1567.0, "country": "Rwanda", "continent": "Africa", "climate_category": "TEMPERATE", "geographic_category": "MOUNTAIN_ALPINE"},
    {"station_id": "STN_UGA_KAMPALA", "name": "Kampala", "lat": 0.3476, "lon": 32.5825, "elevation": 1190.0, "country": "Uganda", "continent": "Africa", "climate_category": "TROPICAL", "geographic_category": "INLAND"},

    # =========================================================================
    # 6. OCEANIA (15 Stations)
    # =========================================================================
    {"station_id": "STN_AUS_SYDNEY", "name": "Sydney", "lat": -33.8688, "lon": 151.2093, "elevation": 19.0, "country": "Australia", "continent": "Oceania", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_AUS_MELBOURNE", "name": "Melbourne", "lat": -37.8136, "lon": 144.9631, "elevation": 31.0, "country": "Australia", "continent": "Oceania", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_AUS_BRISBANE", "name": "Brisbane", "lat": -27.4698, "lon": 153.0251, "elevation": 28.0, "country": "Australia", "continent": "Oceania", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_AUS_PERTH", "name": "Perth", "lat": -31.9505, "lon": 115.8605, "elevation": 20.0, "country": "Australia", "continent": "Oceania", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_AUS_ADELAIDE", "name": "Adelaide", "lat": -34.9285, "lon": 138.6007, "elevation": 50.0, "country": "Australia", "continent": "Oceania", "climate_category": "TEMPERATE", "geographic_category": "COASTAL"},
    {"station_id": "STN_AUS_DARWIN", "name": "Darwin", "lat": -12.4634, "lon": 130.8456, "elevation": 30.0, "country": "Australia", "continent": "Oceania", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_AUS_ALICESPRINGS", "name": "Alice Springs", "lat": -23.6980, "lon": 133.8807, "elevation": 545.0, "country": "Australia", "continent": "Oceania", "climate_category": "ARID", "geographic_category": "DESERT_ARID"},
    {"station_id": "STN_AUS_HOBART", "name": "Hobart", "lat": -42.8821, "lon": 147.3272, "elevation": 5.0, "country": "Australia", "continent": "Oceania", "climate_category": "TEMPERATE", "geographic_category": "ISLAND"},
    {"station_id": "STN_AUS_CAIRNS", "name": "Cairns", "lat": -16.9186, "lon": 145.7781, "elevation": 8.0, "country": "Australia", "continent": "Oceania", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_NZL_AUCKLAND", "name": "Auckland", "lat": -36.8485, "lon": 174.7633, "elevation": 20.0, "country": "New Zealand", "continent": "Oceania", "climate_category": "TEMPERATE", "geographic_category": "ISLAND"},
    {"station_id": "STN_NZL_WELLINGTON", "name": "Wellington", "lat": -41.2865, "lon": 174.7762, "elevation": 15.0, "country": "New Zealand", "continent": "Oceania", "climate_category": "TEMPERATE", "geographic_category": "ISLAND"},
    {"station_id": "STN_NZL_CHRISTCHURCH", "name": "Christchurch", "lat": -43.5321, "lon": 172.6362, "elevation": 20.0, "country": "New Zealand", "continent": "Oceania", "climate_category": "TEMPERATE", "geographic_category": "ISLAND"},
    {"station_id": "STN_FJI_SUVA", "name": "Suva", "lat": -18.1416, "lon": 178.4419, "elevation": 10.0, "country": "Fiji", "continent": "Oceania", "climate_category": "TROPICAL", "geographic_category": "ISLAND"},
    {"station_id": "STN_PNG_PORTMORESBY", "name": "Port Moresby", "lat": -9.4438, "lon": 147.1803, "elevation": 30.0, "country": "Papua New Guinea", "continent": "Oceania", "climate_category": "TROPICAL", "geographic_category": "COASTAL"},
    {"station_id": "STN_NCL_NOUMEA", "name": "Noumea", "lat": -22.2758, "lon": 166.4580, "elevation": 15.0, "country": "New Caledonia", "continent": "Oceania", "climate_category": "TROPICAL", "geographic_category": "ISLAND"}
]


def validate_and_save():
    print(f"Validating {len(STATIONS)} stations...")
    assert len(STATIONS) == 200, f"Expected 200 stations, got {len(STATIONS)}"

    ids = set()
    continents = {}
    regimes = {}
    geo_types = {}
    countries = set()

    for s in STATIONS:
        sid = s["station_id"]
        assert sid not in ids, f"Duplicate station_id: {sid}"
        ids.add(sid)

        # Coordinate checks
        assert -90.0 <= s["lat"] <= 90.0, f"Invalid latitude: {s['lat']} in {sid}"
        assert -180.0 <= s["lon"] <= 180.0, f"Invalid longitude: {s['lon']} in {sid}"

        c = s["continent"]
        continents[c] = continents.get(c, 0) + 1

        r = s["climate_category"]
        regimes[r] = regimes.get(r, 0) + 1

        g = s["geographic_category"]
        geo_types[g] = geo_types.get(g, 0) + 1

        countries.add(s["country"])

    print(f"\n[+] Total Valid Stations: {len(STATIONS)}")
    print(f"[+] Total Distinct Countries: {len(countries)}")
    print("\n[+] Breakdown by Continent:")
    for c, count in sorted(continents.items()):
        print(f"    - {c:15s}: {count:2d} stations")

    print("\n[+] Breakdown by Climate Regime:")
    for r, count in sorted(regimes.items()):
        print(f"    - {r:15s}: {count:2d} stations")

    print("\n[+] Breakdown by Geographic Category:")
    for g, count in sorted(geo_types.items()):
        print(f"    - {g:15s}: {count:2d} stations")

    os.makedirs("data_pipeline/config", exist_ok=True)
    out_file = "data_pipeline/config/stations_global_200.json"
    with open(out_file, "w") as f:
        json.dump(STATIONS, f, indent=2)

    print(f"\n[+] Saved verified station catalog to: {out_file}")


if __name__ == "__main__":
    validate_and_save()
