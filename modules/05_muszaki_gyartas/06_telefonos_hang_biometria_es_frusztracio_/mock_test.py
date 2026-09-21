# -*- coding: utf-8 -*-
import sys
import os
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from handler import run

def test_voice_biometrics_and_frustration():
    test_payload_path = os.path.join(os.path.dirname(__file__), "test_payload.json")
    with open(test_payload_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    result = run(payload)
    print("Test Result Success:", result.get("success"))
    print("Call ID:", result.get("call_id"))

    stress = result.get("stress_analysis", {})
    f_index = stress.get("combined_frustration_index_pct")
    print("Combined Frustration Index Pct:", f_index)
    print("Is Critical Frustration:", stress.get("is_critical_frustration"))

    ident = result.get("customer_identification", {}).get("identified_customer", {})
    print("Identified Customer:", ident.get("name"), ident.get("company"))
    print("Contractual SLA:", ident.get("contractual_sla_hours"), "hours")

    escalation = result.get("escalation_details", {})
    print("Is Escalated to Chief Engineer:", escalation.get("is_escalated_to_chief_engineer"))
    print("Target Engineer:", escalation.get("target_engineer"))
    print("Whisper Coach Audio Text:", escalation.get("whisper_coach_audio_text"))

    assert result.get("success") is True, "Expected success to be True"
    assert f_index >= 75.0, "Expected critical frustration >= 75%"
    assert escalation.get("is_escalated_to_chief_engineer") is True, "Expected escalation to be True"
    assert "whisper_coach_audio_text" in escalation, "Expected whisper coach audio text"
    print("All assertions passed successfully!")

if __name__ == "__main__":
    test_voice_biometrics_and_frustration()
