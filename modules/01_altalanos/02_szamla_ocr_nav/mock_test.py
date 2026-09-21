# -*- coding: utf-8 -*-
import json
from handler import run

with open("test_payload.json", "r", encoding="utf-8") as f:
    payload = json.load(f)

config = {
    "ocr_provider": "mock",
    "company_tax_number": "12345678-2-41",
    "billing_system": "billingo",
    "approval_limit_huf": "250000"
}

print("=== SZÁMLA OCR & NAV ELLENŐRZÉS TESZT ===")
res = run(payload, config)
print(json.dumps(res, indent=2, ensure_ascii=False))
