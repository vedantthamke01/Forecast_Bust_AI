import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:forecast_bust_detection/core/constants.dart';
import 'package:forecast_bust_detection/screens/home_screen.dart';
import 'package:forecast_bust_detection/screens/forecast_screen.dart';
import 'package:forecast_bust_detection/screens/risk_map_screen.dart';
import 'package:forecast_bust_detection/screens/historical_screen.dart';
import 'package:forecast_bust_detection/screens/settings_screen.dart';

void main() {
  runApp(const ProviderScope(child: ForecastBustApp()));
}

class ForecastBustApp extends StatelessWidget {
  const ForecastBustApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'NCMRWF Forecast Bust Detection',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        brightness: Brightness.dark,
        scaffoldBackgroundColor: AppConstants.bgDark,
        colorScheme: const ColorScheme.dark(
          primary: AppConstants.accentBlue,
          surface: AppConstants.cardDark,
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF131D31),
          elevation: 0,
        ),
      ),
      home: const MainNavigationScaffold(),
    );
  }
}

class MainNavigationScaffold extends StatefulWidget {
  const MainNavigationScaffold({super.key});

  @override
  State<MainNavigationScaffold> createState() => _MainNavigationScaffoldState();
}

class _MainNavigationScaffoldState extends State<MainNavigationScaffold> {
  int _currentIndex = 0;

  final List<Widget> _screens = const [
    HomeScreen(),
    ForecastScreen(),
    RiskMapScreen(),
    HistoricalScreen(),
    SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        backgroundColor: const Color(0xFF131D31),
        indicatorColor: AppConstants.accentBlue.withOpacity(0.2),
        onDestinationSelected: (idx) {
          setState(() {
            _currentIndex = idx;
          });
        },
        destinations: const [
          NavigationDestination(icon: Icon(Icons.dashboard_outlined), selectedIcon: Icon(Icons.dashboard), label: 'Dashboard'),
          NavigationDestination(icon: Icon(Icons.timeline_outlined), selectedIcon: Icon(Icons.timeline), label: '10-Day NWP'),
          NavigationDestination(icon: Icon(Icons.map_outlined), selectedIcon: Icon(Icons.map), label: 'Risk Map'),
          NavigationDestination(icon: Icon(Icons.verified_outlined), selectedIcon: Icon(Icons.verified), label: 'Verification'),
          NavigationDestination(icon: Icon(Icons.settings_outlined), selectedIcon: Icon(Icons.settings), label: 'Settings'),
        ],
      ),
    );
  }
}
