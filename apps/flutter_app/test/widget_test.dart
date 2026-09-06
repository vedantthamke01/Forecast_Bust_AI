import 'package:flutter_test/flutter_test.dart';
import 'package:forecast_bust_detection/core/constants.dart';
import 'package:forecast_bust_detection/models/risk_models.dart';

void main() {
  test('PredictionRiskModel parses correctly from JSON', () {
    final mockJson = {
      'location': {'latitude': 18.5204, 'longitude': 73.8567},
      'forecast_horizon_hours': 96,
      'forecast_day': 4,
      'variable': 'precipitation',
      'forecast_value': 42.0,
      'bust_probability': 0.78,
      'reliability_score': 0.22,
      'risk_level': 'HIGH',
      'risk_badge': '🟠 HIGH',
      'model_version': 'model_v001',
      'explanation': {
        'all_factors': [
          {
            'feature': 'ensemble_spread',
            'description': 'NWP Ensemble Spread (3.80σ)',
            'actual_value': 3.8,
            'shap_value': 0.32,
            'impact': 'AMPLIFIER'
          }
        ],
        'summary_text': 'Elevated bust risk.'
      }
    };

    final model = PredictionRiskModel.fromJson(mockJson);
    expect(model.leadHours, 96);
    expect(model.leadDay, 4);
    expect(model.bustProbability, 0.78);
    expect(model.reliabilityScore, 0.22);
    expect(model.riskLevel, 'HIGH');
    expect(model.shapFactors.length, 1);
    expect(model.shapFactors.first.impact, 'AMPLIFIER');
  });

  test('Scientific disclaimer is strictly defined', () {
    expect(AppConstants.scientificDisclaimer, contains('NCMRWF'));
    expect(AppConstants.scientificDisclaimer, contains('IMD'));
  });
}
