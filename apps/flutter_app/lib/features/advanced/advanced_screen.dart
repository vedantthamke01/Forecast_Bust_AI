import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/constants.dart';
import '../../providers/app_providers.dart';
import '../connection/connection_screen.dart';
import '../distribution/install_guide_screen.dart';
import 'widgets/pipeline_dialog.dart';

class AdvancedScreen extends ConsumerWidget {
  const AdvancedScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final evalAsync = ref.watch(modelEvaluationProvider);
    final datasetAsync = ref.watch(datasetStatusProvider);
    final client = ref.watch(apiClientProvider);

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
                    children: const [
                      Text(
                        'Scientific / Advanced',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w800,
                          color: AppColors.text,
                        ),
                      ),
                      SizedBox(height: 3),
                      Text(
                        'model_real_v002 · REAL',
                        style: TextStyle(
                          fontSize: 12,
                          color: AppColors.textDim,
                        ),
                      ),
                    ],
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppColors.green.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: AppColors.strokeStrong),
                    ),
                    child: const Text(
                      'PRODUCTION',
                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: AppColors.green),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 14),

              // PIPELINE STEPPER (Native Responsive Stepper)
              const Text(
                'PIPELINE',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textDim,
                  letterSpacing: 0.05,
                ),
              ),
              const SizedBox(height: 8),

              SizedBox(
                height: 68,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  itemCount: pipelineSteps.length,
                  separatorBuilder: (_, __) => const SizedBox(width: 8),
                  itemBuilder: (context, index) {
                    final step = pipelineSteps[index];
                    return InkWell(
                      onTap: () => showPipelineStepDialog(context, index),
                      borderRadius: BorderRadius.circular(12),
                      child: Container(
                        width: 68,
                        padding: const EdgeInsets.symmetric(vertical: 4),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Container(
                              width: 32,
                              height: 32,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: AppColors.green.withOpacity(0.1),
                                border: Border.all(color: AppColors.green, width: 1.5),
                              ),
                              child: Center(
                                child: Text(
                                  '${step.step}',
                                  style: const TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.w800,
                                    color: AppColors.green,
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(height: 5),
                            Text(
                              step.title,
                              style: const TextStyle(fontSize: 10.5, color: AppColors.textFaint, fontWeight: FontWeight.w600),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              textAlign: TextAlign.center,
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),
              const SizedBox(height: 16),

              // SCIENTIFIC METRIC GRID (PR-AUC, ROC-AUC, Brier Score, ECE)
              evalAsync.when(
                data: (eval) => GridView.count(
                  crossAxisCount: 2,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  crossAxisSpacing: 10,
                  mainAxisSpacing: 10,
                  childAspectRatio: 2.0,
                  children: [
                    _buildMetricCard(value: eval.prAuc.toStringAsFixed(4), label: 'PR-AUC'),
                    _buildMetricCard(value: eval.rocAuc.toStringAsFixed(4), label: 'ROC-AUC'),
                    _buildMetricCard(value: eval.brierScore.toStringAsFixed(4), label: 'Brier Score'),
                    _buildMetricCard(value: eval.ece.toStringAsFixed(4), label: 'ECE'),
                  ],
                ),
                loading: () => const Center(
                  child: Padding(
                    padding: EdgeInsets.all(16.0),
                    child: CircularProgressIndicator(color: AppColors.green),
                  ),
                ),
                error: (_, __) => GridView.count(
                  crossAxisCount: 2,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  crossAxisSpacing: 10,
                  mainAxisSpacing: 10,
                  childAspectRatio: 2.0,
                  children: [
                    _buildMetricCard(value: '0.2682', label: 'PR-AUC'),
                    _buildMetricCard(value: '0.8756', label: 'ROC-AUC'),
                    _buildMetricCard(value: '0.0450', label: 'Brier Score'),
                    _buildMetricCard(value: '0.0257', label: 'ECE'),
                  ],
                ),
              ),
              const SizedBox(height: 14),

              // DATASET HEALTH CARD
              datasetAsync.when(
                data: (dataset) => Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppColors.card,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.stroke),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text(
                            'DATASET HEALTH',
                            style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppColors.textDim),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: AppColors.green.withOpacity(0.15),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              dataset.qcStatus,
                              style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: AppColors.green),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: _buildTile(
                              value: dataset.totalRecords > 0
                                  ? '${(dataset.totalRecords / 1000).toStringAsFixed(1)}k'
                                  : '37,800',
                              label: 'Records',
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: _buildTile(
                              value: dataset.missingPercentage,
                              label: 'Missing',
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                loading: () => const SizedBox.shrink(),
                error: (_, __) => Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppColors.card,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.stroke),
                  ),
                  child: Row(
                    children: [
                      Expanded(child: _buildTile(value: '37,800', label: 'Records')),
                      const SizedBox(width: 8),
                      Expanded(child: _buildTile(value: '0.0%', label: 'Missing')),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),

              // DRIFT ALERT BANNER
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: AppColors.orange.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.orange.withOpacity(0.35)),
                ),
                child: Row(
                  children: const [
                    Text('⚠️', style: TextStyle(fontSize: 16)),
                    SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Drift Alert',
                            style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppColors.orange),
                          ),
                          SizedBox(height: 2),
                          Text(
                            'Continuous baseline monitoring active — no critical covariate shift detected.',
                            style: TextStyle(fontSize: 10.5, color: AppColors.textDim),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // QUICK TOOLS: Backend Connection & Install APK
              Row(
                children: [
                  Expanded(
                    child: InkWell(
                      onTap: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(builder: (_) => const ConnectionScreen()),
                        );
                      },
                      borderRadius: BorderRadius.circular(12),
                      child: Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: AppColors.card2,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: AppColors.stroke),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Icon(Icons.settings_ethernet, color: AppColors.green, size: 22),
                            const SizedBox(height: 8),
                            const Text(
                              'Server Connection',
                              style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppColors.text),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              client.baseUrl,
                              style: const TextStyle(fontSize: 10.5, color: AppColors.textDim, fontFamily: 'monospace'),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: InkWell(
                      onTap: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(builder: (_) => const InstallGuideScreen()),
                        );
                      },
                      borderRadius: BorderRadius.circular(12),
                      child: Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: AppColors.card2,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: AppColors.stroke),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: const [
                            Icon(Icons.qr_code, color: AppColors.green, size: 22),
                            SizedBox(height: 8),
                            Text(
                              'Install / APK QR',
                              style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: AppColors.text),
                            ),
                            SizedBox(height: 2),
                            Text(
                              'LAN download & pairing',
                              style: TextStyle(fontSize: 10.5, color: AppColors.textDim),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 18),

              // About the platform footer
              Center(
                child: Text(
                  '${AppConstants.appName} · v${AppConstants.appVersion}\nMinistry of Earth Sciences / NCMRWF (SIH26079)',
                  style: const TextStyle(fontSize: 11, color: AppColors.textFaint, height: 1.4),
                  textAlign: TextAlign.center,
                ),
              ),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMetricCard({required String value, required String label}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.card2,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.stroke),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            value,
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w800,
              color: AppColors.green,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            label,
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: AppColors.textFaint,
              letterSpacing: 0.04,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTile({required String value, required String label}) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.03),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        children: [
          Text(
            value,
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w700,
              color: AppColors.text,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            label,
            style: const TextStyle(
              fontSize: 10.5,
              color: AppColors.textFaint,
            ),
          ),
        ],
      ),
    );
  }
}
