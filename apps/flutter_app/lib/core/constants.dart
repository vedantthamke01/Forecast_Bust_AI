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
  static const String appSubtitle = 'Reliability Intelligence · Days 3–10';
  static const String appVersion = '1.0.0';
  static const String productionBackendUrl = 'https://forecast-bust-api.onrender.com';

  // Lead Hours Definition
  // Day 3 = 72h, Day 4 = 96h, Day 5 = 120h, Day 6 = 144h, Day 7 = 168h, Day 8 = 192h, Day 9 = 216h, Day 10 = 240h
  static const List<int> operationalLeadHours = [
    24, // Tomorrow
    72, // Day 3
    96, // Day 4
    120, // Day 5
    144, // Day 6
    168, // Day 7
    192, // Day 8
    216, // Day 9
    240, // Day 10
  ];

  static String dayLabelForHours(int hours) {
    switch (hours) {
      case 24:
        return 'Tmrw';
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
      case 192:
        return 'Day 8';
      case 216:
        return 'Day 9';
      case 240:
        return 'Day 10';
      default:
        return 'Day ${(hours / 24).round()}';
    }
  }

  // Default Synoptic Station (Nagpur, Central India)
  static const double defaultLat = 21.1458;
  static const double defaultLon = 79.0882;
  static const String defaultCity = 'Nagpur';
  static const String defaultState = 'Maharashtra';

  // Preset Indian Cities for quick navigation
  static const List<Map<String, dynamic>> presetCities = [
    {'name': 'Nagpur', 'state': 'Maharashtra', 'lat': 21.1458, 'lon': 79.0882},
    {'name': 'New Delhi', 'state': 'Delhi NCR', 'lat': 28.6139, 'lon': 77.2090},
    {'name': 'Pune', 'state': 'Maharashtra', 'lat': 18.5204, 'lon': 73.8567},
    {'name': 'Mumbai', 'state': 'Maharashtra', 'lat': 19.0760, 'lon': 72.8777},
    {'name': 'Kolkata', 'state': 'West Bengal', 'lat': 22.5726, 'lon': 88.3639},
    {'name': 'Bengaluru', 'state': 'Karnataka', 'lat': 12.9716, 'lon': 77.5946},
    {'name': 'Chennai', 'state': 'Tamil Nadu', 'lat': 13.0827, 'lon': 80.2707},
    {'name': 'Bhopal', 'state': 'Madhya Pradesh', 'lat': 23.2599, 'lon': 77.4126},
    {'name': 'Jaipur', 'state': 'Rajasthan', 'lat': 26.9124, 'lon': 75.7873},
    {'name': 'Guwahati', 'state': 'Assam', 'lat': 26.1445, 'lon': 91.7362},
  ];
}
