# -*- coding: utf-8 -*-
import os
import json
from handler import run

payload_path = os.path.join(os.path.dirname(__file__), "test_payload.json")
with open(payload_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

config = {
    "company_name": "ProfiTech Szolgáltató Kft.",
    "whatsapp_first": True,
    "contacts_file_path": "data/ugyfelek_kontaktok.json",
    "booking_calendar_url": "https://idopont.profitech.hu/foglalas",
    "inquiry_form_url": "https://igenyfelmero.profitech.hu/gyorskerdes",
    "callback_promise_mins": 25
}

print("=== 1. TESZT: ISMERT VIP ÜGYFÉL HÍVÁSA ===")
res1 = run(payload, config)
print("Status:", res1.get("status"))
print("Válaszidő:", res1.get("turnaround_seconds"), "másodperc")
print("Hívó:", res1.get("caller_details", {}).get("matched_name"), f"({res1.get('caller_details', {}).get('company')})")
print("Csatorna:", res1.get("outbound_dispatch", {}).get("channel_used"))
print("Kiküldött üzenet:", res1.get("outbound_dispatch", {}).get("message_sent"))

print("")
print("=== 2. TESZT: ISMERETLEN UJ ERDEKLODO HIVASA ===")
payload_new = {
    "caller_phone": "+36305559988",
    "call_timestamp": "2026-09-20 01:52:00"
}
res2 = run(payload_new, config)
print("Status:", res2.get("status"))
print("Ismert ügyfél:", res2.get("caller_details", {}).get("is_known_client"))
print("CRM Művelet:", res2.get("crm_integration", {}).get("action"))
print("Kiküldött üzenet:", res2.get("outbound_dispatch", {}).get("message_sent"))
print("Csapat Telegram Riasztás:", res2.get("team_hotline_alert", {}).get("alert_text")[:60] + "...")
