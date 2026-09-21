# -*- coding: utf-8 -*-
import os
import json
from handler import run

payload_path = os.path.join(os.path.dirname(__file__), "test_payload.json")
with open(payload_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

config = {
    "company_name": "ProfiTech Klíma & Hőszivattyú Kft.",
    "receptionist_name": "Nikolett (AI Recepciós)",
    "telephony_provider": "Vapi.ai Voice Engine",
    "confirmations_channel": "Először WhatsApp, ha nem elérhető akkor Telnyx SMS (Ajánlott)"
}

print("=== 0-24 VIRTUALIS AI TELEFONOS RECEPCIOS TESZT ===")
res = run(payload, config)
print("Status:", res.get("status"))
print("Hivas ID:", res.get("call_id"))
print("Hivo:", res.get("call_analysis", {}).get("caller_name"), f"({res.get('call_analysis', {}).get('caller_phone')})")
print("Szandek:", res.get("call_analysis", {}).get("intent"))
print("Lefoglalt idopont:", res.get("calendar_booking", {}).get("appointment_time"))
print("Megerosites csatornaja:", res.get("post_call_confirmation", {}).get("channel_used"))
print("Mentes helye:", res.get("saved_transcript_file", {}).get("filename"))
