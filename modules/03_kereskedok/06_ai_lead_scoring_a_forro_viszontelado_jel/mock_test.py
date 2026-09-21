"""
Automatizált Mock Teszt Modul 06:
AI Lead Scoring – A Forró Viszonteladó-Jelöltek Kiszűrése
"""

import os
import sys
import json

curr_dir = os.path.dirname(os.path.abspath(__file__))
if curr_dir not in sys.path:
    sys.path.insert(0, curr_dir)

from handler import B2BLeadScoringHandler, run

def run_all_tests():
    print("=" * 65)
    print("[TESZT KEZDES] Modul 06: AI Lead Scoring Tesztcsomag inditasa")
    print("=" * 65)

    # 1. Payload betöltése
    payload_path = os.path.join(curr_dir, "test_payload.json")
    with open(payload_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    lead_count = len(payload.get("leads", []))
    print(f"[1. TESZT] test_payload.json betoltve ({lead_count} lead)")

    # 2. Mód A tesztelése: Speciális Területi KAM Routing
    config_mode_a = {
        "service_mode": "mock",
        "routing_mode": "specialized_sales_routing",
        "tier_thresholds": {
            "tier_a_min_score": 80,
            "tier_b_min_score": 50
        }
    }
    handler_a = B2BLeadScoringHandler(config_mode_a)
    res_a = handler_a.execute(payload)

    assert res_a.get("status") == "success", "Hiba: A scoring nem success statusszal tert vissza!"
    assert res_a.get("leads_processed_count") == 3, f"Hiba: 3 leadet vartunk, de {res_a.get('leads_processed_count')} lett."

    scored_leads = res_a.get("scored_leads", [])
    lead_a = next((l for l in scored_leads if l["lead_id"] == "LEAD-2026-001"), None)
    lead_b = next((l for l in scored_leads if l["lead_id"] == "LEAD-2026-002"), None)
    lead_c = next((l for l in scored_leads if l["lead_id"] == "LEAD-2026-003"), None)

    print("--- PONTOZASI EREDMENYEK ---")
    for sl in scored_leads:
        tier = sl["tier"]
        cname = sl["company_name"]
        score = sl["final_lead_score"]
        sla = sl["sales_strategy"]["sla_minutes"]
        kam = sl["routing"]["assigned_to"]
        print(f"[{tier}] {cname}: {score} pont | SLA: {sla} perc | KAM: {kam}")

    # Tier A ellenőrzése
    assert lead_a is not None, "LEAD-2026-001 nem talalhato!"
    assert lead_a["tier"] == "TIER_A", f"LEAD-2026-001 Tier A kell legyen, de: {lead_a['tier']}"
    assert lead_a["sales_strategy"]["sla_minutes"] == 15, "Tier A SLA 15 perc kell legyen!"
    assert "Kovács László" in lead_a["routing"]["assigned_to"], "Közép-Magyarország felelőse Kovács László kell legyen!"
    assert lead_a["routing"]["one_click_dial"] is not None, "One-click dial link hianyzik!"
    print("[OK] Tier A (KlímaTech Generál) kivaloan minosult Hot Leadkent (15 perces SLA-val)")

    # Tier B ellenőrzése
    assert lead_b is not None, "LEAD-2026-002 nem talalhato!"
    assert lead_b["tier"] == "TIER_B", f"LEAD-2026-002 Tier B kell legyen, de: {lead_b['tier']}"
    assert lead_b["sales_strategy"]["sla_minutes"] == 1440, "Tier B SLA 24 ora kell legyen!"
    assert "Nagy Péter" in lead_b["routing"]["assigned_to"], "Nyugat-Magyarország felelőse Nagy Péter kell legyen!"
    print("[OK] Tier B (Dunántúli Csőszerelő) Mid-Market B2B partnerkent minosult")

    # Tier C ellenőrzése (lakossági kiszűrés)
    assert lead_c is not None, "LEAD-2026-003 nem talalhato!"
    assert lead_c["tier"] == "TIER_C", f"LEAD-2026-003 Tier C kell legyen, de: {lead_c['tier']}"
    assert lead_c["sales_strategy"]["sla_minutes"] == 0, "Tier C nem terhelheti az ertekesitot (0 perc)!"
    act_title = lead_c["sales_strategy"]["action_title"].lower()
    assert "webáruház" in act_title or "udvarias" in act_title, "Lakossagi eliranyitas hianyzik!"
    print("[OK] Tier C (Kovács Béla lakossági) sikeresen kiszurve, sales ido nelkul iranyitva a webshophoz")

    # 3. Mód B tesztelése: Központi CRM Lead Pool
    print("[2. TESZT] Mód B: Központi CRM Lead Pool tesztelése...")
    config_mode_b = {
        "service_mode": "mock",
        "routing_mode": "central_crm_pool"
    }
    handler_b = B2BLeadScoringHandler(config_mode_b)
    res_b = handler_b.execute({"lead": payload["leads"][0]})
    scored_b_lead = res_b["scored_leads"][0]
    assert scored_b_lead["routing"]["routing_mode"].startswith("central_crm_pool"), "Mod B routing hiba!"
    assert scored_b_lead["routing"]["pool_priority_rank"] == "P1", "Tier A lead prioritasa P1 kell legyen!"
    print("[OK] Mód B Központi Lead Pool es P1 prioritasi besorolas tokeletesen mukodik")

    # 4. Egyedi Szabályok (Bonus/Malus) tesztelése
    print("[3. TESZT] Egyedi Szabályok (Bonus / Malus) tesztelése...")
    lead_custom = {
        "lead_id": "LEAD-CUSTOM-01",
        "company_name": "Kockázatos Vállalkozás Kft.",
        "industry": "HVAC kivitelezés",
        "headcount": 15,
        "annual_revenue_huf": 300000000,
        "positive_equity": True,
        "nav_tax_debt_free": False,
        "has_negative_credit_event": True,
        "has_iso_cert": True,
        "estimated_monthly_volume_huf": 2000000,
        "project_urgency": "azonnali_1_het"
    }
    res_custom = handler_a.score_single_lead(lead_custom)
    trig_rules = res_custom["dimension_scores"]["custom_rules_adjustment"]["triggered_rules"]
    assert len(trig_rules) >= 2, "Legalabb 2 egyedi szabaly aktiv kell legyen!"
    assert any(r["field"] == "has_negative_credit_event" for r in trig_rules), "Negativ credit szabaly hianyzik!"
    rule_names = [r["rule"] for r in trig_rules]
    print(f"[OK] Egyedi szabalyok lefutottak, szabaly levonasok/bonuszok ervenyesultek: {rule_names}")

    # 5. Tartós Napló (data/b2b_lead_scoring_naplo.json) ellenőrzése
    print("[4. TESZT] Tartós Adatbázis mentés ellenőrzése...")
    db_path = "data/b2b_lead_scoring_naplo.json"
    assert os.path.exists(db_path), f"Hiba: {db_path} nem jott letre!"
    with open(db_path, "r", encoding="utf-8") as f:
        db_data = json.load(f)
    assert "summary_metrics" in db_data, "Hianyzo summary_metrics!"
    assert db_data["total_scored_leads"] >= 3, "Adatbazis bejegyzesek szama tul keves!"
    tot = db_data["total_scored_leads"]
    avg = db_data["summary_metrics"]["average_lead_score"]
    print(f"[OK] Adatbazis rendben ({db_path}), osszes lead: {tot}, atlag pont: {avg}")

    # 6. Szabványos run() függvény tesztelése
    print("[5. TESZT] Szabványos run() belépési pont tesztelése...")
    hub_res = run(payload)
    assert hub_res.get("status") == "success", "Hub run() hiba!"
    print("[OK] Hub run() fuggveny sikeresen lefutott")

    print("=" * 65)
    print("[MINDEN TESZT SIKERESEN LEFUTOTT]")
    print("=" * 65)

if __name__ == "__main__":
    run_all_tests()