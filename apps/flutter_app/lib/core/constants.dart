import 'package:flutter/material.dart';

class AppColors {
  // Primary Dark Backgrounds (Mockup accurate)
  static const Color bg = Color(0xFF06110C);
  static const Color bgDark = Color(0xFF040806);
  static const Color bgGradStart = Color(0xFF0F2318);
  static const Color bgGradEnd = Color(0xFF06110C);

  // Cards
  static const Color card = Color(0xFF0E1A14);
  static const Color card2 = Color(0xFF12211A);
  static const Color cardGlowBg = Color(0x148CFF6E); // rgba(140,255,110,0.08)

  // Strokes & Borders
  static const Color stroke = Color(0x0FFFFFFF); // rgba(255,255,255,0.06)
  static const Color strokeStrong = Color(0x408CFF6E); // rgba(140,255,110,0.25)
  static const Color strokeCard = Color(0x1A8CFF6E);

  // Typography
  static const Color text = Color(0xFFEAF5EE);
  static const Color textDim = Color(0xFF8FA89B);
  static const Color textFaint = Color(0xFF5F7669);

  // Scientific & Risk Colors
  static const Color green = Color(0xFF8CFF6E);
  static const Color greenDeep = Color(0xFF4FAE3D);
  static const Color amber = Color(0xFFFFCF5C);
  static const Color orange = Color(0xFFFF9A4D);
  static const Color red = Color(0xFFFF5C6C);

  // Severity color lookup
  static Color forRiskLevel(String? level) {
    switch ((level ?? '').toUpperCase()) {
      case 'LOW':
        return green;
      case 'MODERATE':
      case 'MOD':
        return amber;
      case 'HIGH':
        return orange;
      case 'VERY HIGH':
      case 'VERY_HIGH':
      case 'V.HIGH':
        return red;
      default:
        return green;
    }
  }

  static Color forProbability(double prob) {
    if (prob < 0.25) return green;
    if (prob < 0.50) return amber;
    if (prob < 0.75) return orange;
    return red;
  }
}

class AppConstants {
  static const String appName = 'Forecast Bust AI';
  static const String appSubtitle = 'Reliability Intelligence · Days 1–30';
  static const String appVersion = '1.0.0';
  static const String productionBackendUrl = 'https://forecast-bust-api.onrender.com';

  // Lead Hours Definition for Full 30-Day Operational Horizon
  // Day 1 = 24h, Day 2 = 48h, ... Day 7 = 168h (Scientifically Validated)
  // Day 8 = 192h, ... Day 30 = 720h (UNVALIDATED_EXTENDED_RANGE / Exploratory)
  static const List<int> operationalLeadHours = [
    24,  // Day 1
    48,  // Day 2
    72,  // Day 3
    96,  // Day 4
    120, // Day 5
    144, // Day 6
    168, // Day 7
    192, // Day 8 (Extended)
    216, // Day 9 (Extended)
    240, // Day 10 (Extended)
    264, // Day 11
    288, // Day 12
    312, // Day 13
    336, // Day 14
    360, // Day 15
    384, // Day 16
    408, // Day 17
    432, // Day 18
    456, // Day 19
    480, // Day 20
    504, // Day 21
    528, // Day 22
    552, // Day 23
    576, // Day 24
    600, // Day 25
    624, // Day 26
    648, // Day 27
    672, // Day 28
    696, // Day 29
    720, // Day 30
  ];

  static bool isExtendedRange(int hours) => hours > 168;

  static String dayLabelForHours(int hours) {
    switch (hours) {
      case 24:
        return 'Day 1';
      case 48:
        return 'Day 2';
      case 72:
        return 'Day 3';
      case 96:
        return 'Day 4';
      case 120:
        return 'Day 5';
      case 144:
        return 'Day 6';
      case 168:
        return 'Day 7';
      default:
        return 'Day ${(hours / 24).round()}';
    }
  }

  // Format latitude with N/S hemisphere indicator
  static String formatLat(double lat, [int precision = 2]) {
    final dir = lat >= 0 ? 'N' : 'S';
    return '${lat.abs().toStringAsFixed(precision)}°$dir';
  }

  // Format longitude with E/W hemisphere indicator
  static String formatLon(double lon, [int precision = 2]) {
    final dir = lon >= 0 ? 'E' : 'W';
    return '${lon.abs().toStringAsFixed(precision)}°$dir';
  }

  // Format combined coordinate string
  static String formatCoordinates(double lat, double lon, [int precision = 2]) {
    return '${formatLat(lat, precision)}, ${formatLon(lon, precision)}';
  }

  // Default Synoptic Station (Nagpur, Central India - for demo continuity)
  static const double defaultLat = 21.1458;
  static const double defaultLon = 79.0882;
  static const String defaultCity = 'Nagpur';
  static const String defaultState = 'Maharashtra';
  static const String defaultCountry = 'India';

  // Preset Global Benchmark Synoptic Observatories
  static const List<Map<String, dynamic>> presetCities = [
    {'name': 'Nagpur', 'state': 'Maharashtra', 'country': 'India', 'lat': 21.1458, 'lon': 79.0882},
    {'name': 'Tokyo', 'state': 'Tokyo', 'country': 'Japan', 'lat': 35.6762, 'lon': 139.6503},
    {'name': 'London', 'state': 'England', 'country': 'United Kingdom', 'lat': 51.5074, 'lon': -0.1278},
    {'name': 'New York', 'state': 'New York', 'country': 'USA', 'lat': 40.7128, 'lon': -74.0060},
    {'name': 'São Paulo', 'state': 'São Paulo', 'country': 'Brazil', 'lat': -23.5505, 'lon': -46.6333},
    {'name': 'Cape Town', 'state': 'Western Cape', 'country': 'South Africa', 'lat': -33.9249, 'lon': 18.4241},
    {'name': 'Sydney', 'state': 'New South Wales', 'country': 'Australia', 'lat': -33.8688, 'lon': 151.2093},
    {'name': 'New Delhi', 'state': 'Delhi NCR', 'country': 'India', 'lat': 28.6139, 'lon': 77.2090},
    {'name': 'Mumbai', 'state': 'Maharashtra', 'country': 'India', 'lat': 19.0760, 'lon': 72.8777},
    {'name': 'Paris', 'state': 'Île-de-France', 'country': 'France', 'lat': 48.8566, 'lon': 2.3522},
  ];
}
