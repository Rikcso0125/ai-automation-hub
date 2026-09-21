# -*- coding: utf-8 -*-
import os
import json
from handler import run

payload_path = os.path.join(os.path.dirname(__file__), "test_payload.json")
with open(payload_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

config = {
    "company_name": "ProfiTech Szolgáltató Kft.",
    "buffer_time_minutes": 30,
    "meeting_duration_minutes": 45,
    "calendar_system": "Google Calendar API",
    "staff_assignment_mode": "Automatikus Round-Robin (Egyenletes elosztás)",
    "require_reschedule_confirmation": True
}

print("=== 1. TESZT: ÚJ IDŐPONTFOGLALÁSI KÉRÉS ===")
res1 = run(payload, config)
print("Status:", res1.get("status"))
print("Szándék:", res1.get("conversation_intent"))
print("Felajánlott sávok száma:", len(res1.get("offered_slots", [])))
print("Pufferidő:", res1.get("calendar_sync", {}).get("travel_buffer"))
print("Bot válasz:")
print(res1.get("bot_response"))

print("")
print("=== 2. TESZT: IDŐPONT MÓDOSÍTÁS MEGERŐSÍTÉSSEL ===")
resched_payload = {
    "channel": "whatsapp",
    "user_message": "Szia, mégse jó a kedd délután, át tudjuk tenni csütörtökre?",
    "user_profile": {"name": "Balogh Dániel", "email": "daniel.balogh@ceg.hu"},
    "existing_booking_id": "BOOK-2026-9410"
}
res2 = run(resched_payload, config)
print("Status:", res2.get("status"))
print("Foglalási státusz:", res2.get("booking_status"))
print("Vár ügyféli megerősítésre:", res2.get("requires_client_confirmation"))
print("Bot válasz:")
print(res2.get("bot_response"))
