import 'package:flutter/material.dart';

class AppConstants {
  // Backend API URL (Uses localhost for web/desktop, 10.0.2.2 for Android emulator)
  static const String defaultApiBaseUrl = 'http://localhost:8000';
  
  // Scientific Disclaimer required by NCMRWF
  static const String scientificDisclaimer = 
      'This system estimates the likelihood that a weather forecast may experience a '
      'significant forecast error. It does not replace operational numerical weather '
      'prediction, meteorological agencies, or official warnings issued by IMD or NCMRWF.';

  // Visual Risk Color Tokens
  static const Color riskLow = Color(0xFF10B981);
  static const Color riskModerate = Color(0xFFF59E0B);
  static const Color riskHigh = Color(0xFFF97316);
  static const Color riskVeryHigh = Color(0xFFEF4444);

  // Background Themes
  static const Color bgDark = Color(0xFF0B1120);
  static const Color cardDark = Color(0xFF18233A);
  static const Color accentBlue = Color(0xFF38BDF8);
}
