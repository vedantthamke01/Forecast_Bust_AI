import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:forecast_bust_detection/core/constants.dart';
import 'package:forecast_bust_detection/providers/weather_provider.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final location = ref.watch(selectedLocationProvider);
    final riskAsync = ref.watch(currentRiskProvider);
    final leadHours = ref.watch(selectedLeadHoursProvider);

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '${location.name}, ${location.state ?? "India"}',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            Text(
              'Lat ${location.latitude.toStringAsFixed(2)}°, Lon ${location.longitude.toStringAsFixed(2)}°',
              style: const TextStyle(fontSize: 12, color: Colors.grey),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () => _showLocationSearch(context, ref),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(currentRiskProvider);
        },
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Disclaimer Notice
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppConstants.cardDark,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.blueGrey.withOpacity(0.3)),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.info_outline, color: AppConstants.accentBlue, size: 20),
                    SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Reliability layer for medium-range forecasts. Does not replace official IMD/NCMRWF warnings.',
                        style: TextStyle(fontSize: 11, color: Colors.white70),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Horizon Selection Bar
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Horizon: Day ${(leadHours / 24).floor()} ($leadHours Hours)',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                  DropdownButton<int>(
                    value: leadHours,
                    dropdownColor: AppConstants.cardDark,
                    items: [24, 48, 72, 96, 120, 144, 168, 192, 216, 240]
                        .map((h) => DropdownMenuItem(
                              value: h,
                              child: Text('Day ${(h / 24).floor()} (${h}h)'),
                            ))
                        .toList(),
                    onChanged: (val) {
                      if (val != null) {
                        ref.read(selectedLeadHoursProvider.notifier).state = val;
                      }
                    },
                  ),
                ],
              ),
              const SizedBox(height: 12),

              // Main Risk Assessment Card
              riskAsync.when(
                loading: () => const Center(
                  child: Padding(
                    padding: EdgeInsets.all(32.0),
                    child: CircularProgressIndicator(),
                  ),
                ),
                error: (err, _) => Container(
                  padding: const EdgeInsets.all(16),
                  color: Colors.red.withOpacity(0.1),
                  child: Text('Error loading risk data: $err'),
                ),
                data: (risk) {
                  if (risk == null) return const Text('Risk data unavailable.');

                  Color riskColor = AppConstants.riskLow;
                  if (risk.riskLevel == 'MODERATE') riskColor = AppConstants.riskModerate;
                  if (risk.riskLevel == 'HIGH') riskColor = AppConstants.riskHigh;
                  if (risk.riskLevel == 'VERY HIGH') riskColor = AppConstants.riskVeryHigh;

                  return Column(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(20),
                        decoration: BoxDecoration(
                          color: AppConstants.cardDark,
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: riskColor.withOpacity(0.4)),
                        ),
                        child: Column(
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text('Forecast Bust Risk',
                                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: riskColor.withOpacity(0.2),
                                    borderRadius: BorderRadius.circular(6),
                                    border: Border.all(color: riskColor),
                                  ),
                                  child: Text(
                                    risk.riskBadge,
                                    style: TextStyle(color: riskColor, fontWeight: FontWeight.bold),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 20),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceAround,
                              children: [
                                _buildMetricColumn(
                                  'Bust Probability',
                                  '${(risk.bustProbability * 100).toStringAsFixed(1)}%',
                                  riskColor,
                                ),
                                Container(height: 40, width: 1, color: Colors.grey.withOpacity(0.3)),
                                _buildMetricColumn(
                                  'Reliability Score',
                                  '${(risk.reliabilityScore * 100).toStringAsFixed(1)}%',
                                  AppConstants.accentBlue,
                                ),
                              ],
                            ),
                            const SizedBox(height: 16),
                            if (risk.summaryText != null)
                              Container(
                                padding: const EdgeInsets.all(10),
                                decoration: BoxDecoration(
                                  color: Colors.black26,
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Text(
                                  risk.summaryText!,
                                  style: const TextStyle(fontSize: 12, color: Colors.white70),
                                  textAlign: TextAlign.center,
                                ),
                              ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 20),

                      // Quick SHAP Factor Insights
                      if (risk.shapFactors.isNotEmpty) ...[
                        const Text(
                          'Key Atmospheric Drivers (TreeSHAP)',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 8),
                        ...risk.shapFactors.take(3).map((factor) {
                          final isAmp = factor.impact == 'AMPLIFIER';
                          return Card(
                            color: AppConstants.cardDark,
                            margin: const EdgeInsets.only(bottom: 8),
                            child: ListTile(
                              leading: Icon(
                                isAmp ? Icons.arrow_upward : Icons.arrow_downward,
                                color: isAmp ? AppConstants.riskVeryHigh : AppConstants.riskLow,
                              ),
                              title: Text(factor.description, style: const TextStyle(fontSize: 13)),
                              trailing: Text(
                                '${isAmp ? "+" : ""}${factor.shapValue.toStringAsFixed(3)}',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: isAmp ? AppConstants.riskHigh : AppConstants.riskLow,
                                ),
                              ),
                            ),
                          );
                        }),
                      ],
                    ],
                  );
                },
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMetricColumn(String label, String value, Color color) {
    return Column(
      children: [
        Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(fontSize: 26, fontWeight: FontWeight.w900, color: color),
        ),
      ],
    );
  }

  void _showLocationSearch(BuildContext context, WidgetRef ref) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppConstants.cardDark,
      isScrollControlled: true,
      builder: (ctx) {
        final controller = TextEditingController();
        return Padding(
          padding: EdgeInsets.only(
            top: 20,
            left: 16,
            right: 16,
            bottom: MediaQuery.of(ctx).viewInsets.bottom + 20,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: controller,
                autofocus: true,
                decoration: InputDecoration(
                  hintText: 'Search city (e.g. Pune, Delhi, Mumbai, Chennai)...',
                  prefixIcon: const Icon(Icons.search),
                  suffixIcon: IconButton(
                    icon: const Icon(Icons.arrow_forward),
                    onPressed: () async {
                      final q = controller.text.trim();
                      if (q.isNotEmpty) {
                        final results = await ref.read(apiClientProvider).searchLocations(q);
                        if (results.isNotEmpty) {
                          ref.read(selectedLocationProvider.notifier).state = results.first;
                          Navigator.pop(ctx);
                        }
                      }
                    },
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
