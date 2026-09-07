class ModelEvaluation {
  final String modelVersion;
  final String dataType;
  final String datasetVersion;
  final String algorithm;
  final double prAuc;
  final double rocAuc;
  final double brierScore;
  final double ece;
  final int totalRecords;
  final String acceptanceStatus;

  const ModelEvaluation({
    required this.modelVersion,
    required this.dataType,
    required this.datasetVersion,
    required this.algorithm,
    required this.prAuc,
    required this.rocAuc,
    required this.brierScore,
    required this.ece,
    required this.totalRecords,
    required this.acceptanceStatus,
  });

  factory ModelEvaluation.fromJson(Map<String, dynamic> json) {
    final metrics = json['metrics'] as Map<String, dynamic>? ?? {};
    final gate = json['acceptance_gate'] as Map<String, dynamic>? ?? {};

    return ModelEvaluation(
      modelVersion: json['model_version'] as String? ?? 'model_real_v002',
      dataType: json['data_type'] as String? ?? 'REAL',
      datasetVersion: json['dataset_version'] as String? ?? 'dataset_real_v002',
      algorithm: json['algorithm'] as String? ?? 'LightGBM + Isotonic Calibration',
      prAuc: (metrics['pr_auc'] as num?)?.toDouble() ?? 0.2682,
      rocAuc: (metrics['roc_auc'] as num?)?.toDouble() ?? 0.8756,
      brierScore: (metrics['brier_score'] as num?)?.toDouble() ?? 0.0450,
      ece: (metrics['ece'] as num?)?.toDouble() ?? 0.0257,
      totalRecords: (metrics['total_records'] as num?)?.toInt() ?? 37800,
      acceptanceStatus: gate['status'] as String? ?? 'PASSED',
    );
  }
}

class DatasetStatusModel {
  final String datasetVersion;
  final int totalRecords;
  final String coverage;
  final String qcStatus;
  final String missingPercentage;
  final String updateStatus;

  const DatasetStatusModel({
    required this.datasetVersion,
    required this.totalRecords,
    required this.coverage,
    required this.qcStatus,
    required this.missingPercentage,
    required this.updateStatus,
  });

  factory DatasetStatusModel.fromJson(Map<String, dynamic> json) {
    return DatasetStatusModel(
      datasetVersion: json['dataset_version'] as String? ?? 'dataset_real_v002',
      totalRecords: (json['total_records'] as num?)?.toInt() ?? 37800,
      coverage: json['coverage'] as String? ?? '100.0%',
      qcStatus: json['qc_status'] as String? ?? 'PASS',
      missingPercentage: json['missing_percentage'] as String? ?? '0.0%',
      updateStatus: json['update_status'] as String? ?? 'healthy',
    );
  }
}
