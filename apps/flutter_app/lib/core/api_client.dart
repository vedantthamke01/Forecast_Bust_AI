import 'package:dio/dio.dart';
import 'package:forecast_bust_detection/core/constants.dart';
import 'package:forecast_bust_detection/models/weather_models.dart';
import 'package:forecast_bust_detection/models/risk_models.dart';

class ApiClient {
  final Dio _dio;

  ApiClient({String baseUrl = AppConstants.defaultApiBaseUrl})
      : _dio = Dio(BaseOptions(
          baseUrl: baseUrl,
          connectTimeout: const Duration(seconds: 10),
          receiveTimeout: const Duration(seconds: 10),
          headers: {'Accept': 'application/json'},
        ));

  Future<List<LocationModel>> searchLocations(String query) async {
    try {
      final res = await _dio.get('/api/locations/search', queryParameters: {'q': query});
      final List results = res.data['results'] ?? [];
      return results.map((e) => LocationModel.fromJson(e)).toList();
    } catch (e) {
      return [];
    }
  }

  Future<PredictionRiskModel?> getRiskForLocation({
    required double latitude,
    required double longitude,
    required int leadHours,
    String variable = 'precipitation',
  }) async {
    try {
      final res = await _dio.get('/api/risk/location', queryParameters: {
        'lat': latitude,
        'lon': longitude,
        'lead_hours': leadHours,
        'variable': variable,
      });
      return PredictionRiskModel.fromJson(res.data);
    } catch (e) {
      return null;
    }
  }

  Future<List<ForecastModel>> getForecast({
    required double latitude,
    required double longitude,
    int days = 10,
  }) async {
    try {
      final res = await _dio.get('/api/weather/forecast', queryParameters: {
        'lat': latitude,
        'lon': longitude,
        'days': days,
      });
      final List list = res.data['horizons'] ?? [];
      return list.map((e) => ForecastModel.fromJson(e)).toList();
    } catch (e) {
      return [];
    }
  }

  Future<List<HistoricalRecordModel>> getHistoricalVerification({
    required double latitude,
    required double longitude,
    int limit = 10,
  }) async {
    try {
      final res = await _dio.get('/api/risk/history', queryParameters: {
        'lat': latitude,
        'lon': longitude,
        'limit': limit,
      });
      final List records = res.data['records'] ?? [];
      return records.map((e) => HistoricalRecordModel.fromJson(e)).toList();
    } catch (e) {
      return [];
    }
  }

  Future<List<Map<String, dynamic>>> getRiskMapGrid({
    int leadHours = 96,
    String variable = 'precipitation',
  }) async {
    try {
      final res = await _dio.get('/api/risk/map', queryParameters: {
        'lead_hours': leadHours,
        'variable': variable,
      });
      final List grid = res.data['grid'] ?? [];
      return List<Map<String, dynamic>>.from(grid);
    } catch (e) {
      return [];
    }
  }
}
