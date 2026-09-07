import 'dart:convert';
import 'package:geolocator/geolocator.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../core/constants.dart';
import '../models/weather_models.dart';
import 'api_service.dart';

class LocationService {
  static const String _prefKeyLastLocation = 'forecast_bust_last_location';
  final ApiService apiService;

  LocationService({required this.apiService});

  Future<LocationModel> getInitialLocation() async {
    // 1. Check saved location first
    final saved = await getLastSavedLocation();
    if (saved != null) {
      // In background try to update with GPS
      return saved;
    }

    // 2. Try GPS
    final gpsLoc = await getCurrentGpsLocation();
    if (gpsLoc != null) {
      await saveLocation(gpsLoc);
      return gpsLoc;
    }

    // 3. Fallback to Nagpur
    const fallback = LocationModel(
      name: AppConstants.defaultCity,
      state: AppConstants.defaultState,
      country: 'India',
      latitude: AppConstants.defaultLat,
      longitude: AppConstants.defaultLon,
    );
    await saveLocation(fallback);
    return fallback;
  }

  Future<LocationModel?> getCurrentGpsLocation() async {
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        return null;
      }

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          return null;
        }
      }

      if (permission == LocationPermission.deniedForever) {
        return null;
      }

      final position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.medium,
        timeLimit: const Duration(seconds: 8),
      );

      final rev = await apiService.reverseGeocode(position.latitude, position.longitude);
      if (rev != null) {
        return rev;
      }

      return LocationModel(
        name: '${position.latitude.toStringAsFixed(2)}°N',
        state: '${position.longitude.toStringAsFixed(2)}°E',
        country: 'India',
        latitude: position.latitude,
        longitude: position.longitude,
      );
    } catch (_) {
      return null;
    }
  }

  Future<LocationModel?> getLastSavedLocation() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final str = prefs.getString(_prefKeyLastLocation);
      if (str != null) {
        return LocationModel.fromJson(jsonDecode(str) as Map<String, dynamic>);
      }
    } catch (_) {}
    return null;
  }

  Future<void> saveLocation(LocationModel location) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_prefKeyLastLocation, jsonEncode(location.toJson()));
    } catch (_) {}
  }
}
