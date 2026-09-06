import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:forecast_bust_detection/core/constants.dart';
import 'package:forecast_bust_detection/providers/weather_provider.dart';

class ForecastScreen extends ConsumerWidget {
  const ForecastScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final forecastsAsync = ref.watch(forecastHorizonsProvider);
    final location = ref.watch(selectedLocationProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text('10-Day NWP Forecast (${location.name})'),
      ),
      body: forecastsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Error: $err')),
        data: (horizons) {
          if (horizons.isEmpty) {
            return const Center(child: Text('No forecast horizons available.'));
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: horizons.length,
            itemBuilder: (ctx, idx) {
              final h = horizons[idx];
              final dayNum = (h.leadHours / 24).floor();

              return Card(
                color: AppConstants.cardDark,
                margin: const EdgeInsets.only(bottom: 12),
                child: Padding(
                  padding: const EdgeInsets.all(14.0),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: AppConstants.accentBlue.withOpacity(0.15),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          'Day $dayNum\n${h.leadHours}h',
                          textAlign: TextAlign.center,
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: AppConstants.accentBlue),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Precipitation: ${h.precipitation?.toStringAsFixed(1) ?? "0.0"} mm',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Temp: ${h.temperature?.toStringAsFixed(1) ?? "--"}°C | Wind: ${h.windSpeed?.toStringAsFixed(1) ?? "--"} m/s',
                              style: const TextStyle(fontSize: 12, color: Colors.grey),
                            ),
                            Text(
                              'Ensemble Spread: ${h.ensembleSpread.toStringAsFixed(2)}σ | MSLP: ${h.pressure?.toStringAsFixed(1) ?? "--"} hPa',
                              style: const TextStyle(fontSize: 11, color: Colors.white60),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
