import 'package:flutter/material.dart';
import '../../../core/constants.dart';
import '../../../models/risk_models.dart';
import '../../../models/weather_models.dart';
import 'shap_bottom_sheet.dart';

class NwpReliabilityCard extends StatelessWidget {
  final RiskPrediction prediction;
  final ForecastHorizon? horizon;

  const NwpReliabilityCard({
    super.key,
    required this.prediction,
    this.horizon,
  });

  @override
  Widget build(BuildContext context) {
    final precip = prediction.forecastValue;
    final temp = horizon?.temperature2m ?? 26.5;
    final wind = horizon?.windSpeed10m ?? 6.8;

    final relScore = prediction.reliabilityScore;
    final isExtended = prediction.isExtendedRange;
    final dayNum = (prediction.leadHours / 24).round();

    // Days 8–30 must NEVER use green validated color
    final riskColor = isExtended
        ? AppColors.orange
        : AppColors.forRiskLevel(prediction.riskLevel);

    return Column(
      children: [
        Row(
          children: [
            // LEFT CARD: NWP Forecast
            Expanded(
              child: Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppColors.card,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.stroke),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'NWP FORECAST',
                      style: TextStyle(
                        fontSize: 10.5,
                        fontWeight: FontWeight.w700,
                        color: AppColors.textFaint,
                        letterSpacing: 0.05,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      '${precip.toStringAsFixed(1)}mm',
                      style: const TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.w800,
                        color: AppColors.text,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${temp.toStringAsFixed(1)}°C · ${wind.toStringAsFixed(1)} m/s',
                      style: const TextStyle(
                        fontSize: 11.5,
                        color: AppColors.textDim,
                        fontWeight: FontWeight.w500,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 10),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: AppColors.card2,
                        borderRadius: BorderRadius.circular(6),
                        border: Border.all(color: AppColors.stroke),
                      ),
                      child: Text(
                        'Day $dayNum (${prediction.leadHours}h)',
                        style: const TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w600,
                          color: AppColors.textFaint,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(width: 10),

            // RIGHT CARD: Bust Probability & Reliability
            Expanded(
              child: Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: AppColors.card,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: isExtended ? AppColors.orange.withOpacity(0.5) : AppColors.strokeStrong,
                  ),
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [
                      riskColor.withOpacity(0.08),
                      riskColor.withOpacity(0.02),
                    ],
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'BUST PROBABILITY',
                          style: TextStyle(
                            fontSize: 10.5,
                            fontWeight: FontWeight.w700,
                            color: AppColors.textFaint,
                            letterSpacing: 0.05,
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: riskColor.withOpacity(0.18),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Text(
                            isExtended ? 'EXTENDED' : prediction.riskLevel,
                            style: TextStyle(
                              fontSize: 9.5,
                              fontWeight: FontWeight.w800,
                              color: riskColor,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    Text(
                      prediction.bustProbabilityPercentage,
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.w800,
                        color: riskColor,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Reliability ${(relScore * 100).toStringAsFixed(1)}%',
                      style: TextStyle(
                        fontSize: 11.5,
                        color: isExtended ? AppColors.orange : AppColors.textDim,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 10),

                    // Progress Bar
                    Container(
                      height: 5,
                      width: double.infinity,
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.06),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: FractionallySizedBox(
                        alignment: Alignment.centerLeft,
                        widthFactor: relScore.clamp(0.0, 1.0),
                        child: Container(
                          decoration: BoxDecoration(
                            color: riskColor,
                            borderRadius: BorderRadius.circular(4),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),

        // SCIENTIFIC STATUS BANNER (Clearly differentiates Days 1-7 from Days 8-30)
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          decoration: BoxDecoration(
            color: isExtended ? AppColors.orange.withOpacity(0.10) : AppColors.green.withOpacity(0.08),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: isExtended ? AppColors.orange.withOpacity(0.35) : AppColors.green.withOpacity(0.25),
            ),
          ),
          child: Row(
            children: [
              Icon(
                isExtended ? Icons.warning_amber_rounded : Icons.verified_outlined,
                color: isExtended ? AppColors.orange : AppColors.green,
                size: 20,
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      isExtended
                          ? 'STATUS: UNVALIDATED EXTENDED RANGE'
                          : 'STATUS: SCIENTIFICALLY VALIDATED',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w800,
                        color: isExtended ? AppColors.orange : AppColors.green,
                        letterSpacing: 0.03,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      isExtended
                          ? 'Exploratory estimate only (Day $dayNum / ${prediction.leadHours}h). Days 8–30 have no formal scientific ERA5 validation.'
                          : 'Validated against ECMWF ERA5 reanalysis reference data (Day $dayNum / ${prediction.leadHours}h).',
                      style: const TextStyle(
                        fontSize: 10.5,
                        color: AppColors.textDim,
                        height: 1.3,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 10),

        // Action Row: "Why?" Button and Scientific Clarification
        InkWell(
          onTap: () {
            showModalBottomSheet(
              context: context,
              isScrollControlled: true,
              backgroundColor: Colors.transparent,
              builder: (_) => ShapBottomSheet(prediction: prediction),
            );
          },
          borderRadius: BorderRadius.circular(12),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            decoration: BoxDecoration(
              color: AppColors.card2,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.strokeStrong.withOpacity(0.2)),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: const [
                    Icon(Icons.help_outline, color: AppColors.green, size: 18),
                    SizedBox(width: 8),
                    Text(
                      'Why does AI predict this reliability?',
                      style: TextStyle(
                        fontSize: 12.5,
                        fontWeight: FontWeight.w700,
                        color: AppColors.text,
                      ),
                    ),
                  ],
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.green.withOpacity(0.12),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    children: const [
                      Text(
                        'TreeSHAP',
                        style: TextStyle(
                          fontSize: 10.5,
                          fontWeight: FontWeight.w700,
                          color: AppColors.green,
                        ),
                      ),
                      SizedBox(width: 2),
                      Icon(Icons.chevron_right, color: AppColors.green, size: 16),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 10),

        // Mandatory Scientific Governance Disclaimer
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          decoration: BoxDecoration(
            color: AppColors.card.withOpacity(0.5),
            borderRadius: BorderRadius.circular(8),
          ),
          child: const Text(
            'Disclaimer: This system provides forecast reliability estimation and does not replace official NWP or meteorological advisories.',
            style: TextStyle(fontSize: 9.5, color: AppColors.textFaint, fontStyle: FontStyle.italic, height: 1.3),
            textAlign: TextAlign.center,
          ),
        ),
      ],
    );
  }
}
