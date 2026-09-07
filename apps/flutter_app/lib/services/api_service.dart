import '../core/api_client.dart';
import '../models/weather_models.dart';
import '../models/risk_models.dart';
import '../models/verification_models.dart';
import '../models/advanced_models.dart';

class ApiService {
  final ApiClient client;

  ApiService({required this.client});

  Future<CurrentWeather> getCurrentWeather(double lat, double lon) async {
    final response = await client.dio.get(
      '/api/weather/current',
      queryParameters: {'lat': lat, 'lon': lon},
    );
    return CurrentWeather.fromJson(response.data as Map<String, dynamic>);
  }

  Future<List<ForecastHorizon>> getForecast(double lat, double lon, {int days = 10}) async {
    final response = await client.dio.get(
      '/api/weather/forecast',
      queryParameters: {'lat': lat, 'lon': lon, 'days': days},
    );
    final data = response.data as Map<String, dynamic>;
    final list = data['horizons'] as List<dynamic>? ?? [];
    return list.map((e) => ForecastHorizon.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<RiskPrediction> getRiskByLocation({
    required double lat,
    required double lon,
    int leadHours = 96,
    String variable = 'precipitation',
    double? forecastValue,
    double? ensembleSpread,
  }) async {
    final queryParams = <String, dynamic>{
      'lat': lat,
      'lon': lon,
      'lead_hours': leadHours,
      'variable': variable,
    };
    if (forecastValue != null) queryParams['forecast_value'] = forecastValue;
    if (ensembleSpread != null) queryParams['ensemble_spread'] = ensembleSpread;

    final response = await client.dio.get(
      '/api/risk/location',
      queryParameters: queryParams,
    );
    return RiskPrediction.fromJson(response.data as Map<String, dynamic>);
  }

  Future<List<StationRiskPoint>> getRiskMap({
    int leadHours = 96,
    String variable = 'precipitation',
  }) async {
    final response = await client.dio.get(
      '/api/risk/map',
      queryParameters: {'lead_hours': leadHours, 'variable': variable},
    );
    final data = response.data as Map<String, dynamic>;
    final list = (data['stations'] ?? data['grid']) as List<dynamic>? ?? [];
    return list.map((e) => StationRiskPoint.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<HistoricalVerification> getHistoricalVerification({
    required double lat,
    required double lon,
    int limit = 10,
  }) async {
    final response = await client.dio.get(
      '/api/risk/history',
      queryParameters: {'lat': lat, 'lon': lon, 'limit': limit},
    );
    return HistoricalVerification.fromJson(response.data as Map<String, dynamic>);
  }

  Future<ModelEvaluation> getModelEvaluation() async {
    final response = await client.dio.get('/api/models/evaluate');
    return ModelEvaluation.fromJson(response.data as Map<String, dynamic>);
  }

  Future<DatasetStatusModel> getDatasetStatus() async {
    final response = await client.dio.get('/api/datasets/status');
    return DatasetStatusModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<List<LocationModel>> searchLocations(String query) async {
    final response = await client.dio.get(
      '/api/locations/search',
      queryParameters: {'q': query},
    );
    final data = response.data as Map<String, dynamic>;
    final list = data['results'] as List<dynamic>? ?? [];
    return list.map((e) => LocationModel.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<LocationModel?> reverseGeocode(double lat, double lon) async {
    try {
      final response = await client.dio.get(
        '/api/locations/reverse',
        queryParameters: {'lat': lat, 'lon': lon},
      );
      return LocationModel.fromJson(response.data as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  Future<Map<String, dynamic>> getHealth() async {
    final response = await client.dio.get('/health');
    return response.data as Map<String, dynamic>;
  }
}
