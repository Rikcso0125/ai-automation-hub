# -*- coding: utf-8 -*-
import os
import json
from handler import run

payload_path = os.path.join(os.path.dirname(__file__), "test_payload.json")
with open(payload_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

config = {
    "company_name": "DentArt Prémium Fogászat & Implantológia",
    "waitlist_blast_size": 3,
    "require_deposit_on_repeat_noshow": True,
    "deposit_amount_huf": 10000,
    "admin_dashboard_alert_enabled": True
}

print("=== 1. TESZT: LEMONDÁS & VÁRÓLISTA VILLÁM-ÚJRATÖLTÉS ===")
res1 = run(payload, config)
print("Status:", res1.get("status"))
print("Esemény:", res1.get("event_handled"))
print("Kiértesített várólistások száma:", res1.get("waitlist_automation", {}).get("candidates_notified_count"))
print("Új foglaló:", res1.get("waitlist_automation", {}).get("flash_claim_result", {}).get("claimed_by"))
print("Mentett bevétel:", res1.get("waitlist_automation", {}).get("flash_claim_result", {}).get("revenue_saved_huf"), "Ft")
print("Admin jelzés:", res1.get("admin_panel_notice", {}).get("badge"))

print("")
print("=== 2. TESZT: NO-SHOW ESEMENY & ELOLEG KOTELEZETTSEG ===")
noshow_payload = {
    "event_type": "NO_SHOW_OCCURRED",
    "no_show_client": {
        "client_name": "Molnár Tibor",
        "phone": "+36306667788",
        "previous_no_shows": 1
    }
}
res2 = run(noshow_payload, config)
print("Status:", res2.get("status"))
print("CRM Címke:", res2.get("client_profile_updated", {}).get("crm_tag"))
print("Kötelező előleg:", res2.get("client_profile_updated", {}).get("deposit_required_for_future"))
print("Előleg összege:", res2.get("client_profile_updated", {}).get("deposit_amount_huf"), "Ft")
print("Stripe fizetési link:", res2.get("client_profile_updated", {}).get("stripe_deposit_link"))
print("Admin riasztás:", res2.get("admin_dashboard_alert", {}).get("badge"))
