import 'package:flutter/material.dart';
import '../../../core/constants.dart';

class PipelineStepInfo {
  final int step;
  final String title;
  final String description;
  final String details;

  const PipelineStepInfo({
    required this.step,
    required this.title,
    required this.description,
    required this.details,
  });
}

const List<PipelineStepInfo> pipelineSteps = [
  PipelineStepInfo(
    step: 1,
    title: 'Download',
    description: 'Retrieve authentic NWP forecasts and ERA5 reference reanalysis.',
    details: 'Historical Open-Meteo Previous Runs archive paired with Copernicus CDS ERA5 grid data.',
  ),
  PipelineStepInfo(
    step: 2,
    title: 'Validate',
    description: 'Thermodynamic boundary checks and schema integrity verification.',
    details: 'Ensures temperatures (-100 to 75°C), precipitation (0 to 2000mm), and pressures (800 to 1100hPa) are physically valid.',
  ),
  PipelineStepInfo(
    step: 3,
    title: 'Align',
    description: 'Strict temporal pairing between forecast valid times and reference observations.',
    details: 'Prevents future leakage by enforcing exact valid-time synchronization (T₀ + τ).',
  ),
  PipelineStepInfo(
    step: 4,
    title: 'Label',
    description: 'Apply operational bust definition criteria.',
    details: 'A bust is assigned when absolute forecast error exceeds configured meteorological threshold criteria.',
  ),
  PipelineStepInfo(
    step: 5,
    title: 'Train',
    description: 'LightGBM gradient boosted decision trees for bust classification.',
    details: 'Trained on 37,800 records across 25 Indian synoptic stations with strict chronological validation splits.',
  ),
  PipelineStepInfo(
    step: 6,
    title: 'Calibrate',
    description: 'Isotonic probability calibration for reliable risk estimation.',
    details: 'Ensures that a predicted 10% bust probability genuinely corresponds to an observed 10% empirical failure rate (ECE: 0.0257).',
  ),
];

void showPipelineStepDialog(BuildContext context, int stepIndex) {
  final info = pipelineSteps[stepIndex];
  showDialog(
    context: context,
    builder: (_) => Dialog(
      backgroundColor: AppColors.card,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppColors.strokeStrong),
      ),
      child: Padding(
        padding: const EdgeInsets.all(18.0),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 32,
                  height: 32,
                  decoration: BoxDecoration(
                    color: AppColors.green.withOpacity(0.15),
                    shape: BoxShape.circle,
                    border: Border.all(color: AppColors.green, width: 1.5),
                  ),
                  child: Center(
                    child: Text(
                      '${info.step}',
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w800,
                        color: AppColors.green,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Text(
                  'Step ${info.step}: ${info.title}',
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w800,
                    color: AppColors.text,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              info.description,
              style: const TextStyle(fontSize: 12, color: AppColors.text, height: 1.3),
            ),
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppColors.card2,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                info.details,
                style: const TextStyle(fontSize: 10.5, color: AppColors.textDim, height: 1.3),
              ),
            ),
            const SizedBox(height: 14),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('Close', style: TextStyle(color: AppColors.green, fontWeight: FontWeight.w700)),
              ),
            ),
          ],
        ),
      ),
    ),
  );
}
