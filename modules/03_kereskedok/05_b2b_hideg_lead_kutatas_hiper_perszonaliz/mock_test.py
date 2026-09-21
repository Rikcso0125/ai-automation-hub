"""
B2B Hideg Lead-Kutatás & Hiper-perszonalizált Megkeresés - Komprehenzív Mock Teszt
Modul: 05_b2b_hideg_lead_kutatas_hiper_perszonaliz
"""
import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from handler import B2BColdLeadOutreachHandler, run

def run_all_tests():
    print("=" * 65)
    print(">>> [TESZT] 05_b2b_hideg_lead_kutatas_hiper_perszonaliz")
    print("=" * 65)

    handler = B2BColdLeadOutreachHandler()

    # TESZT 1: Kampány előállítása 3-lépcsős perszonalizált szekvenciával
    print("[1. TESZT] B2B Célcsoport kutatás és 3-lépcsős levélsorozat generálás...")
    campaign_payload = {
        "action": "PROSPECT_AND_GENERATE_CAMPAIGN",
        "search_criteria": {
            "industries": ["Épületgépészet", "Klímaszerelés"],
            "region": "Budapest és Pest megye"
        },
        "prospects": [
            {
                "company_name": "Pannónia Épületgépész Kft.",
                "decision_maker_name": "Kerekes András",
                "decision_maker_title": "Ügyvezető",
                "email": "a.kerekes@pannoniagepesz.hu",
                "recent_project_reference": "a Corvin sétány új irodaépületének komplett hűtése",
                "specialty": "Ipari VRF rendszerek"
            },
            {
                "company_name": "BudaVent Légtechnika Zrt.",
                "decision_maker_name": "Váradi Márk",
                "decision_maker_title": "Beszerzési Igazgató",
                "email": "beszerzes@budavent.hu",
                "recent_project_reference": "a Budaörsi logisztikai park 12 000 m2-es raktárcsarnoka",
                "specialty": "Ipari légtechnika és csőhálózatok"
            }
        ]
    }
    res1 = handler.execute(campaign_payload)
    assert res1["status"] == "success"
    assert res1["total_prospects"] == 2
    prospect_1 = res1["prospects"][0]
    seq_1 = prospect_1["sequence"]
    assert len(seq_1) == 3, f"Nem 3-lépcsős a szekvencia: {len(seq_1)}"
    assert "Corvin sétány" in seq_1[0]["body"], "A jégtörő nem tartalmazza a projekt referenciát!"
    print(f"   [OK] Kampány generálva: {res1['campaign_id']} ({res1['total_prospects']} cég)")
    print(f"   [OK] 1. Lépés (Day 0): {seq_1[0]['subject']}")
    print(f"   [OK] 2. Lépés (Day 4): {seq_1[1]['subject']}")
    print(f"   [OK] 3. Lépés (Day 8): {seq_1[2]['subject']}")
    print(f"   [OK] 1-Kattintásos vezetői jóváhagyás: {res1['one_click_approval_url']}")

    # TESZT 2: Kampány jóváhagyása (Értékesítési vezetői kapu)
    print("\n[2. TESZT] Kampány jóváhagyása (Értékesítési vezetői kapu)...")
    camp_id = res1["campaign_id"]
    approve_payload = {
        "action": "APPROVE_CAMPAIGN",
        "campaign_id": camp_id
    }
    res2 = handler.execute(approve_payload)
    assert res2["status"] == "success"
    assert res2["new_status"] == "APPROVED_AND_RUNNING"
    print(f"   [OK] {res2['message']}")

    # TESZT 3: Automatikus szekvencia-leállítás válasz esetén
    print("\n[3. TESZT] Automatikus leállítás válaszérkezés esetén (Auto-Stop on Reply)...")
    reply_payload = {
        "action": "RECORD_REPLY",
        "campaign_id": camp_id,
        "prospect_email": "a.kerekes@pannoniagepesz.hu"
    }
    res3 = handler.execute(reply_payload)
    assert res3["status"] == "success"
    assert res3["action"] == "SEQUENCE_STOPPED"
    print(f"   [OK] {res3['message']}")

    # Adatbázis ellenőrzése
    db_path = Path("data/b2b_hideg_leadek_naplo.json")
    assert db_path.exists(), "A hideg lead adatbázis nem jött létre!"
    with open(db_path, "r", encoding="utf-8") as f:
        campaigns = json.load(f)
    print(f"   [OK] Perzisztens adatbázisban tárolt kampányok száma: {len(campaigns)}")

    print("\n" + "=" * 65)
    print(">>> MINDEN TESZT SIKERESEN LEFUTOTT! (05_b2b_hideg_lead_kutatas)")
    print("=" * 65)

if __name__ == "__main__":
    run_all_tests()
