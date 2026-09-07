import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/constants.dart';
import '../../../models/weather_models.dart';
import '../../../providers/app_providers.dart';

class ForecastTimelineCard extends ConsumerWidget {
  final List<ForecastHorizon> horizons;

  const ForecastTimelineCard({super.key, required this.horizons});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedHours = ref.watch(selectedLeadHoursProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.only(left: 2, bottom: 8),
          child: Text(
            'FORECAST TIMELINE',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: AppColors.textDim,
              letterSpacing: 0.05,
            ),
          ),
        ),
        SizedBox(
          height: 98,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: AppConstants.operationalLeadHours.length,
            separatorBuilder: (_, __) => const SizedBox(width: 8),
            itemBuilder: (context, index) {
              final hours = AppConstants.operationalLeadHours[index];
              final isSelected = hours == selectedHours;
              final dayLabel = AppConstants.dayLabelForHours(hours);

              // Find matching horizon data if available
              ForecastHorizon? matching;
              if (horizons.isNotEmpty) {
                matching = horizons.firstWhere(
                  (h) => (h.leadHours - hours).abs() <= 12,
                  orElse: () => horizons.first,
                );
              }

              final precipMm = matching?.precipitation ?? 0.0;

              // Lead time baseline reliability estimation
              // Hours > 168 (Days 8-10) naturally have wider uncertainty
              final estimatedRel = hours <= 72
                  ? 98
                  : hours <= 96
                      ? 96
                      : hours <= 120
                          ? 93
                          : hours <= 168
                              ? 90
                              : 85;

              final relColor = estimatedRel >= 95
                  ? AppColors.green
                  : estimatedRel >= 90
                      ? AppColors.amber
                      : AppColors.orange;

              return InkWell(
                onTap: () {
                  ref.read(selectedLeadHoursProvider.notifier).state = hours;
                },
                borderRadius: BorderRadius.circular(14),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  width: 74,
                  padding: const EdgeInsets.symmetric(vertical: 9, horizontal: 6),
                  decoration: BoxDecoration(
                    color: isSelected ? AppColors.green.withOpacity(0.12) : AppColors.card2,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(
                      color: isSelected ? AppColors.green : AppColors.stroke,
                      width: isSelected ? 1.5 : 1.0,
                    ),
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        children: [
                          Text(
                            dayLabel,
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                              color: isSelected ? AppColors.green : AppColors.text,
                            ),
                          ),
                          const SizedBox(height: 1),
                          Text(
                            '${hours}h',
                            style: const TextStyle(
                              fontSize: 10,
                              color: AppColors.textFaint,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                      Text(
                        '${precipMm.toStringAsFixed(1)}mm',
                        style: const TextStyle(
                          fontSize: 12.5,
                          fontWeight: FontWeight.w800,
                          color: AppColors.text,
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                        decoration: BoxDecoration(
                          color: relColor.withOpacity(0.18),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          '$estimatedRel% REL',
                          style: TextStyle(
                            fontSize: 8.5,
                            fontWeight: FontWeight.w800,
                            color: relColor,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}
