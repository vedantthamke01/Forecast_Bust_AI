import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:forecast_bust_detection/core/constants.dart';
import 'package:forecast_bust_detection/core/api_client.dart';
import 'package:forecast_bust_detection/models/weather_models.dart';
import 'package:forecast_bust_detection/models/risk_models.dart';
import 'package:forecast_bust_detection/models/verification_models.dart';
import 'package:forecast_bust_detection/models/advanced_models.dart';
import 'package:forecast_bust_detection/main.dart';

void main() {
  group('Data Models & JSON Deserialization', () {
    test('CurrentWeather parses correctly from authentic API response', () {
      final json = {
        'location': {'latitude': 21.1458, 'longitude': 79.0882},
        'observation_time': '2026-09-07T00:00:00Z',
        'temperature_c': 25.4,
        'precipitation_mm': 0.0,
        'wind_speed_mps': 7.2,
        'pressure_hpa': 1013.2,
        'humidity_percent': 83.0,
        'cloud_cover_percent': 10.0,
        'provider': 'Open-Meteo',
        'model': 'ECMWF IFS',
      };

      final weather = CurrentWeather.fromJson(json);
      expect(weather.temperatureC, 25.4);
      expect(weather.precipitationMm, 0.0);
      expect(weather.windSpeedMps, 7.2);
      expect(weather.humidityPercent, 83.0);
      expect(weather.conditionText, 'Clear Sky');
      expect(weather.provider, 'Open-Meteo');
    });

    test('RiskPrediction parses correctly with TreeSHAP feature attributions', () {
      final json = {
        'latitude': 21.1458,
        'longitude': 79.0882,
        'lead_hours': 96,
        'lead_time_days': 4,
        'variable': 'precipitation',
        'forecast_value': 0.0,
        'threshold_criteria': '> 10.0mm absolute error',
        'bust_probability': 0.007,
        'bust_probability_percentage': '0.7%',
        'reliability_score': 0.993,
        'reliability_score_percentage': '99.3%',
        'risk_level': 'LOW',
        'risk_badge': '🟢 LOW',
        'forecast_source': 'ECMWF IFS (Operational NWP)',
        'explanation': {
          'summary_text': 'Statistical TreeSHAP model indicates low bust likelihood.',
          'top_amplifiers': [],
          'top_mitigators': [
            {
              'feature': 'ensemble_spread',
              'attribution': -0.15,
              'raw_value': 1.2,
            }
          ],
          'all_factors': [
            {
              'feature': 'ensemble_spread',
              'attribution': -0.15,
              'raw_value': 1.2,
            }
          ],
          'causality_disclaimer': 'SHAP represents model attribution, not physical causation.'
        }
      };

      final risk = RiskPrediction.fromJson(json);
      expect(risk.leadHours, 96);
      expect(risk.bustProbability, 0.007);
      expect(risk.reliabilityScore, 0.993);
      expect(risk.riskLevel, 'LOW');
      expect(risk.explanation, isNotNull);
      expect(risk.explanation!.topMitigators.length, 1);
      expect(risk.explanation!.topMitigators.first.feature, 'ensemble_spread');
    });

    test('HistoricalVerification parses ERA5 comparison records', () {
      final json = {
        'location': {'latitude': 21.1458, 'longitude': 79.0882},
        'sample_size': 10,
        'bust_count': 1,
        'historical_bust_rate_percentage': 10.0,
        'average_error': 0.8,
        'records': [
          {
            'forecast_id': 'fc_001',
            'lead_hours': 24,
            'valid_time': '2026-07-10T00:00:00Z',
            'forecast_value': 0.0,
            'reference_value': 0.0,
            'absolute_error': 0.0,
            'is_bust': false,
            'status': 'VERIFIED'
          }
        ]
      };

      final hist = HistoricalVerification.fromJson(json);
      expect(hist.sampleSize, 10);
      expect(hist.bustCount, 1);
      expect(hist.bustRatePercentage, 10.0);
      expect(hist.records.length, 1);
      expect(hist.records.first.status, 'VERIFIED');
      expect(hist.records.first.isBust, false);
    });

    test('ModelEvaluation parses scientific metrics accurately', () {
      final json = {
        'model_version': 'model_real_v002',
        'data_type': 'REAL',
        'dataset_version': 'dataset_real_v002',
        'algorithm': 'LightGBM + Isotonic Calibration',
        'metrics': {
          'pr_auc': 0.2682,
          'roc_auc': 0.8756,
          'brier_score': 0.0450,
          'ece': 0.0257,
          'total_records': 37800
        },
        'acceptance_gate': {'status': 'PASSED'}
      };

      final eval = ModelEvaluation.fromJson(json);
      expect(eval.modelVersion, 'model_real_v002');
      expect(eval.dataType, 'REAL');
      expect(eval.prAuc, 0.2682);
      expect(eval.rocAuc, 0.8756);
      expect(eval.brierScore, 0.0450);
      expect(eval.ece, 0.0257);
      expect(eval.totalRecords, 37800);
      expect(eval.acceptanceStatus, 'PASSED');
    });

    test('Risk severity color mapping', () {
      expect(AppColors.forRiskLevel('LOW'), AppColors.green);
      expect(AppColors.forRiskLevel('MODERATE'), AppColors.amber);
      expect(AppColors.forRiskLevel('HIGH'), AppColors.orange);
      expect(AppColors.forRiskLevel('VERY HIGH'), AppColors.red);
    });
  });

  group('UI Widget Tests', () {
    testWidgets('ForecastBustApp renders navigation bar with 4 tabs', (WidgetTester tester) async {
      await tester.pumpWidget(const ProviderScope(child: ForecastBustApp()));
      await tester.pumpAndSettle();

      expect(find.text('Forecast Bust AI'), findsOneWidget);
      expect(find.text('Reliability Intelligence · Days 3–10'), findsOneWidget);

      // Verify 4 tabs in bottom navigation
      expect(find.text('Home'), findsOneWidget);
      expect(find.text('Risk Map'), findsOneWidget);
      expect(find.text('Verify'), findsOneWidget);
      expect(find.text('Advanced'), findsOneWidget);
    });

    test('ApiClient defaults to Render HTTPS production backend', () {
      expect(ApiClient.productionApiBaseUrl, 'https://forecast-bust-ai.onrender.com');
      expect(ApiClient.defaultBaseUrl, 'https://forecast-bust-ai.onrender.com');
      final client = ApiClient();
      expect(client.baseUrl, 'https://forecast-bust-ai.onrender.com');
      expect(client.isProduction, true);
    });
  });
}
