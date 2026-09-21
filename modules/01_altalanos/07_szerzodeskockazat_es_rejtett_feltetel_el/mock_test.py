# -*- coding: utf-8 -*-
import json
from handler import run

with open("test_payload.json", "r", encoding="utf-8") as f:
    payload = json.load(f)

config = {
    "company_name": "ProfiTech Hungary Kft.",
    "company_role": "Vállalkozó / Szállító / Szolgáltató (Megbízott)",
    "max_penalty_cap_percent": "10",
    "notification_email": "jogi@profitech.hu"
}

print("=== SZERZŐDÉSKOCKÁZAT & RED-FLAG AUDIT TESZT ===")
res = run(payload, config)
print(json.dumps(res, indent=2, ensure_ascii=False))
