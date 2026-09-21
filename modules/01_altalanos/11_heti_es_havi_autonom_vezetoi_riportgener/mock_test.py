# -*- coding: utf-8 -*-
import os
import json
from handler import run

payload_path = os.path.join(os.path.dirname(__file__), "test_payload.json")
with open(payload_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

config = {
    "company_name": "ProfiTech Ipari & Kereskedelmi Kft.",
    "report_period": "Heti Vezetői Riport (Minden hétfő 07:00)",
    "executive_email_recipients": "ugyvezetes@profitech.hu, penzugy@profitech.hu"
}

print("=== HETI ES HAVI AUTONOM VEZETOI RIPORT TESZT ===")
res = run(payload, config)
print("Status:", res.get("status"))
print("Ceg:", res.get("company_name"))
print("Idoszak:", res.get("report_period"))
print("Arbevetel:", res.get("kpi_summary", {}).get("invoiced_revenue"))
print("Zaro Cash:", res.get("kpi_summary", {}).get("closing_cash"))
print("PDF fajl:", res.get("generated_files", {}).get("pdf_report"))
print("DOCX fajl:", res.get("generated_files", {}).get("docx_report"))
print("Aktiv akciótervek szama:", len(res.get("executive_insights", {}).get("action_plan", [])))
