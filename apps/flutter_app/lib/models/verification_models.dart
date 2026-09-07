class ComparisonRecord {
  final String forecastId;
  final int leadHours;
  final DateTime validTime;
  final double forecastValue;
  final double referenceValue;
  final double absoluteError;
  final bool isBust;
  final String status;

  const ComparisonRecord({
    required this.forecastId,
    required this.leadHours,
    required this.validTime,
    required this.forecastValue,
    required this.referenceValue,
    required this.absoluteError,
    required this.isBust,
    required this.status,
  });

  factory ComparisonRecord.fromJson(Map<String, dynamic> json) {
    return ComparisonRecord(
      forecastId: json['forecast_id']?.toString() ?? 'rec_0',
      leadHours: json['lead_hours'] as int? ?? 24,
      validTime: json['valid_time'] != null
          ? DateTime.tryParse(json['valid_time'].toString()) ?? DateTime.now()
          : DateTime.now(),
      forecastValue: (json['forecast_value'] as num?)?.toDouble() ?? 0.0,
      referenceValue: (json['reference_value'] as num?)?.toDouble() ?? 0.0,
      absoluteError: (json['absolute_error'] as num?)?.toDouble() ?? 0.0,
      isBust: json['is_bust'] as bool? ?? false,
      status: json['status'] as String? ?? (json['is_bust'] == true ? 'BUST' : 'VERIFIED'),
    );
  }
}

class HistoricalVerification {
  final int sampleSize;
  final int bustCount;
  final double bustRatePercentage;
  final double averageError;
  final List<ComparisonRecord> records;

  const HistoricalVerification({
    required this.sampleSize,
    required this.bustCount,
    required this.bustRatePercentage,
    required this.averageError,
    required this.records,
  });

  factory HistoricalVerification.fromJson(Map<String, dynamic> json) {
    final list = (json['records'] as List<dynamic>? ?? [])
        .map((e) => ComparisonRecord.fromJson(e as Map<String, dynamic>))
        .toList();

    return HistoricalVerification(
      sampleSize: json['sample_size'] as int? ?? list.length,
      bustCount: json['bust_count'] as int? ?? 0,
      bustRatePercentage: (json['historical_bust_rate_percentage'] as num?)?.toDouble() ?? 0.0,
      averageError: (json['average_error'] as num?)?.toDouble() ?? 0.0,
      records: list,
    );
  }
}
