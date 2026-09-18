import sys, os, json, random
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv(override=True)
from backend.app.services.canary_service import CanaryRoutingService

print("=== ENV CHECK ===")
print("PRODUCTION_MODEL:", os.environ.get("PRODUCTION_MODEL"))
print("CANARY_ENABLED:", os.environ.get("CANARY_ENABLED"))
print("CANARY_PERCENTAGE:", os.environ.get("CANARY_PERCENTAGE"))
print("MODEL_VERSION_DEFAULT:", os.environ.get("MODEL_VERSION_DEFAULT"))
print("ROLLBACK_MODEL:", os.environ.get("ROLLBACK_MODEL"))

CanaryRoutingService._instance = None
svc = CanaryRoutingService()
t = svc.get_telemetry()
rc = t["routing_configuration"]

print()
print("=== ROUTING CONFIG ===")
print("canary_enabled:", rc.get("canary_enabled"))
print("canary_percentage:", rc.get("canary_percentage"))
print("production_model:", rc.get("production_model"))
print("canary_model:", rc.get("canary_model"))
print("circuit_broken:", rc.get("circuit_broken"))

# Verify: with CANARY_ENABLED=false, route_request should always return production model name
# The method sig is: route_request(req_id, longitude, lead_hours, variable)
random.seed(42)
routed_to_global = 0
routed_to_other = 0
for i in range(100):
    req_id = f"verify-{i:04d}"
    lon = round(random.uniform(68.0, 97.5), 2)
    lead = random.choice([24, 48, 72, 96, 120, 144, 168])
    var = random.choice(["temperature", "wind_speed", "pressure"])
    result = svc.route_request(req_id, lon, lead, var)
    if result == "global_v001":
        routed_to_global += 1
    else:
        routed_to_other += 1

print()
print("=== 100-REQUEST ROUTING SAMPLE ===")
print(f"Routed to global_v001 (production): {routed_to_global}/100")
print(f"Routed to other: {routed_to_other}/100")

# Registry check
with open("models/registry.json") as f:
    reg = json.load(f)

print()
print("=== REGISTRY CHECK ===")
print("registry.production_model:", reg.get("production_model"))
print("model_real_v002 status:", reg.get("model_real_v002", {}).get("status"))
print("global_v001 status:", reg.get("global_v001", {}).get("status"))
print("global_v001 rollback_model:", reg.get("global_v001", {}).get("rollback_model"))
print("global_v001 promoted_at:", reg.get("global_v001", {}).get("promoted_at"))
print("global_v001 cumulative_canary_requests:", reg.get("global_v001", {}).get("cumulative_canary_requests"))
