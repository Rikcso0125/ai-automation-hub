"""
Mock teszt a 11_targyalaselemzes_es_sales_coaching_besze modulhoz.
Teszteli a beszéd/hallgatás arány kalkulációt, a félbeszakításokat, a Sales Score-t,
a vezetői riasztási küszöböt (<60 pont) és a márkázott PDF Coaching Lap generálását.
"""

import os
import sys
import json

curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, curr_dir)
from handler import run

def test_sales_coaching():
    print("=== 1. TESZT: GYENGE HÍVÁS ELEMZÉSE (TÚLBESZÉLÉS, FÉLBESZAKÍTÁS, VEZETŐI ALERT) ===")
    payload_suboptimal = {
        "call_metadata": {
            "call_id": "CALL-20260920-8812",
            "timestamp": "2026-09-20T14:15:00",
            "duration_seconds": 420,
            "deal_value_huf": 1450000
        },
        "sales_rep": {
            "name": "Németh Tamás (Junior Értékesítő)",
            "phone": "+36 30 222 4455",
            "email": "nemeth.tamas@profiklima.hu"
        },
        "customer": {
            "name": "Farkas Balázs",
            "company": "Farkas Autószerviz Kft."
        },
        "transcript_turns": [
            {"speaker": "SALES_REP", "text": "Jó napot, ajánlatunkkal keresem.", "duration_sec": 12},
            {"speaker": "CUSTOMER", "text": "Sokallom a másfél milliós árat.", "duration_sec": 8},
            {"speaker": "SALES_REP", "text": "De a mi gépünk Daikin kompresszoros és A+++ és 5 év garancia!", "duration_sec": 45},
            {"speaker": "CUSTOMER", "text": "De nekem nem biztos hogy...", "duration_sec": 5},
            {"speaker": "SALES_REP", "text": "És még ingyen be is üzemeljük hétvégén, ezt senki más nem adja meg!", "duration_sec": 28, "interrupted_customer": True},
            {"speaker": "CUSTOMER", "text": "Majd jövő héten beszéljünk.", "duration_sec": 8},
            {"speaker": "SALES_REP", "text": "Rendben, keresem hétfőn.", "duration_sec": 8}
        ]
    }
    res_sub = run(payload_suboptimal)
    print(f"Status: {res_sub.get('status')}")
    print(f"Hívás azonosító: {res_sub.get('call_id')}")
    m = res_sub.get("metrics", {})
    print(f"Beszédarány: Értékesítő {m.get('rep_ratio_percent')}% vs Ügyfél {m.get('cust_ratio_percent')}%")
    print(f"Félbeszakítások: {m.get('interruption_count')} db")
    print(f"Sales Minőségi Pontszám: {m.get('sales_score')}/100 ({m.get('grade')})")
    print(f"Vezetői riasztás aktiválódott: {res_sub.get('manager_alert_triggered')}")
    print(f"PDF jelentés: {res_sub.get('pdf_report_path')}")
    assert os.path.exists(res_sub.get('pdf_report_path')), "PDF fájlnak léteznie kell!"
    assert m.get('rep_ratio_percent') > 50, "Értékesítő beszédaránya magas kell legyen!"
    assert res_sub.get('manager_alert_triggered') is True, "Vezetői riasztásnak aktiválódnia kell!"

    print("\n=== 2. TESZT: PROFI KONZULTATÍV HÍVÁS ELEMZÉSE (MAGAS SALES SCORE) ===")
    payload_pro = {
        "call_metadata": {"call_id": "CALL-20260920-9901", "deal_value_huf": 650000},
        "sales_rep": {"name": "Kovács László (Senior Értékesítő)"},
        "customer": {"name": "Kiss Péter"},
        "transcript_turns": [
            {"speaker": "SALES_REP", "text": "Jó napot Péter! Hogyan értékeli a felmérés alapján készített csomagokat?", "duration_sec": 10},
            {"speaker": "CUSTOMER", "text": "Átnéztük a feleségemmel, alapvetően tetszik, de a villanyszámlán szeretnénk biztosak lenni.", "duration_sec": 25},
            {"speaker": "SALES_REP", "text": "Teljesen jogos szempont. Miért fontos Önöknek különösen az A+++ energiaosztály?", "duration_sec": 12},
            {"speaker": "CUSTOMER", "text": "Mert sokat használjuk nyáron otthonról dolgozva és nem szeretnénk meglepetéseket.", "duration_sec": 30},
            {"speaker": "SALES_REP", "text": "Értem. Ha kiszámoljuk, hogy az A+++ gép évi 45 ezer Ft-ot takarít meg a villanyszámlán, az megkönnyíti a döntést?", "duration_sec": 15},
            {"speaker": "CUSTOMER", "text": "Abszolút, akkor a prémium csomagot választjuk, küldje a szerződést!", "duration_sec": 15}
        ]
    }
    res_pro = run(payload_pro)
    m_pro = res_pro.get("metrics", {})
    print(f"Profi hívás Sales Pontszáma: {m_pro.get('sales_score')}/100 ({m_pro.get('grade')})")
    print(f"Beszédarány: Értékesítő {m_pro.get('rep_ratio_percent')}% vs Ügyfél {m_pro.get('cust_ratio_percent')}%")
    assert m_pro.get('sales_score') >= 85, "Profi hívásnak magas pontot kell kapnia!"
    print("\n[SIKERES TESZT] Minden teszteset sikeresen lefutott!")

if __name__ == "__main__":
    test_sales_coaching()
