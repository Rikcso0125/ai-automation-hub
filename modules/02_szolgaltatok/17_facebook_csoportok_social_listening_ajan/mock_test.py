"""
Facebook Csoportok Social Listening - Komprehenzív Mock Teszt
Modul: 17_facebook_csoportok_social_listening_ajan
"""
import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from handler import FacebookSocialListeningHandler, run

def run_all_tests():
    print("=" * 65)
    print(">>> [TESZT] 17_facebook_csoportok_social_listening_ajan")
    print("=" * 65)

    custom_config = {
        "company_name": "ProfiKlíma & Épületgépészet Kft.",
        "company_specialty": "Lakossági és ipari klíma, hőszivattyú telepítés, F-Gáz garancia",
        "company_phone": "+36 30 123 4567",
        "booking_url": "https://profiklima.hu/idopontfoglalas",
        "min_relevance_score": 65,
        "leads_db_path": "data/facebook_leads_naplo.json"
    }
    handler = FacebookSocialListeningHandler(custom_config)

    # TESZT 1: Valós Forró Ajánláskérés (Magas Relevancia)
    print("[1. TESZT] Releváns lakossági ajánláskérés észlelése...")
    lead_payload = {
        "action": "ANALYZE_POST",
        "post_id": "FB-TEST-9001",
        "group_name": "Újbuda - XI. kerületiek csoportja",
        "author_name": "Kovács László",
        "post_text": "Sziasztok! Tudtok jó klímást ajánlani a XI. kerületben? Csendes, minőségi klímát keresünk nappaliba garanciával és tisztességes számlával. Köszönöm!",
        "post_url": "https://facebook.com/groups/ujbuda/posts/9001"
    }
    res1 = handler.execute(lead_payload)
    assert res1["status"] == "success", f"Hibás státusz: {res1.get('status')}"
    assert res1["relevance_score"] >= 65, f"Alacsony pontszám: {res1['relevance_score']}"
    assert "Gazdagrét" in res1["generated_expert_comment"] or "XI. kerület" in res1["generated_expert_comment"] or "ProfiKlíma" in res1["generated_expert_comment"]
    print(f"   [OK] Relevancia pontszám: {res1['relevance_score']}/100 | Intent: {res1['intent']}")
    print(f"   [OK] Szakértői komment előállítva (Hossz: {len(res1['generated_expert_comment'])} karakater)")
    print(f"   [OK] Messenger DM vázlat előállítva (Hossz: {len(res1['generated_messenger_dm'])} karakter)")
    print(f"   [OK] 1-kattintásos jóváhagyási kapu: {res1['one_click_approval_url']}")

    # TESZT 2: Negatív kizáró kulcsszó kiszűrése (Spam / Álláshirdetés)
    print("\n[2. TESZT] Negatív kizáró kulcsszó teszt (Álláshirdetés kiszűrése)...")
    spam_payload = {
        "action": "ANALYZE_POST",
        "post_id": "FB-TEST-SPAM",
        "group_name": "Klímaszerelők és Fűtéstechnika",
        "author_name": "Karrier Iroda",
        "post_text": "Azonnali kezdéssel klímaszerelő munkatársat felveszünk kiemelt bérezéssel. Munkaajánlat és állás kapcsán keressetek!",
        "post_url": "https://facebook.com/groups/klima/posts/999"
    }
    res2 = handler.execute(spam_payload)
    assert res2["status"] == "SKIPPED_NEGATIVE_KEYWORD", f"Nem szűrte ki: {res2.get('status')}"
    print(f"   [OK] Sikeres spamszűrés: {res2['reason']}")

    # TESZT 3: Alacsony relevanciájú bejegyzés kiszűrése
    print("\n[3. TESZT] Alacsony relevanciájú bejegyzés teszt...")
    low_payload = {
        "action": "ANALYZE_POST",
        "post_id": "FB-TEST-LOW",
        "group_name": "Budaörsiek közössége",
        "author_name": "Kiss Anna",
        "post_text": "Milyen szép idő van ma Budaörsön a hegyen!",
        "post_url": "https://facebook.com/groups/budaors/posts/888"
    }
    res3 = handler.execute(low_payload)
    assert res3["status"] == "LOW_RELEVANCE", f"Nem jelölte alacsonynak: {res3.get('status')}"
    print(f"   [OK] Helyesen figyelmen kívül hagyva: Relevancia = {res3['relevance_score']}/100")

    # TESZT 4: Értékesítői 1-kattintásos jóváhagyás tesztelése
    print("\n[4. TESZT] Értékesítői 1-kattintásos jóváhagyás (Lead Státusz frissítés)...")
    lead_id = res1["lead_id"]
    approve_payload = {
        "action": "APPROVE_LEAD",
        "lead_id": lead_id
    }
    res4 = handler.execute(approve_payload)
    assert res4["status"] == "success", f"Jóváhagyási hiba: {res4.get('message')}"
    assert res4["new_status"] == "APPROVED_AND_POSTED"
    print(f"   [OK] {res4['message']}")

    # Adatbázis ellenőrzése
    db_path = Path("data/facebook_leads_naplo.json")
    assert db_path.exists(), "Az adatbázis fájl nem jött létre!"
    with open(db_path, "r", encoding="utf-8") as f:
        records = json.load(f)
    print(f"   [OK] Perzisztens lead adatbázisban tárolt elemek száma: {len(records)}")

    print("\n" + "=" * 65)
    print(">>> MINDEN TESZT SIKERESEN LEFUTOTT! (17_facebook_csoportok)")
    print("=" * 65)

if __name__ == "__main__":
    run_all_tests()
