class LocationModel {
  final String name;
  final String? state;
  final String? country;
  final double latitude;
  final double longitude;

  const LocationModel({
    required this.name,
    this.state,
    this.country,
    required this.latitude,
    required this.longitude,
  });

  String get displayName {
    if (state != null && state!.isNotEmpty) {
      return '$name, $state';
    }
    if (country != null && country!.isNotEmpty) {
      return '$name, $country';
    }
    return name;
  }

  factory LocationModel.fromJson(Map<String, dynamic> json) {
    return LocationModel(
      name: json['name'] as String? ?? 'Custom Location',
      state: json['state'] as String? ?? json['admin1'] as String?,
      country: json['country'] as String?,
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
        'name': name,
        'state': state,
        'country': country,
        'latitude': latitude,
        'longitude': longitude,
      };
}

class CurrentWeather {
  final double latitude;
  final double longitude;
  final DateTime observationTime;
  final double temperatureC;
  final double precipitationMm;
  final double windSpeedMps;
  final double? pressureHpa;
  final double? humidityPercent;
  final double? cloudCoverPercent;
  final String provider;
  final String model;

  const CurrentWeather({
    required this.latitude,
    required this.longitude,
    required this.observationTime,
    required this.temperatureC,
    required this.precipitationMm,
    required this.windSpeedMps,
    this.pressureHpa,
    this.humidityPercent,
    this.cloudCoverPercent,
    required this.provider,
    required this.model,
  });

  String get conditionText {
    if (precipitationMm > 5.0) return 'Heavy Rain';
    if (precipitationMm > 0.5) return 'Light Rain';
    if ((cloudCoverPercent ?? 0) > 80) return 'Overcast';
    if ((cloudCoverPercent ?? 0) > 40) return 'Partly Cloudy';
    if (windSpeedMps > 10.0) return 'Windy';
    return 'Clear Sky';
  }

  factory CurrentWeather.fromJson(Map<String, dynamic> json) {
    final loc = json['location'] as Map<String, dynamic>? ?? {};
    return CurrentWeather(
      latitude: (loc['latitude'] as num?)?.toDouble() ?? 0.0,
      longitude: (loc['longitude'] as num?)?.toDouble() ?? 0.0,
      observationTime: json['observation_time'] != null
          ? DateTime.tryParse(json['observation_time'].toString()) ?? DateTime.now()
          : DateTime.now(),
      temperatureC: (json['temperature_c'] as num?)?.toDouble() ?? 0.0,
      precipitationMm: (json['precipitation_mm'] as num?)?.toDouble() ?? 0.0,
      windSpeedMps: (json['wind_speed_mps'] as num?)?.toDouble() ?? 0.0,
      pressureHpa: (json['pressure_hpa'] as num?)?.toDouble(),
      humidityPercent: (json['humidity_percent'] as num?)?.toDouble(),
      cloudCoverPercent: (json['cloud_cover_percent'] as num?)?.toDouble(),
      provider: json['provider'] as String? ?? 'Open-Meteo',
      model: json['model'] as String? ?? 'ECMWF IFS',
    );
  }
}

class ForecastHorizon {
  final int leadHours;
  final DateTime validTime;
  final double? temperature2m;
  final double? precipitation;
  final double? windSpeed10m;
  final double? pressureMsl;
  final double? relativeHumidity2m;
  final double? cloudCover;
  final double? ensembleSpread;
  final double? runRevision;
  final String provider;
  final String model;

  const ForecastHorizon({
    required this.leadHours,
    required this.validTime,
    this.temperature2m,
    this.precipitation,
    this.windSpeed10m,
    this.pressureMsl,
    this.relativeHumidity2m,
    this.cloudCover,
    this.ensembleSpread,
    this.runRevision,
    required this.provider,
    required this.model,
  });

  factory ForecastHorizon.fromJson(Map<String, dynamic> json) {
    return ForecastHorizon(
      leadHours: json['lead_hours'] as int? ?? 0,
      validTime: json['valid_time'] != null
          ? DateTime.tryParse(json['valid_time'].toString()) ?? DateTime.now()
          : DateTime.now(),
      temperature2m: (json['temperature_2m'] as num?)?.toDouble(),
      precipitation: (json['precipitation'] as num?)?.toDouble(),
      windSpeed10m: (json['wind_speed_10m'] as num?)?.toDouble(),
      pressureMsl: (json['pressure_msl'] as num?)?.toDouble(),
      relativeHumidity2m: (json['relative_humidity_2m'] as num?)?.toDouble(),
      cloudCover: (json['cloud_cover'] as num?)?.toDouble(),
      ensembleSpread: (json['ensemble_spread'] as num?)?.toDouble(),
      runRevision: (json['run_revision'] as num?)?.toDouble(),
      provider: json['provider'] as String? ?? 'ECMWF IFS',
      model: json['model'] as String? ?? 'Operational NWP',
    );
  }
}
