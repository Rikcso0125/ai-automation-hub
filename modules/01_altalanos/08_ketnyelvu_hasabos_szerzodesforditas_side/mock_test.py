# -*- coding: utf-8 -*-
import json
from handler import run

with open("test_payload.json", "r", encoding="utf-8") as f:
    payload = json.load(f)

config = {
    "company_name": "ProfiTech Hungary Kft.",
    "default_source_lang": "Magyar",
    "default_target_lang": "Angol",
    "governing_language_rule": "A forrásnyelv (Magyar) az irányadó vita esetén",
    "export_formats": "Word (.docx) és PDF mindkettő"
}

print("=== KÉTNYELVŰ HASÁBOS SZERZŐDÉSFORDÍTÁS TESZT ===")
res = run(payload, config)
print(json.dumps(res, indent=2, ensure_ascii=False))
