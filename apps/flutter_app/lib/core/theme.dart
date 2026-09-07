import 'package:flutter/material.dart';
import 'constants.dart';

class AppTheme {
  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: AppColors.bg,
      fontFamily: 'Segoe UI',
      colorScheme: const ColorScheme.dark(
        primary: AppColors.green,
        secondary: AppColors.greenDeep,
        surface: AppColors.card,
        error: AppColors.red,
        onPrimary: AppColors.bgDark,
        onSurface: AppColors.text,
      ),
      cardTheme: CardThemeData(
        color: AppColors.card,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: AppColors.stroke, width: 1),
        ),
        margin: EdgeInsets.zero,
      ),
      dividerTheme: const DividerThemeData(
        color: AppColors.stroke,
        thickness: 1,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: AppColors.bgDark,
        foregroundColor: AppColors.text,
        elevation: 0,
        centerTitle: false,
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: AppColors.bgDark,
        selectedItemColor: AppColors.green,
        unselectedItemColor: AppColors.textFaint,
        selectedLabelStyle: TextStyle(
          fontSize: 9,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.04,
        ),
        unselectedLabelStyle: TextStyle(
          fontSize: 9,
          fontWeight: FontWeight.w600,
        ),
        type: BottomNavigationBarType.fixed,
        elevation: 8,
      ),
    );
  }

  // Card styles matching mockup CSS
  static BoxDecoration get cardDecoration => BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.stroke, width: 1),
      );

  static BoxDecoration get card2Decoration => BoxDecoration(
        color: AppColors.card2,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.stroke, width: 1),
      );

  static BoxDecoration get cardGlowDecoration => BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.strokeStrong, width: 1),
        gradient: const LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [
            Color(0x148CFF6E), // rgba(140,255,110,0.08)
            Color(0x058CFF6E), // rgba(140,255,110,0.02)
          ],
        ),
      );

  static BoxDecoration get screenBackgroundDecoration => const BoxDecoration(
        gradient: RadialGradient(
          center: Alignment(-0.6, -1.0),
          radius: 1.2,
          colors: [
            AppColors.bgGradStart,
            AppColors.bgGradEnd,
          ],
          stops: [0.0, 0.6],
        ),
      );
}
