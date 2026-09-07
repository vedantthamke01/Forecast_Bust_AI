import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants.dart';
import '../../providers/app_providers.dart';
import 'widgets/active_location_card.dart';
import 'widgets/current_weather_card.dart';
import 'widgets/forecast_timeline_card.dart';
import 'widgets/nwp_reliability_card.dart';
import '../connection/connection_screen.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final location = ref.watch(activeLocationProvider);
    final weatherAsync = ref.watch(currentWeatherProvider);
    final forecastAsync = ref.watch(forecastTimelineProvider);
    final riskAsync = ref.watch(riskPredictionProvider);

    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        child: RefreshIndicator(
          color: AppColors.green,
          backgroundColor: AppColors.card,
          onRefresh: () async {
            ref.invalidate(currentWeatherProvider);
            ref.invalidate(forecastTimelineProvider);
            ref.invalidate(riskPredictionProvider);
          },
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Top App Header
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: const [
                        Text(
                          AppConstants.appName,
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.w800,
                            color: AppColors.text,
                            letterSpacing: -0.3,
                          ),
                        ),
                        SizedBox(height: 3),
                        Text(
                          AppConstants.appSubtitle,
                          style: TextStyle(
                            fontSize: 12,
                            color: AppColors.textDim,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                      decoration: BoxDecoration(
                        color: AppColors.green.withOpacity(0.12),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: AppColors.strokeStrong),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: const [
                          Icon(Icons.circle, color: AppColors.green, size: 6),
                          SizedBox(width: 5),
                          Text(
                            'LIVE',
                            style: TextStyle(
                              fontSize: 10.5,
                              fontWeight: FontWeight.w700,
                              color: AppColors.green,
                              letterSpacing: 0.05,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),

                // Active Location Card
                ActiveLocationCard(location: location),
                const SizedBox(height: 12),

                // Current Weather Card
                weatherAsync.when(
                  data: (weather) => CurrentWeatherCard(weather: weather),
                  loading: () => _buildShimmerCard(height: 130, title: 'CURRENT WEATHER'),
                  error: (err, _) => _buildErrorCard(
                    context: context,
                    title: 'CURRENT WEATHER',
                    message: 'Weather service offline or unreachable.',
                    onRetry: () => ref.refresh(currentWeatherProvider),
                  ),
                ),
                const SizedBox(height: 12),

                // Forecast Timeline
                forecastAsync.when(
                  data: (horizons) => ForecastTimelineCard(horizons: horizons),
                  loading: () => _buildShimmerCard(height: 90, title: 'FORECAST TIMELINE'),
                  error: (err, _) => const SizedBox.shrink(),
                ),
                const SizedBox(height: 12),

                // Split NWP + Bust Probability Cards
                riskAsync.when(
                  data: (risk) {
                    final horizons = forecastAsync.valueOrNull ?? [];
                    final selectedHours = ref.watch(selectedLeadHoursProvider);
                    final matchingHorizon = horizons.isNotEmpty
                        ? horizons.firstWhere(
                            (h) => (h.leadHours - selectedHours).abs() <= 12,
                            orElse: () => horizons.first,
                          )
                        : null;
                    return NwpReliabilityCard(
                      prediction: risk,
                      horizon: matchingHorizon,
                    );
                  },
                  loading: () => _buildShimmerCard(height: 110, title: 'BUST PROBABILITY'),
                  error: (err, _) => _buildErrorCard(
                    context: context,
                    title: 'RELIABILITY PREDICTION',
                    message: 'Inference engine unreachable. Check server connection.',
                    onRetry: () => ref.refresh(riskPredictionProvider),
                  ),
                ),
                const SizedBox(height: 16),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildShimmerCard({required double height, required String title}) {
    return Container(
      height: height,
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.stroke),
      ),
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              fontSize: 9,
              fontWeight: FontWeight.w700,
              color: AppColors.textFaint,
            ),
          ),
          const Expanded(
            child: Center(
              child: SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: AppColors.green,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildErrorCard({
    required BuildContext context,
    required String title,
    required String message,
    required VoidCallback onRetry,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.red.withOpacity(0.3)),
      ),
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              fontSize: 9,
              fontWeight: FontWeight.w700,
              color: AppColors.textFaint,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              const Icon(Icons.cloud_off, color: AppColors.red, size: 18),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  message,
                  style: const TextStyle(fontSize: 11, color: AppColors.textDim),
                ),
              ),
              InkWell(
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const ConnectionScreen()),
                  );
                },
                borderRadius: BorderRadius.circular(8),
                child: Container(
                  margin: const EdgeInsets.only(right: 6),
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.green.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Text(
                    'Settings',
                    style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: AppColors.green),
                  ),
                ),
              ),
              InkWell(
                onTap: onRetry,
                borderRadius: BorderRadius.circular(8),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.red.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Text(
                    'Retry',
                    style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: AppColors.red),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
