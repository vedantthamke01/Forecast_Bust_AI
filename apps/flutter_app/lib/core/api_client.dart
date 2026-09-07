import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ApiClient {
  static const String _prefKeyBaseUrl = 'forecast_bust_base_url';

  static const String currentLanIp = '10.238.246.67';

  // Default IP: Pre-configured to current host LAN IP for instant out-of-the-box connectivity
  static String get defaultBaseUrl {
    if (kIsWeb) return 'http://127.0.0.1:8000';
    if (Platform.isAndroid) {
      // Connects directly to host machine over LAN
      return 'http://$currentLanIp:8000';
    }
    return 'http://127.0.0.1:8000';
  }

  late Dio _dio;
  String _baseUrl = defaultBaseUrl;

  String get baseUrl => _baseUrl;

  ApiClient({String? initialUrl}) {
    _baseUrl = initialUrl ?? defaultBaseUrl;
    _dio = Dio(
      BaseOptions(
        baseUrl: _baseUrl,
        connectTimeout: const Duration(seconds: 12),
        receiveTimeout: const Duration(seconds: 12),
        sendTimeout: const Duration(seconds: 12),
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      ),
    );

    _loadSavedUrl();
  }

  Future<void> _loadSavedUrl() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final saved = prefs.getString(_prefKeyBaseUrl);
      if (saved != null && saved.isNotEmpty) {
        updateBaseUrl(saved);
      }
    } catch (_) {}
  }

  void updateBaseUrl(String newUrl) {
    String cleanUrl = newUrl.trim();
    if (!cleanUrl.startsWith('http://') && !cleanUrl.startsWith('https://')) {
      cleanUrl = 'http://$cleanUrl';
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
        ? (customUrl.trim().startsWith('http') ? customUrl.trim() : 'http://${customUrl.trim()}')
        : _baseUrl;
    final stopwatch = Stopwatch()..start();
    try {
      final testDio = Dio(
        BaseOptions(
          baseUrl: targetUrl.endsWith('/') ? targetUrl.substring(0, targetUrl.length - 1) : targetUrl,
          connectTimeout: const Duration(seconds: 6),
          receiveTimeout: const Duration(seconds: 6),
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
