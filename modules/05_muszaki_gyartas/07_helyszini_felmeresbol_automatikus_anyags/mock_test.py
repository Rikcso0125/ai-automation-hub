# -*- coding: utf-8 -*-
import sys
import os
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from handler import run

def test_survey_materials_and_labor_calc():
    test_payload_path = os.path.join(os.path.dirname(__file__), "test_payload.json")
    with open(test_payload_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    result = run(payload)
    print("Test Result Success:", result.get("success"))
    print("Survey ID:", result.get("survey_id"))

    mat_req = result.get("material_requirements", {})
    mat_cost = mat_req.get("total_materials_cost_net_huf")
    print("Total Materials Prime Cost Net HUF:", mat_cost)
    print("Materials Item Count:", len(mat_req.get("materials_itemized", [])))

    labor = result.get("labor_norm_calculations", {})
    total_hours = labor.get("total_man_hours")
    print("Total Man Hours:", total_hours)
    print("Estimated Working Days:", labor.get("crew_scheduling", {}).get("estimated_working_days"))

    quote = result.get("formal_quotation_and_budget", {})
    fin = quote.get("financial_summary", {})
    print("Final Offer Price Net HUF:", fin.get("final_offer_price_net_huf"))
    print("Final Offer Price Gross HUF:", fin.get("final_offer_price_gross_huf"))
    print("Profit Margin Net HUF:", fin.get("profit_margin_net_huf"))

    assert result.get("success") is True, "Expected success to be True"
    assert mat_cost > 5000000, "Expected materials cost > 5M HUF"
    assert total_hours > 500, "Expected man hours > 500 hours"
    assert fin.get("final_offer_price_net_huf") > 12000000, "Expected offer price > 12M HUF"
    assert "procurement_cart" in quote, "Expected procurement cart"
    print("All assertions passed successfully!")

if __name__ == "__main__":
    test_survey_materials_and_labor_calc()
