import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'core/constants.dart';
import 'core/theme.dart';
import 'features/advanced/advanced_screen.dart';
import 'features/home/home_screen.dart';
import 'features/risk_map/risk_map_screen.dart';
import 'features/verification/verification_screen.dart';
import 'providers/app_providers.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // True full-screen native edge-to-edge Android system UI styling
  SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
      statusBarBrightness: Brightness.dark,
      systemNavigationBarColor: Colors.transparent,
      systemNavigationBarDividerColor: Colors.transparent,
      systemNavigationBarIconBrightness: Brightness.light,
    ),
  );

  runApp(const ProviderScope(child: ForecastBustApp()));
}

class ForecastBustApp extends StatelessWidget {
  const ForecastBustApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: AppConstants.appName,
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: const MainNavigationScaffold(),
    );
  }
}

class MainNavigationScaffold extends ConsumerStatefulWidget {
  const MainNavigationScaffold({super.key});

  @override
  ConsumerState<MainNavigationScaffold> createState() => _MainNavigationScaffoldState();
}

class _MainNavigationScaffoldState extends ConsumerState<MainNavigationScaffold> {
  int _currentIndex = 0;

  final List<Widget> _screens = const [
    HomeScreen(),
    RiskMapScreen(),
    VerificationScreen(),
    AdvancedScreen(),
  ];

  @override
  void initState() {
    super.initState();
    _initAppLocation();
  }

  Future<void> _initAppLocation() async {
    try {
      final locService = ref.read(locationServiceProvider);
      final initialLoc = await locService.getInitialLocation();
      if (mounted) {
        ref.read(activeLocationProvider.notifier).state = initialLoc;
      }
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: _currentIndex == 0,
      onPopInvokedWithResult: (didPop, result) {
        if (!didPop && _currentIndex != 0) {
          setState(() {
            _currentIndex = 0;
          });
        }
      },
      child: Scaffold(
        backgroundColor: AppColors.bg,
        body: Container(
          decoration: AppTheme.screenBackgroundDecoration,
          child: IndexedStack(
            index: _currentIndex,
            children: _screens,
          ),
        ),
        bottomNavigationBar: Container(
          decoration: const BoxDecoration(
            color: AppColors.bgDark,
            border: Border(
              top: BorderSide(color: AppColors.stroke, width: 1),
            ),
          ),
          child: SafeArea(
            top: false,
            child: BottomNavigationBar(
              currentIndex: _currentIndex,
              backgroundColor: Colors.transparent,
              elevation: 0,
              selectedItemColor: AppColors.green,
              unselectedItemColor: AppColors.textFaint,
              selectedFontSize: 11.0,
              unselectedFontSize: 10.0,
              type: BottomNavigationBarType.fixed,
              onTap: (index) {
                setState(() {
                  _currentIndex = index;
                });
              },
              items: const [
                BottomNavigationBarItem(
                  icon: Icon(Icons.home_outlined, size: 22),
                  activeIcon: Icon(Icons.home, size: 22),
                  label: 'Home',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.map_outlined, size: 22),
                  activeIcon: Icon(Icons.map, size: 22),
                  label: 'Risk Map',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.fact_check_outlined, size: 22),
                  activeIcon: Icon(Icons.fact_check, size: 22),
                  label: 'Verify',
                ),
                BottomNavigationBarItem(
                  icon: Icon(Icons.science_outlined, size: 22),
                  activeIcon: Icon(Icons.science, size: 22),
                  label: 'Advanced',
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
