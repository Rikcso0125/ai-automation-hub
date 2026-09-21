# -*- coding: utf-8 -*-
import os
import json
from handler import run

payload_path = os.path.join(os.path.dirname(__file__), "test_payload.json")
with open(payload_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

config = {
    "enabled_self_healing_strategies": "Mindhárom stratégia aktív (Retry 3x, Failover Fallback, Dead-Letter Queue)",
    "alert_channels": "Mindkét csatorna (Telegram Bot & Admin Email)",
    "admin_alert_email": "admin@profitech.hu",
    "telegram_alert_chat_id": "@profitech_hub_alerts"
}

print("=== ONJAVITO MUNKA FOLYAMAT-FELUGYELET (WATCHDOG) TESZT ===")
res = run(payload, config)
print("Status:", res.get("status"))
print("Watchdog akcio:", res.get("watchdog_action"))
print("Onjavitas sikeres:", res.get("self_healing_execution", {}).get("is_healed"))
print("Onjavitas osszefoglalo:", res.get("self_healing_execution", {}).get("summary"))
print("Hub Rendelkezesre allas:", res.get("system_health_report", {}).get("overall_uptime_pct"), "%")
print("1-Kattintasos link:", res.get("one_click_fix", {}).get("action_url"))
