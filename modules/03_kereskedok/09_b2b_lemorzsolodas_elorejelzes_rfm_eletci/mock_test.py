"""
Automatizált Mock Teszt Modul 09:
B2B Lemorzsolódás Előrejelzés & RFM Életciklus Figyelő
"""

import os
import sys
import json

curr_dir = os.path.dirname(os.path.abspath(__file__))
if curr_dir not in sys.path:
    sys.path.insert(0, curr_dir)

from handler import B2BChurnPredictionHandler, run

def run_all_tests():
    print("=" * 65)
    print("[TESZT KEZDES] Modul 09: B2B Lemorzsolodas & RFM Tesztcsomag")
    print("=" * 65)

    # 1. Payload betöltése
    payload_path = os.path.join(curr_dir, "test_payload.json")
    with open(payload_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    p_count = len(payload.get("partners", []))
    print(f"[1. TESZT] test_payload.json betoltve ({p_count} partner)")

    # 2. Alapértelmezett elemzés futtatása
    handler = B2BChurnPredictionHandler({
        "service_mode": "mock",
        "churn_sensitivity": {
            "cycle_delay_multiplier_threshold": 1.5,
            "revenue_drop_percent_threshold": 40.0
        },
        "retention_strategy_mode": "tier_adaptive",
        "vip_retention_extra_discount_percent": 5.0,
        "escalation_mode": "hybrid_dual_channel"
    })
    res = handler.execute(payload)

    assert res.get("status") == "success", "Hiba: Folyamat statusz nem success!"
    assert res.get("partners_analyzed_count") == 3, "3 partnert vartunk!"

    partners = res.get("analyzed_partners", [])
    p_gold = next((p for p in partners if p["partner_code"] == "PARTNER-101"), None)
    p_silver = next((p for p in partners if p["partner_code"] == "PARTNER-102"), None)
    p_plat = next((p for p in partners if p["partner_code"] == "PARTNER-104"), None)

    print("--- ELEMZESI EREDMENYEK ES KOCKAZATI BESOROLASOK ---")
    for p in partners:
        cname = p["company_name"]
        tier = p["tier"]
        score = p["churn_assessment"]["churn_risk_score"]
        lvl = p["churn_assessment"]["risk_level"]
        segment = p["churn_assessment"]["rfm_segment"]
        alert = "AZONNALI" if p["escalation"]["instant_alert_triggered"] else "HETI_RIPORT"
        print(f"[{tier}] {cname} | Churn: {score}/100 | {lvl} | RFM: {segment} | Riasztas: {alert}")

    # 3. Gold Partner vizsgálata (KlímaMaster Szerelő Kft. - Magas Kockázat)
    assert p_gold is not None, "Gold partner nem talalhato!"
    assert p_gold["churn_assessment"]["risk_level"] == "HIGH_RISK_CHURN", "Gold partnernek HIGH_RISK_CHURN-nek kell lennie!"
    assert p_gold["churn_assessment"]["churn_risk_score"] >= 70, "Magas churn pontszam vart!"
    assert p_gold["escalation"]["instant_alert_triggered"] is True, "Gold partnernel azonnali KAM riasztas kell!"
    assert p_gold["escalation"]["one_click_dial"] is not None, "One-click dial hianyzik!"
    assert p_gold["retention_strategy"]["strategy_type"] == "VIP_BONUS_RETENTION", "VIP bonusz ajanlat hianyzik!"
    assert "+5%" in p_gold["retention_strategy"]["title"], "+5% bonusz ajanlat hianyzik a cimbol!"
    assert p_gold["competitor_switch_analysis"] is not None, "Konkurencia-atpartolas figyelmeztetes hianyzik!"
    print("[OK] Gold partner (KlímaMaster): Sikeresen azonositva High-Risk zónában, +5% visszatartó ajánlattal és azonnali KAM riasztással")

    # 4. Silver Partner vizsgálata (TermoGépész Kivitelező Bt. - Watchlist / Drifting)
    assert p_silver is not None, "Silver partner nem talalhato!"
    assert p_silver["churn_assessment"]["risk_level"] == "WATCHLIST_DRIFTING", "Silver partner WATCHLIST_DRIFTING kell legyen!"
    assert p_silver["escalation"]["instant_alert_triggered"] is False, "Silvernel heti riport kell azonnali riasztas helyett!"
    assert p_silver["retention_strategy"]["strategy_type"] == "DIAGNOSTIC_CHECK_IN", "Diagnosztikai kerdessor vart!"
    print("[OK] Silver partner (TermoGépész): Sikeresen Watchlist zónába sorolva, diagnosztikai beszélgetésindító kérdésekkel")

    # 5. Platinum Partner vizsgálata (Industrial Facility Services Zrt. - Egészséges)
    assert p_plat is not None, "Platinum partner nem talalhato!"
    assert p_plat["churn_assessment"]["risk_level"] == "HEALTHY_ACTIVE", "Platinum partnernek egeszsegesnek kell lennie!"
    assert p_plat["churn_assessment"]["rfm_segment"] == "Champions", "Platinum partner RFM Champion kell legyen!"
    print("[OK] Platinum partner (IFS Zrt.): Egészséges, aktív Champion státuszban maradt")

    # 6. Konfiguráció: talking_points_only mód tesztelése
    print("[2. TESZT] Retenciós stratégia: talking_points_only tesztelése...")
    handler_tp = B2BChurnPredictionHandler({"retention_strategy_mode": "talking_points_only"})
    res_tp = handler_tp._analyze_partner(payload["partners"][0], "2026-09-20")
    assert res_tp["retention_strategy"]["strategy_type"] == "DIAGNOSTIC_CHECK_IN"
    print("[OK] talking_points_only mod sikeresen elkerulte a direkt kedvezmenyadast")

    # 7. Tartós Napló (data/b2b_lemorzsolodas_naplo.json) ellenőrzése
    print("[3. TESZT] Tartós Adatbázis mentés ellenőrzése...")
    db_path = "data/b2b_lemorzsolodas_naplo.json"
    assert os.path.exists(db_path), f"Hiba: {db_path} nem jott letre!"
    with open(db_path, "r", encoding="utf-8") as f:
        db_data = json.load(f)
    assert "summary_kpis" in db_data, "Hianyzo summary_kpis!"
    kpis = db_data["summary_kpis"]
    assert kpis["high_risk_churn_count"] >= 1, "Legalabb 1 high risk partner kell legyen!"
    print(f"[OK] Adatbazis rendben ({db_path}) | High risk: {kpis['high_risk_churn_count']} | Veszelyeztetett arbevetel: {kpis['monthly_revenue_at_risk_huf']:,.0f} Ft/ho")

    # 8. Szabványos run() függvény tesztelése
    print("[4. TESZT] Szabványos run() belépési pont tesztelése...")
    hub_res = run(payload)
    assert hub_res.get("status") == "success", "Hub run() hiba!"
    print("[OK] Hub run() fuggveny tokeletesen mukodik")

    print("=" * 65)
    print("[MINDEN TESZT SIKERESEN LEFUTOTT]")
    print("=" * 65)

if __name__ == "__main__":
    run_all_tests()