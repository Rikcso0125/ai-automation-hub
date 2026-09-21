# -*- coding: utf-8 -*-
import os
import json
from handler import run

payload_path = os.path.join(os.path.dirname(__file__), "test_payload.json")
with open(payload_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

config = {
    "company_name": "ProfiTech Ipari & Kereskedelmi Kft.",
    "company_email_domain": "profitech.hu",
    "default_workspace_system": "Google Workspace (Gmail, Drive, Meet)",
    "communication_tool": "Slack Workspace",
    "pm_system": "ClickUp",
    "cloud_storage": "Google Drive Shared Drive",
    "hr_manager_email": "hr@profitech.hu",
    "it_support_email": "it@profitech.hu"
}

print("=== ZERO-TOUCH ONBOARDING AUTOPILOT TESZT ===")
res = run(payload, config)
print("Status:", res.get("status"))
print("Munkatars:", res.get("employee_summary", {}).get("name"))
print("Ceges Email:", res.get("employee_summary", {}).get("company_email"))
print("PDF Szerzodes:", res.get("generated_documents", {}).get("pdf_filename"))
print("DOCX Szerzodes:", res.get("generated_documents", {}).get("docx_filename"))
print("IT Rendszerek:", res.get("provisioning", {}).get("systems_count"))
print("Drip Fazisok:", res.get("drip_schedule", {}).get("total_phases"))
