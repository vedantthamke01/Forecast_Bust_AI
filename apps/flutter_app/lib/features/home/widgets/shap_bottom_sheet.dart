import 'package:flutter/material.dart';
import '../../../core/constants.dart';
import '../../../models/risk_models.dart';

class ShapBottomSheet extends StatelessWidget {
  final RiskPrediction prediction;

  const ShapBottomSheet({super.key, required this.prediction});

  @override
  Widget build(BuildContext context) {
    final expl = prediction.explanation;
    final amplifiers = expl?.topAmplifiers ?? [];
    final mitigators = expl?.topMitigators ?? [];

    return Container(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 28),
      decoration: const BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        border: Border(top: BorderSide(color: AppColors.strokeStrong, width: 1.5)),
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Drag Handle
            Center(
              child: Container(
                width: 36,
                height: 4,
                margin: const EdgeInsets.only(bottom: 14),
                decoration: BoxDecoration(
                  color: AppColors.strokeStrong,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),

            // Title & Probability Badge
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Why this forecast has this reliability',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w800,
                          color: AppColors.text,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'TreeSHAP Model Feature Attribution · Day ${(prediction.leadHours / 24).round()}',
                        style: const TextStyle(
                          fontSize: 10,
                          color: AppColors.textDim,
                        ),
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.forRiskLevel(prediction.riskLevel).withOpacity(0.15),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppColors.forRiskLevel(prediction.riskLevel).withOpacity(0.4)),
                  ),
                  child: Text(
                    prediction.riskBadge,
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w800,
                      color: AppColors.forRiskLevel(prediction.riskLevel),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),

            // Dynamic Summary Text from Backend
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppColors.card2,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.stroke),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.psychology_outlined, color: AppColors.green, size: 20),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      expl?.summaryText ??
                          'Model-estimated forecast bust probability is ${prediction.bustProbabilityPercentage} based on operational NWP features.',
                      style: const TextStyle(
                        fontSize: 11.5,
                        color: AppColors.text,
                        height: 1.35,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Risk Amplifiers Section
            if (amplifiers.isNotEmpty) ...[
              Row(
                children: const [
                  Text(
                    '🔺 RISK AMPLIFIERS (Pushed risk higher)',
                    style: TextStyle(
                      fontSize: 9.5,
                      fontWeight: FontWeight.w800,
                      color: AppColors.red,
                      letterSpacing: 0.05,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              ...amplifiers.map((factor) => _buildFactorCard(factor, isAmplifier: true)),
              const SizedBox(height: 12),
            ],

            // Risk Mitigators Section
            if (mitigators.isNotEmpty) ...[
              Row(
                children: const [
                  Text(
                    '🛡️ RISK MITIGATORS (Stabilized reliability)',
                    style: TextStyle(
                      fontSize: 9.5,
                      fontWeight: FontWeight.w800,
                      color: AppColors.green,
                      letterSpacing: 0.05,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              ...mitigators.map((factor) => _buildFactorCard(factor, isAmplifier: false)),
              const SizedBox(height: 12),
            ],

            // Causality & Scientific Disclaimer
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.2),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: AppColors.stroke),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.info_outline, color: AppColors.textDim, size: 14),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      expl?.causalityDisclaimer ??
                          'TreeSHAP values quantify statistical model feature attribution and do not claim direct atmospheric physical causation.',
                      style: const TextStyle(
                        fontSize: 9.5,
                        color: AppColors.textDim,
                        height: 1.3,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFactorCard(ShapFactor factor, {required bool isAmplifier}) {
    final color = isAmplifier ? AppColors.red : AppColors.green;
    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: AppColors.card2,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withOpacity(0.25)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  factor.displayName,
                  style: const TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: AppColors.text,
                  ),
                ),
                if (factor.rawValue != null)
                  Text(
                    'Value: ${factor.rawValue}',
                    style: const TextStyle(
                      fontSize: 9.5,
                      color: AppColors.textFaint,
                    ),
                  ),
              ],
            ),
          ),
          Text(
            '${factor.attribution >= 0 ? '+' : ''}${factor.attribution.toStringAsFixed(3)}',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w800,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}
