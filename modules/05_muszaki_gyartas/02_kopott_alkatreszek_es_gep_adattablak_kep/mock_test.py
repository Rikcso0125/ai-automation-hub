# -*- coding: utf-8 -*-
import sys
import os
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from handler import run

def test_worn_part_vision_id():
    test_payload_path = os.path.join(os.path.dirname(__file__), "test_payload.json")
    with open(test_payload_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    result = run(payload)
    print("Test Result Success:", result.get("success"))
    print("Request ID:", result.get("request_id"))

    best_match = result.get("part_identification", {}).get("best_match", {})
    print("Identified Brand:", best_match.get("brand"))
    print("Identified Part No:", best_match.get("part_number"))
    print("Confidence Score:", best_match.get("confidence_score"))

    exploded = result.get("exploded_view_and_cross_ref", {}).get("exploded_view", {})
    print("Exploded View Diagram:", exploded.get("diagram_name"))
    print("Position Number:", exploded.get("position_number"))

    procurement = result.get("procurement_and_inventory", {})
    rec_part = procurement.get("recommended_part_to_order", {})
    print("Recommended Quick-Fix Part:", rec_part.get("brand"), rec_part.get("part_number"))
    print("Price Net HUF:", rec_part.get("price_net_huf"))
    print("Approval Status:", procurement.get("approval_gate", {}).get("status"))

    assert result.get("success") is True, "Expected success to be True"
    assert best_match.get("part_number") == "196941", "Expected part number 196941"
    assert exploded.get("position_number") == "Pos. 14", "Expected Pos. 14"
    assert len(result.get("exploded_view_and_cross_ref", {}).get("cross_reference_matrix", [])) >= 2, "Expected alternatives"
    print("All assertions passed successfully!")

if __name__ == "__main__":
    test_worn_part_vision_id()
