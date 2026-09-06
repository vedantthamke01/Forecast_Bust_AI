import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:forecast_bust_detection/core/api_client.dart';
import 'package:forecast_bust_detection/models/weather_models.dart';
import 'package:forecast_bust_detection/models/risk_models.dart';

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

final selectedLocationProvider = StateProvider<LocationModel>((ref) {
  return LocationModel(
    name: 'Pune',
    district: 'Pune',
    state: 'Maharashtra',
    latitude: 18.5204,
    longitude: 73.8567,
    elevation: 560.0,
  );
});

final selectedLeadHoursProvider = StateProvider<int>((ref) => 96);
final selectedVariableProvider = StateProvider<String>((ref) => 'precipitation');

final currentRiskProvider = FutureProvider<PredictionRiskModel?>((ref) async {
  final client = ref.watch(apiClientProvider);
  final loc = ref.watch(selectedLocationProvider);
  final lead = ref.watch(selectedLeadHoursProvider);
  final variable = ref.watch(selectedVariableProvider);

  return await client.getRiskForLocation(
    latitude: loc.latitude,
    longitude: loc.longitude,
    leadHours: lead,
    variable: variable,
  );
});

final forecastHorizonsProvider = FutureProvider<List<ForecastModel>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final loc = ref.watch(selectedLocationProvider);
  return await client.getForecast(latitude: loc.latitude, longitude: loc.longitude, days: 10);
});

final historicalVerificationProvider = FutureProvider<List<HistoricalRecordModel>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final loc = ref.watch(selectedLocationProvider);
  return await client.getHistoricalVerification(latitude: loc.latitude, longitude: loc.longitude);
});

final riskMapGridProvider = FutureProvider<List<Map<String, dynamic>>>((ref) async {
  final client = ref.watch(apiClientProvider);
  final lead = ref.watch(selectedLeadHoursProvider);
  final variable = ref.watch(selectedVariableProvider);
  return await client.getRiskMapGrid(leadHours: lead, variable: variable);
});
