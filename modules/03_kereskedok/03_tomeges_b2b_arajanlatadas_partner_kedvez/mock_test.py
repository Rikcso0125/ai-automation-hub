"""
Tömeges B2B Árajánlatadás Partner Kedvezményszintekkel - Komprehenzív Mock Teszt
Modul: 03_tomeges_b2b_arajanlatadas_partner_kedvez
"""
import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from handler import B2BQuotationHandler, run

def run_all_tests():
    print("=" * 65)
    print(">>> [TESZT] 03_tomeges_b2b_arajanlatadas_partner_kedvez")
    print("=" * 65)

    handler = B2BQuotationHandler()

    # TESZT 1: Ömlesztett szöveges email feldolgozása, GOLD partner és készlethiány-kezelés
    print("[1. TESZT] Ömlesztett email kérés elemzése (GOLD partner & hiánykezelés)...")
    email_payload = {
        "action": "GENERATE_B2B_QUOTE",
        "partner_identifier": "KlímaMaster Szerelő Kft.",
        "request_text": "Sziasztok! Kérnék gyors hivatalos árajánlatot és készletinfót az alábbi tételekre: 150 m 15-ös rézcső, 40 db 1/2 colos golyóscsap és 5 db Grundfos Alpha 25-60 keringető szivattyú. Köszi, Nagy Zoltán - KlímaMaster Szerelő Kft."
    }
    res1 = handler.execute(email_payload)
    assert res1["status"] == "success"
    assert res1["partner"]["tier"] == "GOLD"
    assert res1["partner"]["tier_discount_percent"] == 22.0
    assert len(res1["items"]) >= 3
    print(f"   [OK] Partner beazonosítva: {res1['partner']['company_name']} ({res1['partner']['tier']} -{res1['partner']['tier_discount_percent']}%)")
    print(f"   [OK] Nettó végösszeg: {res1['financial_summary']['final_net_huf']:,} Ft (Megtakarítás: {res1['financial_summary']['partner_savings_huf']:,} Ft)")
    
    # Hiány és alternatíva ellenőrzése
    assert len(res1["shortage_alerts"]) >= 1, "Nem detektálta a Grundfos szivattyú készlethiányát!"
    pump_alert = res1["shortage_alerts"][0]
    assert pump_alert["sku"] == "PUMP-GRUNDFOS-25"
    assert pump_alert["alternative"] is not None
    print(f"   [OK] Készlethiány sikeresen detektálva: {pump_alert['sku']} (Kért: {pump_alert['requested_qty']}, Készlet: {pump_alert['available_qty']})")
    print(f"   [OK] Egyenértékű alternatíva felajánlva: {pump_alert['alternative']['alternative_name']} (Készleten: {pump_alert['alternative']['alternative_stock_qty']} db)")
    print(f"   [OK] 1-Kattintásos értékesítői jóváhagyási link: {res1['one_click_approval_url']}")

    # TESZT 2: Strukturált tétellista és PLATINUM partner kedvezmény
    print("\n[2. TESZT] Strukturált tétellista feldolgozása (PLATINUM partner -28%)...")
    platinum_payload = {
        "action": "GENERATE_B2B_QUOTE",
        "partner_identifier": "Industrial Facility Services Zrt.",
        "items": [
            {"sku": "DAIKIN-SENSIRA-35", "quantity": 4},
            {"sku": "FITTING-ELBOW-90", "quantity": 200}
        ]
    }
    res2 = handler.execute(platinum_payload)
    assert res2["partner"]["tier"] == "PLATINUM"
    assert res2["partner"]["tier_discount_percent"] == 28.0
    print(f"   [OK] Platina partner azonosítva (-28% engedmény): {res2['partner']['company_name']}")
    print(f"   [OK] Nettó ajánlati összeg: {res2['financial_summary']['final_net_huf']:,} Ft")

    # TESZT 3: Értékesítői 1-kattintásos jóváhagyás
    print("\n[3. TESZT] Értékesítői 1-kattintásos ajánlat jóváhagyás és kiküldés...")
    quote_id = res1["quote_id"]
    approve_payload = {
        "action": "APPROVE_QUOTE",
        "quote_id": quote_id
    }
    res3 = handler.execute(approve_payload)
    assert res3["status"] == "success"
    assert res3["new_status"] == "APPROVED_AND_SENT_TO_PARTNER"
    print(f"   [OK] {res3['message']}")

    # Naplózás ellenőrzése
    db_path = Path("data/b2b_ajanlatok_naplo.json")
    assert db_path.exists(), "Az ajánlati napló nem létezik!"
    with open(db_path, "r", encoding="utf-8") as f:
        quotes = json.load(f)
    print(f"   [OK] Perzisztens ajánlati naplóban tárolt elemek száma: {len(quotes)}")

    print("\n" + "=" * 65)
    print(">>> MINDEN TESZT SIKERESEN LEFUTOTT! (03_tomeges_b2b_arajanlatadas)")
    print("=" * 65)

if __name__ == "__main__":
    run_all_tests()
