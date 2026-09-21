"""
B2B Weboldal Látogatók Leleplezése - Komprehenzív Mock Teszt
Modul: 04_b2b_weboldal_latogatok_leleplezese_de_an
"""
import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from handler import B2BDeAnonymizationHandler, run

def run_all_tests():
    print("=" * 65)
    print(">>> [TESZT] 04_b2b_weboldal_latogatok_leleplezese_de_an")
    print("=" * 65)

    handler = B2BDeAnonymizationHandler()

    # TESZT 1: Forró B2B Látogató leleplezése, Intent pontozás és döntéshozó-kutatás
    print("[1. TESZT] Forró B2B cég leleplezése (Reverse IP & Intent Scoring)...")
    hot_payload = {
        "action": "DE_ANONYMIZE_VISITOR",
        "session_id": "SESS-2026-99120",
        "ip_address": "194.149.24.88",
        "isp_name": "GTS Datanet / Corporate Leased Line",
        "domain": "duna-epgep.hu",
        "company_hint": "Duna-ÉpítőGépész Kivitelező Zrt.",
        "time_on_site_seconds": 245,
        "visit_count": 2,
        "pages_visited": [
            {"url": "/fooldal"},
            {"url": "/termekek/ipari-klimak-es-hoszivattyuk"},
            {"url": "/nagyker-viszonteladoi-arlista"},
            {"url": "/kapcsolat-nagykereskedes"}
        ]
    }
    res1 = handler.execute(hot_payload)
    assert res1["status"] == "success"
    assert res1["is_hot_lead"] is True
    assert res1["intent_score"] >= 70
    comp = res1["company_intelligence"]
    print(f"   [OK] Leleplezett cég: {comp['company_name']} ({comp['industry']})")
    print(f"   [OK] Cégméret: {comp['headcount']} | Becsült árbevétel: {comp['estimated_annual_revenue']}")
    print(f"   [OK] Intent Score: {res1['intent_score']}/100 ({res1['intent_tier']})")
    
    # Döntéshozók és forgatókönyv ellenőrzése
    dms = res1["decision_makers"]
    assert len(dms) >= 3
    print(f"   [OK] Felkutatott döntéshozók száma: {len(dms)} fő (pl. {dms[0]['name']} - {dms[0]['title']})")
    assert len(res1["sales_outreach_scripts"]["phone_script"]) > 100
    print(f"   [OK] Személyre szabott telefonos és emailes nyitószöveg legenerálva.")
    print(f"   [OK] 1-Kattintásos CRM átvételi link: {res1['one_click_crm_claim_url']}")

    # TESZT 2: Lakossági internetszolgáltató kiszűrése (Telekom előfizető)
    print("\n[2. TESZT] Lakossági internetszolgáltató kiszűrése (Spamszűrő)...")
    residential_payload = {
        "action": "DE_ANONYMIZE_VISITOR",
        "session_id": "SESS-RESIDENTIAL-01",
        "ip_address": "84.2.45.12",
        "isp_name": "Magyar Telekom Nyrt. Lakossági Dinamikus Pool",
        "pages_visited": [{"url": "/fooldal"}]
    }
    res2 = handler.execute(residential_payload)
    assert res2["status"] == "SKIPPED_RESIDENTIAL_ISP"
    print(f"   [OK] Helyesen kiszűrve: {res2['reason']}")

    # TESZT 3: Értékesítői 1-kattintásos CRM lead átvétel
    print("\n[3. TESZT] Értékesítői 1-kattintásos CRM átvétel (Lead Claim)...")
    lead_id = res1["lead_id"]
    claim_payload = {
        "action": "CLAIM_LEAD",
        "lead_id": lead_id,
        "sales_rep": "Kovács László Értékesítési Vezető"
    }
    res3 = handler.execute(claim_payload)
    assert res3["status"] == "success"
    assert res3["new_status"] == "CLAIMED_IN_CRM"
    print(f"   [OK] {res3['message']}")

    # Adatbázis ellenőrzése
    db_path = Path("data/b2b_weboldal_latogatok.json")
    assert db_path.exists(), "A látogatói adatbázis fájl nem jött létre!"
    with open(db_path, "r", encoding="utf-8") as f:
        visitors = json.load(f)
    print(f"   [OK] Perzisztens látogatói adatbázisban tárolt elemek száma: {len(visitors)}")

    print("\n" + "=" * 65)
    print(">>> MINDEN TESZT SIKERESEN LEFUTOTT! (04_b2b_weboldal_latogatok)")
    print("=" * 65)

if __name__ == "__main__":
    run_all_tests()
