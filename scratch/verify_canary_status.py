import os
import sys
import json
sys.path.insert(0, os.path.abspath("."))
from dotenv import load_dotenv
load_dotenv()

from backend.app.services.canary_service import CanaryRoutingService, flush_shadow_executor
from backend.app.services.bust_service import BustPredictionService

def main():
    router = CanaryRoutingService()
    
    # 1. Telemetry
    telemetry = router.get_telemetry()
    print("=== CANARY STATUS & TELEMETRY ===")
    print(json.dumps(telemetry, indent=2))
    
    config = telemetry["routing_configuration"]
    
    assert config["canary_enabled"] is True, "CANARY_ENABLED is not True!"
    assert config["canary_percentage"] == 10.0, "CANARY_PERCENTAGE is not 10.0!"
    assert config["production_model"] == "model_real_v002", "Production model mismatch!"
    assert config["canary_model"] == "global_v001", "Canary model mismatch!"
    assert config["circuit_broken"] is False, "Circuit breaker is tripped!"
    assert config["circuit_break_reason"] is None, f"Break reason: {config['circuit_break_reason']}"
    
    print("\n[PASS] Canary configuration and circuit breaker health verified.")
    
    # 2. Output determinism and equivalence
    test_inputs = [
        {"latitude": 18.52, "longitude": 73.86, "lead_hours": 96, "variable": "precipitation"},
        {"latitude": 28.61, "longitude": 77.20, "lead_hours": 48, "variable": "temperature"},
        {"latitude": 51.50, "longitude": -0.12, "lead_hours": 72, "variable": "wind"},
        {"latitude": -33.86, "longitude": 151.20, "lead_hours": 120, "variable": "pressure"},
        {"latitude": 35.67, "longitude": 139.65, "lead_hours": 24, "variable": "humidity"},
    ]
    
    print("\n=== OUTPUT EQUIVALENCE & DETERMINISM ===")
    for inp in test_inputs:
        r1 = router.predict_risk(**inp)
        r2 = router.predict_risk(**inp)
        flush_shadow_executor()
        assert r1["bust_probability"] == r2["bust_probability"], "Probability mismatch!"
        assert r1["risk_level"] == r2["risk_level"], "Risk level mismatch!"
        assert r1["reliability_score"] == r2["reliability_score"], "Reliability mismatch!"
        assert r1["explanation"]["all_factors"] == r2["explanation"]["all_factors"], "SHAP explanation mismatch!"
        print(f"Input: {inp['variable']} @ ({inp['latitude']}, {inp['longitude']}), {inp['lead_hours']}h -> Model: {r1['model_version']}, Prob: {r1['bust_probability']:.4f}, Risk: {r1['risk_level']}, Rel: {r1['reliability_score']:.3f}")
    
    print("\n[PASS] Determinism, risk category, reliability score, and SHAP explanations verified identical.")
    
    # 3. Direct global_v001 bundle test
    print("\n=== DIRECT GLOBAL_V001 DETERMINISM & INTEGRITY ===")
    direct_canary = router.canary_service
    for inp in test_inputs:
        c1 = direct_canary.predict_risk(**inp)
        c2 = direct_canary.predict_risk(**inp)
        assert c1["bust_probability"] == c2["bust_probability"]
        assert c1["risk_level"] == c2["risk_level"]
        assert c1["reliability_score"] == c2["reliability_score"]
        assert 0.0 <= c1["bust_probability"] <= 1.0
        print(f"Direct global_v001 -> Prob: {c1['bust_probability']:.4f}, Risk: {c1['risk_level']}, Rel: {c1['reliability_score']:.3f}")
    
    print("\n[PASS] Direct global_v001 predictions verified healthy and bounded.")

if __name__ == "__main__":
    main()
