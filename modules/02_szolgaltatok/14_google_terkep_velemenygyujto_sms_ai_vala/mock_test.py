"""
Mock teszt a 14_google_terkep_velemenygyujto_sms_ai_vala modulhoz.
Teszteli az értékeléskérő üzenetet a Gatekeeper linkkel, a pozitív 5 csillagos
vélemény automatikus SEO válaszát, valamint a 2 csillagos negatív vélemény belső védőpajzsát.
"""

import os
import sys
import json

curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, curr_dir)
from handler import run

def test_google_reviews():
    print("=== 1. TESZT: ÉRTÉKELÉSKÉRÉS KIKÜLDÉSE GATEKEEPER LINKKEL ===")
    payload_req = {
        "action": "SEND_REVIEW_REQUEST",
        "customer": {
            "name": "Németh Krisztina",
            "phone": "+36 30 555 9988"
        },
        "completed_job": {
            "job_id": "JOB-20260920-112",
            "service_name": "Gree Comfort X klímaszerelés",
            "site_district": "2. kerület (Buda)"
        },
        "technician": {"name": "Kovács László"}
    }
    res_req = run(payload_req)
    print(f"Status: {res_req.get('status')}")
    print(f"Gatekeeper link: {res_req.get('gatekeeper_link')}")
    print(f"Csatorna: {res_req.get('delivery_channel')}")
    assert "gate?job_id=" in res_req.get('gatekeeper_link')

    print("\n=== 2. TESZT: 5 CSILLAGOS POZITÍV VÉLEMÉNY & HELYI SEO AUTO-VÁLASZ ===")
    payload_pos = {
        "action": "PROCESS_INCOMING_REVIEW",
        "review_data": {
            "review_id": "REV-551",
            "rating_stars": 5,
            "author_name": "Németh Krisztina",
            "comment": "Kiváló és gyors munka, Kovács úr nagyon tiszta volt és mindent elmagyarázott!"
        },
        "completed_job": {
            "service_name": "klímaszerelés",
            "site_district": "2. kerület (Buda)"
        }
    }
    res_pos = run(payload_pos)
    print(f"Csillagok: {res_pos.get('rating_stars')}")
    print(f"Státusz: {res_pos.get('publication_status')}")
    print(f"Helyi SEO tartalom: {res_pos.get('contains_local_seo')}")
    print(f"Generált AI válasz:\n{res_pos.get('generated_reply')}")
    assert res_pos.get('publication_status') == "PUBLISHED_TO_GOOGLE_MAPS"
    assert res_pos.get('manager_alert_triggered') is False

    print("\n=== 3. TESZT: 2 CSILLAGOS NEGATÍV VÉLEMÉNY & REPUTÁCIÓVÉDŐ RIASZTÁS ===")
    payload_neg = {
        "action": "PROCESS_INCOMING_REVIEW",
        "review_data": {
            "review_id": "REV-992",
            "rating_stars": 2,
            "author_name": "Kovács Péter",
            "comment": "Késtek fél órát a szereléssel és zajosnak találom a gépet."
        }
    }
    res_neg = run(payload_neg)
    print(f"Csillagok: {res_neg.get('rating_stars')}")
    print(f"Státusz: {res_neg.get('publication_status')}")
    print(f"Vezetői riasztás aktiválódott: {res_neg.get('manager_alert_triggered')}")
    print(f"Jóváhagyási link: {res_neg.get('one_click_approval_link')}")
    print(f"Diplomatikus válaszjavaslat:\n{res_neg.get('generated_reply')}")
    assert res_neg.get('publication_status') == "PENDING_MANAGER_APPROVAL"
    assert res_neg.get('manager_alert_triggered') is True
    print("\n[SIKERES TESZT] Minden teszteset sikeresen lefutott!")

if __name__ == "__main__":
    test_google_reviews()
