# -*- coding: utf-8 -*-
import os
import json
from handler import run

payload_path = os.path.join(os.path.dirname(__file__), "test_payload.json")
with open(payload_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

config = {
    "executive_name": "Dr. Kovács Béla",
    "input_channels": "Minden csatorna aktív (Webes Mikrofon, Telegram, WhatsApp, Siri)",
    "stt_engine": "Helyi Faster-Whisper (Privát, ingyenes, gépen fut)",
    "enable_voice_feedback_tts": "Igen (Hangos felolvasás / TTS válasz az autó hangszóróira)",
    "calendar_integration": "Google Calendar API",
    "task_management_tool": "ClickUp API"
}

print("=== VEZETOI HANGPARANCS-ASSZISZTENS (JARVIS) TESZT ===")
res = run(payload, config)
print("Status:", res.get("status"))
print("Vezeto:", res.get("executive"))
print("Műveletek száma:", res.get("executed_actions_count"))
for act in res.get("executed_actions", []):
    print(" -> Akcio:", act.get("action_type"), "| Rendszer:", act.get("target_system"))
print("Hangos TTS Valasz:", res.get("tts_voice_feedback", {}).get("spoken_audio_text"))
