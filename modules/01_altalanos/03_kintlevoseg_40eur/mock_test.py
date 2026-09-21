# -*- coding: utf-8 -*-
import json
from handler import run

with open("test_payload.json", "r", encoding="utf-8") as f:
    payload = json.load(f)

config = {
    "company_name": "ProfiTech Hungary Kft.",
    "company_bank_account": "11705008-20495812-00000000",
    "email_provider": "resend",
    "sms_provider": "telnyx",
    "payment_gateway": "billingo",
    "grace_period_days": "15",
    "eur_huf_rate": "400"
}

print("=== KINTLÉVŐSÉG ÉS 40 EUR BEHAJTÁSI LÁNC TESZT ===")
res = run(payload, config)
print(json.dumps(res, indent=2, ensure_ascii=False))
