import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants.dart';
import '../../../models/risk_models.dart';
import '../../../models/weather_models.dart';
import '../../../providers/app_providers.dart';

class StationDetailDialog extends ConsumerWidget {
  final StationRiskPoint station;

  const StationDetailDialog({super.key, required this.station});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final riskColor = AppColors.forRiskLevel(station.riskLevel);

    return Dialog(
      backgroundColor: AppColors.card,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(18),
        side: BorderSide(color: riskColor.withOpacity(0.4), width: 1),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    station.stationName,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                      color: AppColors.text,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: riskColor.withOpacity(0.18),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    station.riskBadge,
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w800,
                      color: riskColor,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              '${station.latitude.toStringAsFixed(2)}°N, ${station.longitude.toStringAsFixed(2)}°E · Synoptic Observatory',
              style: const TextStyle(fontSize: 10, color: AppColors.textDim),
            ),
            const SizedBox(height: 14),

            // Metrics row
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.card2,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.stroke),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'P(BUST)',
                          style: TextStyle(fontSize: 8, color: AppColors.textFaint, fontWeight: FontWeight.w700),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          '${(station.bustProbability * 100).toStringAsFixed(1)}%',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w800,
                            color: riskColor,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Container(width: 1, height: 30, color: AppColors.stroke),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'RELIABILITY',
                          style: TextStyle(fontSize: 8, color: AppColors.textFaint, fontWeight: FontWeight.w700),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          '${(station.reliabilityScore * 100).toStringAsFixed(1)}%',
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w800,
                            color: AppColors.green,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),

            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('Close', style: TextStyle(color: AppColors.textDim)),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.green,
                    foregroundColor: AppColors.bgDark,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  onPressed: () {
                    // Set as active location and switch to Home
                    final loc = LocationModel(
                      name: station.stationName,
                      state: 'India',
                      latitude: station.latitude,
                      longitude: station.longitude,
                    );
                    ref.read(activeLocationProvider.notifier).state = loc;
                    ref.read(locationServiceProvider).saveLocation(loc);
                    Navigator.of(context).pop();
                  },
                  child: const Text(
                    'Set as Active Location',
                    style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
