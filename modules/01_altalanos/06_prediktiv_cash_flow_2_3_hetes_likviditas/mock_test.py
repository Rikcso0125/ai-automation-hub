# -*- coding: utf-8 -*-
import json
from handler import run

with open("test_payload.json", "r", encoding="utf-8") as f:
    payload = json.load(f)

config = {
    "company_name": "ProfiTech Hungary Kft.",
    "safety_buffer_huf": "1000000",
    "default_late_payment_adjustment_days": "6",
    "fixed_monthly_salaries_huf": "2800000",
    "salary_due_day": "10",
    "fixed_monthly_taxes_huf": "1200000",
    "tax_due_day": "12",
    "estimated_vat_huf": "950000",
    "vat_due_day": "20",
    "forecast_days": "21",
    "executive_email": "vezeto@profitech.hu"
}

print("=== PREDIKTÍV CASH-FLOW & LIKVIDITÁSI VÉSZJELZŐ TESZT ===")
res = run(payload, config)
print(json.dumps(res, indent=2, ensure_ascii=False))
