import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:forecast_bust_detection/core/constants.dart';
import 'package:forecast_bust_detection/providers/weather_provider.dart';

class HistoricalScreen extends ConsumerWidget {
  const HistoricalScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final historyAsync = ref.watch(historicalVerificationProvider);
    final location = ref.watch(selectedLocationProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text('Verification: Forecast vs Reference (${location.name})'),
      ),
      body: historyAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (err, _) => Center(child: Text('Error: $err')),
        data: (records) {
          if (records.isEmpty) {
            return const Center(child: Text('No historical verification records found.'));
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: records.length,
            itemBuilder: (ctx, idx) {
              final r = records[idx];
              final isBust = r.isBust;

              return Card(
                color: AppConstants.cardDark,
                margin: const EdgeInsets.only(bottom: 12),
                shape: RoundedRectangleBorder(
                  side: BorderSide(
                    color: isBust ? AppConstants.riskVeryHigh.withOpacity(0.5) : Colors.transparent,
                    width: 1,
                  ),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(14.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('Day ${(r.leadHours / 24).floor()} (${r.leadHours}h Lead)',
                              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: isBust ? AppConstants.riskVeryHigh.withOpacity(0.2) : AppConstants.riskLow.withOpacity(0.2),
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(
                              isBust ? 'BUST (${r.severity})' : 'VERIFIED',
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                color: isBust ? AppConstants.riskVeryHigh : AppConstants.riskLow,
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          _buildValueItem('Forecasted', '${r.forecastValue.toStringAsFixed(1)} mm'),
                          _buildValueItem('Observed/Ref', '${r.referenceValue.toStringAsFixed(1)} mm'),
                          _buildValueItem('Abs Error', '${r.absoluteError.toStringAsFixed(1)} mm', highlight: isBust),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Threshold Strategy: ${r.thresholdMethod}',
                        style: const TextStyle(fontSize: 10, color: Colors.grey),
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

  Widget _buildValueItem(String label, String value, {bool highlight = false}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
        Text(
          value,
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.bold,
            color: highlight ? AppConstants.riskHigh : Colors.white,
          ),
        ),
      ],
    );
  }
}
