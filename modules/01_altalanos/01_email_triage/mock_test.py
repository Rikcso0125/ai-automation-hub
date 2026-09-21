# -*- coding: utf-8 -*-
import json
from handler import run

with open("test_payload.json", "r", encoding="utf-8") as f:
    payload = json.load(f)

config = {
    "company_name": "ProfiVill Kft.",
    "company_knowledge_base": "Kiszállási díj 15.000 Ft, óradíj 12.000 Ft. 2 év garancia.",
    "ai_provider": "mock",
    "reply_tone": "Professzionális és udvarias (Magázó)"
}

print("=== EMAIL TRIAGE TESZT INDÍTÁSA ===")
res = run(payload, config)
print(json.dumps(res, indent=2, ensure_ascii=False))
