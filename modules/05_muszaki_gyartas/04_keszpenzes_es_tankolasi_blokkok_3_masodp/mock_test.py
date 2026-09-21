# -*- coding: utf-8 -*-
import sys
import os
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from handler import run

def test_field_receipt_processing():
    test_payload_path = os.path.join(os.path.dirname(__file__), "test_payload.json")
    with open(test_payload_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    result = run(payload)
    print("Test Result Success:", result.get("success"))
    print("Claim ID:", result.get("expense_claim_id"))

    rec_data = result.get("extracted_receipt_data", {})
    fin = rec_data.get("financial_summary", {})
    print("Grand Total Gross HUF:", fin.get("grand_total_gross_huf"))
    print("Grand Total VAT HUF:", fin.get("grand_total_vat_huf"))

    fuel = rec_data.get("fuel_breakdown", {})
    print("Fuel Liters:", fuel.get("quantity_liters"))
    print("Recognized Plate:", fuel.get("recognized_license_plate"))
    print("Odometer Reading:", fuel.get("odometer_km"))

    proj = result.get("project_allocation", {})
    print("Allocated Project:", proj.get("matched_project_code"))
    print("Budget Status:", proj.get("budget_impact", {}).get("budget_status"))

    accounting = result.get("accounting_and_approval", {})
    appr_gate = accounting.get("approval_gate", {})
    print("Approval Status:", appr_gate.get("status"))
    print("Requires Director Approval:", appr_gate.get("requires_director_approval"))

    assert result.get("success") is True, "Expected success to be True"
    assert fin.get("grand_total_gross_huf") == 60490, "Expected 60490 HUF total"
    assert proj.get("matched_project_code") == "PRJ-2026-AUDI-G3", "Expected Audi G3 project match"
    assert appr_gate.get("requires_director_approval") is True, "Expected director approval required"
    print("All assertions passed successfully!")

if __name__ == "__main__":
    test_field_receipt_processing()
