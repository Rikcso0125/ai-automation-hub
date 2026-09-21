# -*- coding: utf-8 -*-
import os
import json
from handler import run

payload_path = os.path.join(os.path.dirname(__file__), "test_payload.json")
with open(payload_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

config = {
    "company_name": "ProfiTech Ipari & Kereskedelmi Kft.",
    "approval_threshold_huf": 25000,
    "manager_approval_email": "ugyvezetes@profitech.hu",
    "accounting_system_export": "Könyvelői CSV / Excel Összesítő"
}

print("=== CEGES KOLTSEGELSZAMOLAS & BLOKK-FELDOLGOZAS TESZT ===")
res = run(payload, config)
print("Status:", res.get("status"))
print("Feldolgozasi ido:", res.get("processing_time_sec"), "mp")
print("Kereskedo:", res.get("receipt_data", {}).get("merchant"))
print("Brutto osszeg:", res.get("receipt_data", {}).get("gross_huf"), "Ft")
print("Kategoria:", res.get("categorization", {}).get("assigned_category"))
print("Indoklas:", res.get("categorization", {}).get("category_reasoning"))
print("Bankkartya parositas:", res.get("bank_card_matching", {}).get("matched"))
print("Jovahagyasi statusz:", res.get("approval_rule", {}).get("status"))
print("Jovahagyasi uzenet:", res.get("approval_rule", {}).get("message"))
print("CSV fajl:", res.get("accounting_export", {}).get("csv_file_path"))
