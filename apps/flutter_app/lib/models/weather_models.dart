class LocationModel {
  final String name;
  final String? district;
  final String? state;
  final double latitude;
  final double longitude;
  final double elevation;

  LocationModel({
    required this.name,
    this.district,
    this.state,
    required this.latitude,
    required this.longitude,
    this.elevation = 0.0,
  });

  factory LocationModel.fromJson(Map<String, dynamic> json) {
    return LocationModel(
      name: json['name'] ?? '',
      district: json['district'],
      state: json['state'],
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      elevation: (json['elevation'] as num?)?.toDouble() ?? 0.0,
    );
  }
}

class ForecastModel {
  final String provider;
  final String model;
  final String initializationTime;
  final String validTime;
  final int leadHours;
  final double? temperature;
  final double? precipitation;
  final double? windSpeed;
  final double? pressure;
  final double? humidity;
  final double? cloudCover;
  final double ensembleSpread;
  final double runRevision;

  ForecastModel({
    required this.provider,
    required this.model,
    required this.initializationTime,
    required this.validTime,
    required this.leadHours,
    this.temperature,
    this.precipitation,
    this.windSpeed,
    this.pressure,
    this.humidity,
    this.cloudCover,
    this.ensembleSpread = 0.0,
    this.runRevision = 0.0,
  });

  factory ForecastModel.fromJson(Map<String, dynamic> json) {
    return ForecastModel(
      provider: json['provider'] ?? 'open-meteo',
      model: json['model'] ?? 'ecmwf',
      initializationTime: json['initialization_time'] ?? '',
      validTime: json['valid_time'] ?? '',
      leadHours: json['lead_hours'] ?? 24,
      temperature: (json['temperature_2m'] as num?)?.toDouble(),
      precipitation: (json['precipitation'] as num?)?.toDouble(),
      windSpeed: (json['wind_speed_10m'] as num?)?.toDouble(),
      pressure: (json['pressure_msl'] as num?)?.toDouble(),
      humidity: (json['relative_humidity_2m'] as num?)?.toDouble(),
      cloudCover: (json['cloud_cover'] as num?)?.toDouble(),
      ensembleSpread: (json['ensemble_spread'] as num?)?.toDouble() ?? 0.0,
      runRevision: (json['run_revision'] as num?)?.toDouble() ?? 0.0,
    );
  }
}
