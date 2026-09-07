class ShapFactor {
  final String feature;
  final double attribution;
  final dynamic rawValue;
  final String? description;
  final bool isAmplifier;

  const ShapFactor({
    required this.feature,
    required this.attribution,
    this.rawValue,
    this.description,
    required this.isAmplifier,
  });

  String get displayName {
    switch (feature) {
      case 'run_revision':
      case 'run_consistency':
        return 'Run Consistency';
      case 'ensemble_spread':
        return 'Ensemble Spread';
      case 'lead_hours':
        return 'Forecast Horizon';
      case 'forecast_precip':
      case 'forecast_precipitation':
        return 'Forecast Precipitation';
      case 'forecast_temp':
      case 'forecast_temperature':
        return 'Forecast Temperature';
      case 'forecast_wind':
        return 'Wind Speed';
      case 'forecast_press':
      case 'forecast_pressure':
        return 'Barometric Pressure';
      case 'forecast_hum':
      case 'forecast_humidity':
        return 'Relative Humidity';
      default:
        return feature
            .replaceAll('_', ' ')
            .split(' ')
            .map((w) => w.isNotEmpty ? '${w[0].toUpperCase()}${w.substring(1)}' : '')
            .join(' ');
    }
  }

  factory ShapFactor.fromJson(Map<String, dynamic> json) {
    final attr = (json['attribution'] as num?)?.toDouble() ??
        (json['shap_value'] as num?)?.toDouble() ??
        0.0;
    return ShapFactor(
      feature: json['feature'] as String? ?? json['name'] as String? ?? 'factor',
      attribution: attr,
      rawValue: json['raw_value'] ?? json['value'] ?? json['actual_value'],
      description: json['description'] as String?,
      isAmplifier: attr > 0,
    );
  }
}

class ShapExplanation {
  final String summaryText;
  final List<ShapFactor> topAmplifiers;
  final List<ShapFactor> topMitigators;
  final List<ShapFactor> allFactors;
  final String causalityDisclaimer;

  const ShapExplanation({
    required this.summaryText,
    required this.topAmplifiers,
    required this.topMitigators,
    required this.allFactors,
    required this.causalityDisclaimer,
  });

  factory ShapExplanation.fromJson(Map<String, dynamic> json) {
    final amps = (json['top_amplifiers'] as List<dynamic>? ?? [])
        .map((e) => ShapFactor.fromJson(e as Map<String, dynamic>))
        .toList();
    final mits = (json['top_mitigators'] as List<dynamic>? ?? [])
        .map((e) => ShapFactor.fromJson(e as Map<String, dynamic>))
        .toList();
    final all = (json['all_factors'] as List<dynamic>? ?? [])
        .map((e) => ShapFactor.fromJson(e as Map<String, dynamic>))
        .toList();

    return ShapExplanation(
      summaryText: json['summary_text'] as String? ??
          'Statistical TreeSHAP model feature attribution indicates low bust likelihood.',
      topAmplifiers: amps,
      topMitigators: mits,
      allFactors: all,
      causalityDisclaimer: json['causality_disclaimer'] as String? ??
          'SHAP values reflect model feature attributions, not direct physical causes.',
    );
  }
}

class RiskPrediction {
  final double latitude;
  final double longitude;
  final int leadHours;
  final String variable;
  final double forecastValue;
  final String thresholdCriteria;
  final double bustProbability;
  final String bustProbabilityPercentage;
  final double reliabilityScore;
  final String reliabilityScorePercentage;
  final String riskLevel;
  final String riskBadge;
  final String forecastSource;
  final ShapExplanation? explanation;

  const RiskPrediction({
    required this.latitude,
    required this.longitude,
    required this.leadHours,
    required this.variable,
    required this.forecastValue,
    required this.thresholdCriteria,
    required this.bustProbability,
    required this.bustProbabilityPercentage,
    required this.reliabilityScore,
    required this.reliabilityScorePercentage,
    required this.riskLevel,
    required this.riskBadge,
    required this.forecastSource,
    this.explanation,
  });

  factory RiskPrediction.fromJson(Map<String, dynamic> json) {
    final p = (json['bust_probability'] as num?)?.toDouble() ?? 0.05;
    final rel = (json['reliability_score'] as num?)?.toDouble() ?? (1.0 - p);

    final rawLat = json['latitude'] ??
        (json['location'] is Map ? (json['location'] as Map)['latitude'] : null);
    final rawLon = json['longitude'] ??
        (json['location'] is Map ? (json['location'] as Map)['longitude'] : null);

    final lat = (rawLat as num?)?.toDouble() ?? 0.0;
    final lon = (rawLon as num?)?.toDouble() ?? 0.0;

    final lead = json['lead_hours'] as int? ??
        json['forecast_horizon_hours'] as int? ??
        72;

    String pPct;
    final rawPPct = json['bust_probability_percentage'];
    if (rawPPct is num) {
      pPct = '${rawPPct.toStringAsFixed(1)}%';
    } else if (rawPPct is String) {
      pPct = rawPPct.contains('%') ? rawPPct : '$rawPPct%';
    } else {
      pPct = '${(p * 100).toStringAsFixed(1)}%';
    }

    String relPct;
    final rawRelPct = json['reliability_score_percentage'] ?? json['reliability_percentage'];
    if (rawRelPct is num) {
      relPct = '${rawRelPct.toStringAsFixed(1)}%';
    } else if (rawRelPct is String) {
      relPct = rawRelPct.contains('%') ? rawRelPct : '$rawRelPct%';
    } else {
      relPct = '${(rel * 100).toStringAsFixed(1)}%';
    }

    ShapExplanation? expl;
    if (json['explanation'] != null && json['explanation'] is Map<String, dynamic>) {
      expl = ShapExplanation.fromJson(json['explanation'] as Map<String, dynamic>);
    }

    return RiskPrediction(
      latitude: lat,
      longitude: lon,
      leadHours: lead,
      variable: json['variable'] as String? ?? 'precipitation',
      forecastValue: (json['forecast_value'] as num?)?.toDouble() ?? 0.0,
      thresholdCriteria: json['threshold_criteria'] as String? ?? '> 10.0mm absolute error',
      bustProbability: p,
      bustProbabilityPercentage: pPct,
      reliabilityScore: rel,
      reliabilityScorePercentage: relPct,
      riskLevel: json['risk_level'] as String? ?? 'LOW',
      riskBadge: json['risk_badge'] as String? ?? '🟢 LOW',
      forecastSource: json['forecast_source'] as String? ?? 'ECMWF IFS (Operational NWP)',
      explanation: expl,
    );
  }
}

class StationRiskPoint {
  final String stationName;
  final double latitude;
  final double longitude;
  final double bustProbability;
  final double reliabilityScore;
  final String riskLevel;
  final String riskBadge;

  const StationRiskPoint({
    required this.stationName,
    required this.latitude,
    required this.longitude,
    required this.bustProbability,
    required this.reliabilityScore,
    required this.riskLevel,
    required this.riskBadge,
  });

  factory StationRiskPoint.fromJson(Map<String, dynamic> json) {
    final p = (json['bust_probability'] as num?)?.toDouble() ?? 0.05;
    return StationRiskPoint(
      stationName: json['station_name'] as String? ?? json['name'] as String? ?? 'Synoptic Station',
      latitude: (json['latitude'] as num?)?.toDouble() ?? 0.0,
      longitude: (json['longitude'] as num?)?.toDouble() ?? 0.0,
      bustProbability: p,
      reliabilityScore: (json['reliability_score'] as num?)?.toDouble() ?? (1.0 - p),
      riskLevel: json['risk_level'] as String? ?? 'LOW',
      riskBadge: json['risk_badge'] as String? ?? '🟢 LOW',
    );
  }
}
