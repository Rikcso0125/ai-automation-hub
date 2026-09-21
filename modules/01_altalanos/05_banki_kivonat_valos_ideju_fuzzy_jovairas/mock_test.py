# -*- coding: utf-8 -*-
import json
from handler import run

with open("test_payload.json", "r", encoding="utf-8") as f:
    payload = json.load(f)

config = {
    "bank_source_type": "Billingo Bankszinkron API",
    "bank_name": "OTP Bank",
    "confidence_threshold_percent": "85",
    "partial_payment_handling": "Részfizetés rögzítése + Köszönőlevél a fennmaradó összeggel",
    "stop_dunning_on_match": "Igen (Azonnal leállítja a felszólításokat)",
    "alert_email": "penzugy@cegem.hu"
}

print("=== BANKI FUZZY JÓVÁÍRÁS-PÁROSÍTÁS TESZT ===")
res = run(payload, config)
print(json.dumps(res, indent=2, ensure_ascii=False))
