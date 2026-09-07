import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../core/constants.dart';
import '../../models/verification_models.dart';
import '../../providers/app_providers.dart';

class VerificationScreen extends ConsumerWidget {
  const VerificationScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final historyAsync = ref.watch(historicalVerificationProvider);
    final location = ref.watch(activeLocationProvider);

    return Scaffold(
      backgroundColor: AppColors.bg,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Forecast vs Reference',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w800,
                          color: AppColors.text,
                        ),
                      ),
                      const SizedBox(height: 3),
                      Text(
                        'Verified against ERA5 reanalysis · ${location.name}',
                        style: const TextStyle(
                          fontSize: 12,
                          color: AppColors.textDim,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 14),

              // Stage Flow: STAGE 1 (T0) -> STAGE 2 (T0+tau)
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.card,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.stroke),
                ),
                child: Column(
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                            decoration: BoxDecoration(
                              color: AppColors.card2,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: AppColors.stroke),
                            ),
                            child: Column(
                              children: const [
                                Text(
                                  'STAGE 1',
                                  style: TextStyle(
                                    fontSize: 10.5,
                                    color: AppColors.green,
                                    fontWeight: FontWeight.w800,
                                  ),
                                ),
                                SizedBox(height: 3),
                                Text(
                                  'T₀ Prediction',
                                  style: TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.w700,
                                    color: AppColors.text,
                                  ),
                                ),
                                SizedBox(height: 2),
                                Text(
                                  'Issuance time only',
                                  style: TextStyle(fontSize: 10.5, color: AppColors.textFaint),
                                ),
                              ],
                            ),
                          ),
                        ),
                        const Padding(
                          padding: EdgeInsets.symmetric(horizontal: 8),
                          child: Icon(Icons.arrow_forward, color: AppColors.textFaint, size: 18),
                        ),
                        Expanded(
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                            decoration: BoxDecoration(
                              color: AppColors.card2,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: AppColors.stroke),
                            ),
                            child: Column(
                              children: const [
                                Text(
                                  'STAGE 2',
                                  style: TextStyle(
                                    fontSize: 10.5,
                                    color: AppColors.green,
                                    fontWeight: FontWeight.w800,
                                  ),
                                ),
                                SizedBox(height: 3),
                                Text(
                                  'T₀+τ Verify',
                                  style: TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.w700,
                                    color: AppColors.text,
                                  ),
                                ),
                                SizedBox(height: 2),
                                Text(
                                  'ERA5 Reanalysis',
                                  style: TextStyle(fontSize: 10.5, color: AppColors.textFaint),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    const Text(
                      'Anti-leakage certified: No future reference or error data is ever permitted into T₀ model inference.',
                      style: TextStyle(fontSize: 11, color: AppColors.textDim),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Recent Records Header & Summary
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'RECENT RECORDS',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: AppColors.textDim,
                      letterSpacing: 0.05,
                    ),
                  ),
                  historyAsync.when(
                    data: (hist) => Text(
                      'Bust Rate: ${hist.bustRatePercentage.toStringAsFixed(1)}% (${hist.bustCount}/${hist.sampleSize})',
                      style: const TextStyle(fontSize: 11, color: AppColors.textDim, fontWeight: FontWeight.w600),
                    ),
                    loading: () => const SizedBox.shrink(),
                    error: (_, __) => const SizedBox.shrink(),
                  ),
                ],
              ),
              const SizedBox(height: 10),

              // Records List
              historyAsync.when(
                data: (hist) {
                  final records = hist.records;
                  if (records.isEmpty) {
                    return _buildEmptyState();
                  }

                  return Column(
                    children: records.map((rec) => _buildVerifyCard(rec)).toList(),
                  );
                },
                loading: () => const Center(
                  child: Padding(
                    padding: EdgeInsets.all(24.0),
                    child: CircularProgressIndicator(color: AppColors.green),
                  ),
                ),
                error: (err, _) => Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: AppColors.card,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Center(
                    child: Text(
                      'Verification archive unreachable: $err',
                      style: const TextStyle(color: AppColors.red, fontSize: 12),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 14),

              // Anti-leakage certified banner
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: AppColors.card2,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.stroke),
                ),
                child: Row(
                  children: const [
                    Icon(Icons.shield_outlined, color: AppColors.green, size: 18),
                    SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Anti-leakage certified — predictions generated strictly at T₀',
                        style: TextStyle(fontSize: 11, color: AppColors.textDim, fontWeight: FontWeight.w500),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildVerifyCard(ComparisonRecord rec) {
    final dateStr = DateFormat('MMM dd, HH:mm').format(rec.validTime);
    final isBust = rec.isBust;
    final statusColor = isBust ? AppColors.red : AppColors.green;
    final statusText = isBust ? 'BUST' : 'VERIFIED';

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: AppColors.card2,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.stroke),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // Left: Time & Forecast
          Expanded(
            flex: 4,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  dateStr,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: AppColors.text,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  'Day ${(rec.leadHours / 24).round()} · NWP ${rec.forecastValue.toStringAsFixed(1)}mm',
                  style: const TextStyle(fontSize: 11, color: AppColors.textFaint),
                ),
              ],
            ),
          ),

          // Mid: Error
          Expanded(
            flex: 3,
            child: Column(
              children: [
                Text(
                  '${rec.absoluteError.toStringAsFixed(1)}mm',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w800,
                    color: statusColor,
                  ),
                ),
                const SizedBox(height: 1),
                const Text(
                  'ERROR',
                  style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: AppColors.textFaint),
                ),
              ],
            ),
          ),

          // Right: Status Chip
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
            decoration: BoxDecoration(
              color: statusColor.withOpacity(0.15),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              statusText,
              style: TextStyle(
                fontSize: 10.5,
                fontWeight: FontWeight.w800,
                color: statusColor,
                letterSpacing: 0.04,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.card2,
        borderRadius: BorderRadius.circular(12),
      ),
      child: const Center(
        child: Text(
          'No historical verification records found for this location.',
          style: TextStyle(fontSize: 12, color: AppColors.textFaint),
        ),
      ),
    );
  }
}
