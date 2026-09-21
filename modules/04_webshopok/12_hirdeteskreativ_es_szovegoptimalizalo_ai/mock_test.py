# -*- coding: utf-8 -*-
"""
Mock teszt a Hirdeteskreativ- es Szovegoptimalizalo AI & Ad Fatigue Figyelo modulhoz.
3 uzleti forgatokonyv tesztelese:
1. Kritikus Ad Fatigue (Meta Ads) -> 100/100 pont, Circuit Breaker vészleállítás, 4 szög generálás
2. Fully Autonomous Kill & Scale mod -> regi hirdetes leallitasa es uj adset azonnali inditasa
3. Egeszseges hirdetes (alacsony frekvencia, jo ROAS) -> Healthy statusz, nem kell beavatkozas
"""

import sys
import os
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from handler import run


def test_scenario_1_critical_ad_fatigue():
    print("\n--- TESZT 1: Kritikus Ad Fatigue (Magas frekvencia + CTR zuhanas + ROAS eses) ---")
    payload = {
        "campaign": {
            "campaign_id": "CAMP-META-2026-BOSCH",
            "campaign_name": "Tavaszi Epítkezes - Konverzios Kampany",
            "adset_id": "ADSET-881920",
            "ad_id": "AD-4418290-DRILL",
            "ad_name": "Bosch GBH 2-28 - Regi Hirdetes 1"
        },
        "product": {
            "sku": "BOSCH-GBH-2-28",
            "name": "Bosch Professional GBH 2-28 Furokalapacs L-BOXX",
            "price_huf": 68900
        },
        "metrics_last_7_days": {
            "impressions": 84500,
            "reach": 29800,
            "frequency": 2.84,
            "current_ctr_pct": 0.82,
            "baseline_ctr_pct": 1.65,
            "ctr_drop_pct": 50.3,
            "spend_huf": 142000,
            "purchases_count": 14,
            "current_cpa_huf": 10142,
            "max_target_cpa_huf": 7500,
            "revenue_huf": 298200,
            "current_roas": 2.1,
            "target_min_roas": 3.0
        },
        "config": {
            "fatigue_detection_mode": "hybrid_comprehensive_rules",
            "frequency_fatigue_threshold": 2.8,
            "ctr_drop_percent_threshold": 25,
            "target_minimum_roas": 3.0,
            "copywriting_generation_mode": "selectable_all_formats",
            "intervention_mode": "hybrid_smart_guard"
        }
    }
    
    res = run(payload)
    print(f"Status: {res.get('status')}")
    print(f"Fatigue Statusz: {res.get('fatigue_analysis', {}).get('status')}")
    print(f"Fatigue Pontszam: {res.get('fatigue_analysis', {}).get('fatigue_score')}/100")
    print(f"Beavatkozas: {res.get('intervention', {}).get('action_taken')}")
    print(f"Meta Graph API parancs: {res.get('intervention', {}).get('meta_graph_api_command')}")
    
    angles = res.get("new_creative_package", {}).get("psychological_angles", [])
    print(f"Legeneralt pszichologiai szogek szama: {len(angles)}")
    print(f"1. Szog cime: {angles[0].get('primary_headline')}")
    print(f"2. Szog cime: {angles[1].get('primary_headline')}")
    print(f"3. Szog cime: {angles[2].get('primary_headline')}")
    print(f"4. Szog cime: {angles[3].get('primary_headline')}")
    
    hooks = res.get("new_creative_package", {}).get("dynamic_hook_matrix", {}).get("hooks", [])
    print(f"Dinamikus hookok szama: {len(hooks)}")
    
    assert res.get("status") == "success"
    assert res.get("fatigue_analysis", {}).get("status") == "CRITICAL_AD_FATIGUE"
    assert res.get("fatigue_analysis", {}).get("fatigue_score") == 100
    assert res.get("intervention", {}).get("action_taken") == "CIRCUIT_BREAKER_EMERGENCY_PAUSE"
    assert len(angles) == 4
    print("[OK] Teszt 1 sikeresen lefutott!")


def test_scenario_2_fully_autonomous_scale():
    print("\n--- TESZT 2: Teljesen Autonom Kill & Scale beavatkozas ---")
    payload = {
        "campaign": {
            "campaign_id": "CAMP-002",
            "ad_id": "AD-OLD-99"
        },
        "product": {
            "name": "DeWalt DCD796 Furo"
        },
        "metrics_last_7_days": {
            "frequency": 3.1,
            "ctr_drop_pct": 35.0,
            "current_roas": 2.2,
            "target_min_roas": 3.0
        },
        "config": {
            "intervention_mode": "fully_autonomous_kill_and_scale"
        }
    }
    
    res = run(payload)
    print(f"Beavatkozas: {res.get('intervention', {}).get('action_taken')}")
    print(f"Uj adset parancs: {res.get('intervention', {}).get('new_adset_command')}")
    print(f"Emberi jovahagyas szukseges: {res.get('intervention', {}).get('requires_human_approval')}")
    
    assert res.get("status") == "success"
    assert res.get("intervention", {}).get("action_taken") == "AUTO_PAUSED_AND_REPLACED"
    assert res.get("intervention", {}).get("requires_human_approval") is False
    print("[OK] Teszt 2 sikeresen lefutott!")


def test_scenario_3_healthy_ad_no_action():
    print("\n--- TESZT 3: Egeszseges hirdetes ellenorzese ---")
    payload = {
        "campaign": {
            "campaign_id": "CAMP-003",
            "ad_id": "AD-FRESH-12"
        },
        "product": {
            "name": "Makita Akkus Furesz"
        },
        "metrics_last_7_days": {
            "frequency": 1.4,
            "ctr_drop_pct": 0.0,
            "current_roas": 4.2,
            "target_min_roas": 3.0,
            "current_cpa_huf": 4200,
            "max_target_cpa_huf": 7500
        },
        "config": {
            "intervention_mode": "hybrid_smart_guard"
        }
    }
    
    res = run(payload)
    print(f"Fatigue Statusz: {res.get('fatigue_analysis', {}).get('status')}")
    print(f"Fatigue Pontszam: {res.get('fatigue_analysis', {}).get('fatigue_score')}")
    print(f"Surgosseg: {res.get('fatigue_analysis', {}).get('urgency')}")
    
    assert res.get("status") == "success"
    assert res.get("fatigue_analysis", {}).get("status") == "HEALTHY_PERFORMANCE"
    assert res.get("fatigue_analysis", {}).get("fatigue_score") == 0
    print("[OK] Teszt 3 sikeresen lefutott!")


if __name__ == "__main__":
    print("=== MODULE 4.12: HIRDETESKREATIV & AD FATIGUE FIGYELO MOCK TESZT ===")
    test_scenario_1_critical_ad_fatigue()
    test_scenario_2_fully_autonomous_scale()
    test_scenario_3_healthy_ad_no_action()
    print("\n[MINDEN TESZT SIKERESEN LEFUTOTT!]")
