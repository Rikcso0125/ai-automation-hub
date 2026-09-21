# -*- coding: utf-8 -*-
import sys
import os
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from handler import run

def test_voice_field_report():
    test_payload_path = os.path.join(os.path.dirname(__file__), "test_payload.json")
    with open(test_payload_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    result = run(payload)
    print("Test Result Success:", result.get("success"))
    print("Report ID:", result.get("report_id"))
    print("Project Name:", result.get("project_name"))
    print("Total Hours:", result.get("extracted_entities", {}).get("total_hours"))
    print("Total Cost HUF:", result.get("cost_summary", {}).get("total_cost_huf"))
    print("e-Napló Formatted:", "e_epitesi_naplo_entry" in result)
    print("Approval Status:", result.get("approval_status"))

    assert result.get("success") is True, "Expected success to be True"
    assert result.get("report_id") is not None, "Report ID must be present"
    assert "e_epitesi_naplo_entry" in result, "e-Építési napló entry missing"
    assert "internal_work_order" in result, "Internal work order missing"
    print("All assertions passed successfully!")

if __name__ == "__main__":
    test_voice_field_report()
