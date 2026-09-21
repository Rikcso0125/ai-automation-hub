"""
Mock teszt a 15_alvo_ugyfelbazis_ujraaktivalo_sprint_sms modulhoz.
Teszteli az alvó ügyfél szegmentációt, a várható bevételkalkulációt,
a Drip kapacitásvédelmet és a kétirányú interaktív ügyfélválasz feldolgozást.
"""

import os
import sys
import json

curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, curr_dir)
from handler import run

def test_dormant_reactivation():
    print("=== 1. TESZT: ALVÓ BÁZIS FELMÉRÉSE, BEVÉTELKALKULÁCIÓ & DRIP KAMPÁNY ===")
    payload_prep = {
        "action": "PREPARE_REACTIVATION_CAMPAIGN",
        "campaign_name": "Őszi Fűtésfelkészítő Sprint 2026",
        "target_service": "Éves Garanciamegőrző Karbantartás",
        "custom_inactivity_days": 180,
        "sample_dormant_clients": [
            {"id": "CL-101", "name": "Kovács Béla", "phone": "+36301234567", "last_service_date": "2025-10-15"},
            {"id": "CL-102", "name": "Tóth Gábor", "phone": "+36709876543", "last_service_date": "2025-11-20"},
            {"id": "CL-103", "name": "Molnár Zsuzsanna", "phone": "+36204567890", "last_service_date": "2025-08-10"},
            {"id": "CL-104", "name": "Varga Péter", "phone": "+36305556677", "last_service_date": "2026-08-15"}, # Nem alvó (friss)
            {"id": "CL-105", "name": "Farkas Andrea", "phone": "+36208889911", "last_service_date": "2025-09-05"}
        ]
    }
    res_prep = run(payload_prep)
    print(f"Status: {res_prep.get('status')}")
    camp = res_prep.get("campaign", {})
    print(f"Kampány azonosító: {camp.get('campaign_id')}")
    print(f"Kiszűrt alvó ügyfelek száma: {camp.get('dormant_clients_count')} fő (5-ből 4 alvó)")
    print(f"Várható potenciális bevétel: {camp.get('estimated_potential_revenue_huf'):,} Ft".replace(",", " "))
    print(f"Státusz: {camp.get('status')}")
    print(f"Vezetői jóváhagyási link: {camp.get('one_click_approval_link')}")
    print(f"Drip kötegek: {len(camp.get('batches_preview', []))} napra ütemezve")
    assert camp.get('dormant_clients_count') == 4
    assert camp.get('estimated_potential_revenue_huf') == 4 * 24000

    print("\n=== 2. TESZT: KÉTIRÁNYÚ AI ÜZENETVÁLTÁS (ÜGYFÉL MEGERŐSÍTŐ VÁLASZA) ===")
    payload_reply = {
        "action": "HANDLE_CUSTOMER_REPLY",
        "customer_phone": "+36 30 123 4567",
        "reply_message": "Szia! Igen, jövő hét szerdán jó lenne egy karbantartás délután."
    }
    res_reply = run(payload_reply)
    r = res_reply.get("result", {})
    print(f"Észlelt szándék: {r.get('detected_intent')}")
    print(f"Lead státusz: {r.get('lead_status')}")
    print(f"AI automatikus válasz az ügyfélnek:\n{r.get('automated_reply_text')}")
    assert r.get('detected_intent') == "BOOKING_INTERESTED"
    print("\n[SIKERES TESZT] Minden teszteset sikeresen lefutott!")

if __name__ == "__main__":
    test_dormant_reactivation()
