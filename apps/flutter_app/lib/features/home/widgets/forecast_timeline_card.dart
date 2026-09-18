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
        Padding(
          padding: const EdgeInsets.only(left: 2, bottom: 8),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'FORECAST TIMELINE (DAYS 1–30)',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textDim,
                  letterSpacing: 0.05,
                ),
              ),
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppColors.green.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: const Text(
                      'D1–7 Validated',
                      style: TextStyle(fontSize: 8.5, fontWeight: FontWeight.w700, color: AppColors.green),
                    ),
                  ),
                  const SizedBox(width: 4),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppColors.orange.withOpacity(0.12),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: const Text(
                      'D8–30 Extended',
                      style: TextStyle(fontSize: 8.5, fontWeight: FontWeight.w700, color: AppColors.orange),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        SizedBox(
          height: 106,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: AppConstants.operationalLeadHours.length,
            separatorBuilder: (_, __) => const SizedBox(width: 8),
            itemBuilder: (context, index) {
              final hours = AppConstants.operationalLeadHours[index];
              final dayNum = (hours / 24).round();
              final isSelected = hours == selectedHours;
              final isExtended = AppConstants.isExtendedRange(hours);
              final dayLabel = 'Day $dayNum';

              // Find matching horizon data if available from operational feed
              ForecastHorizon? matching;
              if (horizons.isNotEmpty) {
                matching = horizons.firstWhere(
                  (h) => (h.leadHours - hours).abs() <= 12,
                  orElse: () => horizons.first,
                );
              }

              final precipMm = matching?.precipitation ?? 0.0;
              final activeColor = isExtended ? AppColors.orange : AppColors.green;

              return InkWell(
                onTap: () {
                  ref.read(selectedLeadHoursProvider.notifier).state = hours;
                },
                borderRadius: BorderRadius.circular(14),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  width: 80,
                  padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 6),
                  decoration: BoxDecoration(
                    color: isSelected
                        ? activeColor.withOpacity(0.14)
                        : AppColors.card2,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(
                      color: isSelected
                          ? activeColor
                          : (isExtended ? AppColors.orange.withOpacity(0.25) : AppColors.stroke),
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
                              color: isSelected ? activeColor : AppColors.text,
                            ),
                          ),
                          const SizedBox(height: 1),
                          Text(
                            '${hours}h',
                            style: TextStyle(
                              fontSize: 9.5,
                              color: isSelected ? activeColor.withOpacity(0.8) : AppColors.textFaint,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                      Text(
                        '${precipMm.toStringAsFixed(1)}mm',
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w800,
                          color: AppColors.text,
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                        decoration: BoxDecoration(
                          color: isExtended
                              ? AppColors.orange.withOpacity(0.18)
                              : AppColors.green.withOpacity(0.18),
                          borderRadius: BorderRadius.circular(5),
                        ),
                        child: Text(
                          isExtended ? 'EXTENDED' : 'VALIDATED',
                          style: TextStyle(
                            fontSize: 7.5,
                            fontWeight: FontWeight.w800,
                            color: isExtended ? AppColors.orange : AppColors.green,
                            letterSpacing: 0.02,
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
