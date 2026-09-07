import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_client.dart';
import '../core/constants.dart';
import '../models/weather_models.dart';
import '../models/risk_models.dart';
import '../models/verification_models.dart';
import '../models/advanced_models.dart';
import '../services/api_service.dart';
import '../services/location_service.dart';

// 1. Core Service Providers
final apiClientProvider = Provider<ApiClient>((ref) {
  return ApiClient();
});

final apiServiceProvider = Provider<ApiService>((ref) {
  final client = ref.watch(apiClientProvider);
  return ApiService(client: client);
});

final locationServiceProvider = Provider<LocationService>((ref) {
  final api = ref.watch(apiServiceProvider);
  return LocationService(apiService: api);
});

// 2. Active Location & Navigation State
final activeLocationProvider = StateProvider<LocationModel>((ref) {
  return const LocationModel(
    name: AppConstants.defaultCity,
    state: AppConstants.defaultState,
    country: 'India',
    latitude: AppConstants.defaultLat,
    longitude: AppConstants.defaultLon,
  );
});

// Selected lead hours (e.g. 24, 72, 96, 120, 144, 168, 192, 216, 240)
final selectedLeadHoursProvider = StateProvider<int>((ref) => 72);

// 3. Operational Data Providers (Real backend calls)
final currentWeatherProvider = FutureProvider.autoDispose<CurrentWeather>((ref) async {
  final loc = ref.watch(activeLocationProvider);
  final api = ref.watch(apiServiceProvider);
  return api.getCurrentWeather(loc.latitude, loc.longitude);
});

final forecastTimelineProvider = FutureProvider.autoDispose<List<ForecastHorizon>>((ref) async {
  final loc = ref.watch(activeLocationProvider);
  final api = ref.watch(apiServiceProvider);
  return api.getForecast(loc.latitude, loc.longitude, days: 10);
});

final riskPredictionProvider = FutureProvider.autoDispose<RiskPrediction>((ref) async {
  final loc = ref.watch(activeLocationProvider);
  final leadHours = ref.watch(selectedLeadHoursProvider);
  final api = ref.watch(apiServiceProvider);

  return api.getRiskByLocation(
    lat: loc.latitude,
    lon: loc.longitude,
    leadHours: leadHours,
  );
});

final spatialRiskMapProvider = FutureProvider.autoDispose<List<StationRiskPoint>>((ref) async {
  final leadHours = ref.watch(selectedLeadHoursProvider);
  final api = ref.watch(apiServiceProvider);
  return api.getRiskMap(leadHours: leadHours);
});

final historicalVerificationProvider = FutureProvider.autoDispose<HistoricalVerification>((ref) async {
  final loc = ref.watch(activeLocationProvider);
  final api = ref.watch(apiServiceProvider);
  return api.getHistoricalVerification(lat: loc.latitude, lon: loc.longitude, limit: 10);
});

final modelEvaluationProvider = FutureProvider.autoDispose<ModelEvaluation>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return api.getModelEvaluation();
});

final datasetStatusProvider = FutureProvider.autoDispose<DatasetStatusModel>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return api.getDatasetStatus();
});

final backendHealthProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return api.getHealth();
});
