class ShapFactor {
  final String feature;
  final String description;
  final double actualValue;
  final double shapValue;
  final String impact; // AMPLIFIER or MITIGATOR

  ShapFactor({
    required this.feature,
    required this.description,
    required this.actualValue,
    required this.shapValue,
    required this.impact,
  });

  factory ShapFactor.fromJson(Map<String, dynamic> json) {
    return ShapFactor(
      feature: json['feature'] ?? '',
      description: json['description'] ?? '',
      actualValue: (json['actual_value'] as num?)?.toDouble() ?? 0.0,
      shapValue: (json['shap_value'] as num?)?.toDouble() ?? 0.0,
      impact: json['impact'] ?? 'AMPLIFIER',
    );
  }
}

class PredictionRiskModel {
  final double latitude;
  final double longitude;
  final int leadHours;
  final int leadDay;
  final String variable;
  final double forecastValue;
  final double bustProbability;
  final double reliabilityScore;
  final String riskLevel;
  final String riskBadge;
  final String modelVersion;
  final List<ShapFactor> shapFactors;
  final String? summaryText;

  PredictionRiskModel({
    required this.latitude,
    required this.longitude,
    required this.leadHours,
    required this.leadDay,
    required this.variable,
    required this.forecastValue,
    required this.bustProbability,
    required this.reliabilityScore,
    required this.riskLevel,
    required this.riskBadge,
    required this.modelVersion,
    this.shapFactors = const [],
    this.summaryText,
  });

  factory PredictionRiskModel.fromJson(Map<String, dynamic> json) {
    final loc = json['location'] as Map<String, dynamic>? ?? {};
    final exp = json['explanation'] as Map<String, dynamic>? ?? {};
    final rawFactors = (exp['all_factors'] as List<dynamic>?) ?? [];
    final factors = rawFactors.map((f) => ShapFactor.fromJson(f as Map<String, dynamic>)).toList();

    return PredictionRiskModel(
      latitude: (loc['latitude'] as num?)?.toDouble() ?? 18.52,
      longitude: (loc['longitude'] as num?)?.toDouble() ?? 73.85,
      leadHours: json['forecast_horizon_hours'] ?? 96,
      leadDay: json['forecast_day'] ?? 4,
      variable: json['variable'] ?? 'precipitation',
      forecastValue: (json['forecast_value'] as num?)?.toDouble() ?? 0.0,
      bustProbability: (json['bust_probability'] as num?)?.toDouble() ?? 0.0,
      reliabilityScore: (json['reliability_score'] as num?)?.toDouble() ?? 1.0,
      riskLevel: json['risk_level'] ?? 'LOW',
      riskBadge: json['risk_badge'] ?? '🟢 LOW',
      modelVersion: json['model_version'] ?? 'model_v001',
      shapFactors: factors,
      summaryText: exp['summary_text'],
    );
  }
}

class HistoricalRecordModel {
  final String initializationTime;
  final String validTime;
  final int leadHours;
  final double forecastValue;
  final double referenceValue;
  final double absoluteError;
  final bool isBust;
  final String severity;
  final String thresholdMethod;

  HistoricalRecordModel({
    required this.initializationTime,
    required this.validTime,
    required this.leadHours,
    required this.forecastValue,
    required this.referenceValue,
    required this.absoluteError,
    required this.isBust,
    required this.severity,
    required this.thresholdMethod,
  });

  factory HistoricalRecordModel.fromJson(Map<String, dynamic> json) {
    return HistoricalRecordModel(
      initializationTime: json['initialization_time'] ?? '',
      validTime: json['valid_time'] ?? '',
      leadHours: json['lead_hours'] ?? 96,
      forecastValue: (json['forecast_value'] as num?)?.toDouble() ?? 0.0,
      referenceValue: (json['reference_value'] as num?)?.toDouble() ?? 0.0,
      absoluteError: (json['absolute_error'] as num?)?.toDouble() ?? 0.0,
      isBust: json['is_bust'] ?? false,
      severity: json['bust_severity'] ?? 'NONE',
      thresholdMethod: json['labeling_method'] ?? 'DYNAMIC_HORIZON_SCALED',
    );
  }
}
