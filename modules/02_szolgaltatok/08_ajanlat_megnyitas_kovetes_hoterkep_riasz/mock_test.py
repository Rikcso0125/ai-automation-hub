"""
Mock teszt a 08_ajanlat_megnyitas_kovetes_hoterkep_riasz modulhoz.
Teszteli az első megnyitást, a többszöri újramegnyitási sürgősségi riasztást,
a forrósági pontszámot (Hot / Burning Hot) és a közvetlen 1-kattintásos hívásindítót.
"""

import os
import sys
import json

curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, curr_dir)
from handler import run

def test_offer_tracking():
    print("=== 1. TESZT: ELSŐ MEGNÉZÉS ÉS ALAP HŐTÉRKÉP RIASZTÁS ===")
    payload_first = {
        "quote_id": "AJ-20260920-1001",
        "sales_rep": {"name": "Kovács László", "phone": "+36 30 111 2233"},
        "customer": {"name": "Kiss Péter", "phone": "+36 30 987 6543", "company": "Kiss Kft."},
        "telemetry": {
            "session_number": 1,
            "device_type": "Mobile (Android)",
            "total_dwell_seconds": 45,
            "scroll_depth_percent": 75,
            "sections_visited": {"pricing_packages": {"dwell_seconds": 30}}
        }
    }
    res_first = run(payload_first)
    print(f"Status: {res_first.get('status')}")
    print(f"Ajánlatszám: {res_first.get('quote_id')}")
    print(f"Megnyitások száma: {res_first.get('session_number')}")
    print(f"Forrósági pontszám: {res_first.get('heat_analytics', {}).get('score')}/100 ({res_first.get('heat_analytics', {}).get('heat_level')})")
    print(f"Közvetlen híváscím: {res_first.get('click_to_call_link')}")

    print("\n=== 2. TESZT: ÉGETŐEN FORRÓ ÚJRAMEGNYITÁS (BURNING HOT + SÜRGŐSSÉGI RIASZTÁS) ===")
    payload_reopen = {
        "quote_id": "AJ-20260920-1001",
        "sales_rep": {"name": "Kovács László", "phone": "+36 30 111 2233"},
        "customer": {"name": "Kiss Péter", "phone": "+36 30 987 6543", "company": "Kiss Kft."},
        "telemetry": {
            "session_number": 3,
            "device_type": "Mobile (iPhone / Safari)",
            "total_dwell_seconds": 135,
            "scroll_depth_percent": 100,
            "sections_visited": {
                "pricing_packages": {"dwell_seconds": 70},
                "warranty_terms": {"dwell_seconds": 40}
            },
            "clicked_elements": ["select_better_package_details"]
        }
    }
    res_reopen = run(payload_reopen)
    print(f"Status: {res_reopen.get('status')}")
    print(f"Újramegnyitás észlelve: {res_reopen.get('is_reopened')}")
    print(f"Forrósági pontszám: {res_reopen.get('heat_analytics', {}).get('score')}/100 ({res_reopen.get('heat_analytics', {}).get('heat_level')})")
    print(f"Jelvény: {res_reopen.get('heat_analytics', {}).get('heat_badge')}")
    print(f"Akció javaslat: {res_reopen.get('heat_analytics', {}).get('action_recommendation')}")
    print("\nRiasztási üzenet az értékesítőnek:\n" + res_reopen.get('sales_alert_message', ''))
    assert res_reopen.get('is_reopened') is True
    assert res_reopen.get('heat_analytics', {}).get('score') >= 85
    print("\n[SIKERES TESZT] Minden teszteset sikeresen lefutott!")

if __name__ == "__main__":
    test_offer_tracking()
