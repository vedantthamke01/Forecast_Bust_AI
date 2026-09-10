import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ApiClient {
  static const String _prefKeyBaseUrl = 'forecast_bust_base_url';

  /// Production Render Cloud Backend (HTTPS)
  static const String productionApiBaseUrl = 'https://forecast-bust-ai.onrender.com';

  /// Local LAN fallback for optional development only
  static const String devLanIp = '10.238.246.67';
  static const String devLanBaseUrl = 'http://$devLanIp:8000';

  /// Centralized Base URL resolution
  /// In RELEASE mode: permanently uses production Render backend.
  /// In DEBUG mode: defaults to production Render backend, while allowing developer overrides.
  static String get defaultBaseUrl {
    if (kReleaseMode) {
      return productionApiBaseUrl;
    }
    return productionApiBaseUrl;
  }

  late Dio _dio;
  String _baseUrl = defaultBaseUrl;

  String get baseUrl => _baseUrl;
  bool get isProduction => _baseUrl == productionApiBaseUrl;

  ApiClient({String? initialUrl}) {
    _baseUrl = initialUrl ?? defaultBaseUrl;
    _dio = Dio(
      BaseOptions(
        baseUrl: _baseUrl,
        connectTimeout: const Duration(seconds: 45),
        receiveTimeout: const Duration(seconds: 45),
        sendTimeout: const Duration(seconds: 45),
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'User-Agent': 'ForecastBustAI-Flutter/1.0.0',
        },
      ),
    );

    // Add interceptor to retry once if Render free-tier is in cold-start wake-up
    _dio.interceptors.add(
      InterceptorsWrapper(
        onError: (DioException err, handler) async {
          // Detect cold start: connection/receive timeout or Render proxy "no-server" error
          final isColdStartSign = err.type == DioExceptionType.connectionTimeout ||
              err.type == DioExceptionType.receiveTimeout ||
              (err.response?.statusCode == 404 &&
                  err.response?.headers.value('x-render-routing') == 'no-server');

          if (isColdStartSign &&
              err.requestOptions.method.toUpperCase() == 'GET' &&
              err.requestOptions.extra['retried'] != true) {
            err.requestOptions.extra['retried'] = true;
            try {
              // Wait 2.5 seconds for Render container to finish waking up
              await Future.delayed(const Duration(milliseconds: 2500));
              final response = await _dio.fetch(err.requestOptions);
              return handler.resolve(response);
            } catch (_) {
              // If retry also fails, continue with original error
            }
          }
          return handler.next(err);
        },
      ),
    );

    _loadSavedUrl();
  }

  Future<void> _loadSavedUrl() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final saved = prefs.getString(_prefKeyBaseUrl);
      if (saved != null && saved.trim().isNotEmpty) {
        final clean = saved.trim();
        // In Release mode, purge any legacy local LAN / localhost URLs
        final isLocalAddress = clean.contains('10.') ||
            clean.contains('192.168.') ||
            clean.contains('172.16.') ||
            clean.contains('127.0.0.1') ||
            clean.contains('localhost') ||
            clean.contains(':8000');

        if (kReleaseMode && isLocalAddress) {
          // Reset to production and persist
          updateBaseUrl(productionApiBaseUrl);
        } else {
          updateBaseUrl(clean);
        }
      } else if (kReleaseMode) {
        updateBaseUrl(productionApiBaseUrl);
      }
    } catch (_) {}
  }

  void updateBaseUrl(String newUrl) {
    String cleanUrl = newUrl.trim();
    if (!cleanUrl.startsWith('http://') && !cleanUrl.startsWith('https://')) {
      cleanUrl = cleanUrl.contains('onrender.com') ? 'https://$cleanUrl' : 'http://$cleanUrl';
    }
    if (cleanUrl.endsWith('/')) {
      cleanUrl = cleanUrl.substring(0, cleanUrl.length - 1);
    }
    _baseUrl = cleanUrl;
    _dio.options.baseUrl = _baseUrl;

    SharedPreferences.getInstance().then((prefs) {
      prefs.setString(_prefKeyBaseUrl, _baseUrl);
    }).catchError((_) {});
  }

  Future<int?> testConnection([String? customUrl]) async {
    final targetUrl = (customUrl != null && customUrl.trim().isNotEmpty)
        ? (customUrl.trim().startsWith('http')
            ? customUrl.trim()
            : (customUrl.trim().contains('onrender.com')
                ? 'https://${customUrl.trim()}'
                : 'http://${customUrl.trim()}'))
        : _baseUrl;
    final stopwatch = Stopwatch()..start();
    try {
      final testDio = Dio(
        BaseOptions(
          baseUrl: targetUrl.endsWith('/') ? targetUrl.substring(0, targetUrl.length - 1) : targetUrl,
          connectTimeout: const Duration(seconds: 30),
          receiveTimeout: const Duration(seconds: 30),
          headers: {
            'Accept': 'application/json',
            'User-Agent': 'ForecastBustAI-Flutter/1.0.0',
          },
        ),
      );
      final resp = await testDio.get('/health');
      stopwatch.stop();
      if (resp.statusCode == 200) {
        return stopwatch.elapsedMilliseconds;
      }
      return null;
    } catch (_) {
      return null;
    }
  }

  Dio get dio => _dio;
}
