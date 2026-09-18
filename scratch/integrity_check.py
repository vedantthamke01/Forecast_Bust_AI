import sys, os
sys.path.insert(0, os.path.abspath('.'))
from dotenv import load_dotenv
load_dotenv(override=True)
from backend.app.services.canary_service import CanaryRoutingService, flush_shadow_executor

CanaryRoutingService._instance = None
router = CanaryRoutingService()

test_inputs = [
    {'latitude': 18.52,  'longitude': 73.86,   'lead_hours': 96,  'variable': 'precipitation'},
    {'latitude': 51.50,  'longitude': -0.12,   'lead_hours': 72,  'variable': 'wind'},
    {'latitude': -33.86, 'longitude': 151.20,  'lead_hours': 120, 'variable': 'pressure'},
    {'latitude': 35.67,  'longitude': 139.65,  'lead_hours': 24,  'variable': 'humidity'},
    {'latitude': -26.20, 'longitude': 28.04,   'lead_hours': 168, 'variable': 'temperature'},
]

print('=== MODEL INTEGRITY & DETERMINISM CHECK ===')
all_ok = True
for inp in test_inputs:
    r1 = router.predict_risk(**inp)
    r2 = router.predict_risk(**inp)
    flush_shadow_executor()
    prob = r1['bust_probability']
    rel  = r1['reliability_score']
    complement_ok = abs(rel - (1.0 - prob)) < 0.002
    det_ok = r1['bust_probability'] == r2['bust_probability']
    bounds_ok = 0.0 <= prob <= 1.0
    schema_ok = all(k in r1 for k in ['bust_probability','reliability_score','risk_level','model_version','explanation'])
    shap_ok = isinstance(r1.get('explanation', {}).get('all_factors', None), list)
    if not (complement_ok and det_ok and bounds_ok and schema_ok):
        all_ok = False
    print(f"  {inp['variable']:15s} ({inp['latitude']:7.2f},{inp['longitude']:8.2f}) {inp['lead_hours']:3d}h => model={r1['model_version']:20s} prob={prob:.4f} rel={rel:.4f} complement_ok={complement_ok} det={det_ok} bounds={bounds_ok} schema={schema_ok} shap={shap_ok}")

print()
if all_ok:
    print('[PASS] All integrity checks passed.')
else:
    print('[FAIL] One or more integrity checks failed!')
