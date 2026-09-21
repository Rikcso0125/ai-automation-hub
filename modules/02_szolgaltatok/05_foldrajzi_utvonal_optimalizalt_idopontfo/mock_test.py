# -*- coding: utf-8 -*-
import os
import json
from handler import run

payload_path = os.path.join(os.path.dirname(__file__), "test_payload.json")
with open(payload_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

config = {
    "company_name": "ProfiTech Klíma & Gázkészülék Szerviz",
    "emergency_out_of_zone_surcharge_huf": 15000,
    "allow_emergency_booking": True,
    "planning_horizon_days": 1
}

print("=== 1. TESZT: ÜGYFÉL CÍM ALAPJÁN ZÓNÁS IDŐPONT-FELAJÁNLÁS ===")
res1 = run(payload, config)
print("Status:", res1.get("status"))
print("Cím:", res1.get("input_address"))
print("Felismerve:", res1.get("detected_zone", {}).get("zone_name"))
print("Ajánlott napok:", res1.get("detected_zone", {}).get("standard_service_days"))
print("Sürgősségi felár opció:", res1.get("booking_proposals", {}).get("emergency_slots", [{}])[0].get("badge"))

print("")
print("=== 2. TESZT: NAPI WAZE & GOOGLE MAPS MENETREND EXPORT ===")
dispatch_payload = {
    "action": "GENERATE_DAILY_DISPATCH_ROUTE",
    "target_date": "2026-09-22"
}
res2 = run(dispatch_payload, config)
print("Status:", res2.get("status"))
print("Tervezési ablak:", res2.get("planning_metadata", {}).get("planning_horizon_applied"))
print("Megspórolt menetidő:", res2.get("route_optimization_stats", {}).get("saved_travel_time_minutes"), "perc")
print("Megspórolt üzemanyag:", res2.get("route_optimization_stats", {}).get("saved_fuel_cost_huf"), "Ft")
print("Google Maps link:", res2.get("navigation_links", {}).get("google_maps_turn_by_turn")[:70] + "...")
print("Waze link:", res2.get("navigation_links", {}).get("waze_first_destination"))
