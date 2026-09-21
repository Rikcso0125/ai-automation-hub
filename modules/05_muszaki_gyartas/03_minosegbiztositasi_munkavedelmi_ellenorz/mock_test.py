# -*- coding: utf-8 -*-
import sys
import os
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from handler import run

def test_quality_and_safety_audit():
    test_payload_path = os.path.join(os.path.dirname(__file__), "test_payload.json")
    with open(test_payload_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    result = run(payload)
    print("Test Result Success:", result.get("success"))
    print("Audit ID:", result.get("audit_id"))

    findings = result.get("visual_audit_findings", {})
    print("Compliance Score Pct:", findings.get("compliance_score_pct"))
    print("Non-Compliant Count:", findings.get("non_compliant_count"))

    risk_eval = result.get("regulatory_risk_evaluation", {})
    stop_work = risk_eval.get("stop_work_order", {})
    print("Stop Work Issued:", stop_work.get("issued"))
    print("Stop Work Order Code:", stop_work.get("order_code"))
    print("Penalty Exposure Avg HUF:", risk_eval.get("total_penalty_exposure_huf", {}).get("average_expected_huf"))

    remediation = result.get("remediation_workflow", {})
    print("Action Tickets Count:", len(remediation.get("action_tickets", [])))
    print("Verification Gate URL:", remediation.get("photo_verification_gate_url"))

    assert result.get("success") is True, "Expected success to be True"
    assert stop_work.get("issued") is True, "Expected Stop Work order to be issued"
    assert findings.get("non_compliant_count") >= 2, "Expected at least 2 non-compliant findings"
    assert "e_naplo_official_entry" in remediation, "e-Napló entry must be generated"
    print("All assertions passed successfully!")

if __name__ == "__main__":
    test_quality_and_safety_audit()
