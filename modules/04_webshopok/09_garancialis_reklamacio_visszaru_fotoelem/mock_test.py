# -*- coding: utf-8 -*-
"""
Mock teszt a Garancialis Reklamacio & Visszaru Fotoelemzes modulhoz.
4 kulonbozo uzleti forgatokonyv tesztelese:
1. Gyari hiba (Bosch furogep, 48.900 Ft) - Foxpost retur kod + 10% bonusz kupon
2. Alacsony erteku tetel (9.800 Ft) - Keep-the-item kuszob ervenyesites (nem kell visszakuldeni)
3. Nem rendeltetesszeru hasznalat (beazas / tores) - Garanciavesztes elutasitas
4. GLS Pick & Return haztol-hazig futar + Billingo/Szamlazz.hu jovairo szamla
"""

import sys
import os
import json

# Helyi handler importalasa szamozott mappanev miatt
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from handler import run


def test_scenario_1_manufacturing_defect_foxpost():
    print("\n--- TESZT 1: Gyari hiba (Foxpost automatas retur + 10% bonusz kupon) ---")
    payload = {
        "claim_id": "CLM-2026-8941",
        "customer": {
            "name": "Kovacs Peter",
            "email": "kovacs.peter@pelda.hu",
            "phone": "+36301234567"
        },
        "order": {
            "order_number": "ORD-2025-11048",
            "invoice_number": "SZAMLA-2025-0842",
            "purchase_date": "2025-10-15",
            "item_sku": "BOSCH-GSR-18V-50",
            "item_name": "Bosch Professional GSR 18V-50 Akkus Furo-Csavarozon",
            "item_price_gross_huf": 48900,
            "serial_number": "SN-8849201948"
        },
        "complaint": {
            "issue_description": "Bekapcsolaskor szikrazik a motor es fustol a szellozonyilas, a tokmany megszorult.",
            "photo_urls": ["https://storage.webshop.hu/claims/CLM-2026-8941/motor_eges.jpg"],
            "preferred_return_channel": "foxpost_box",
            "preferred_resolution": "store_credit_bonus"
        },
        "config": {
            "verification_mode": "hybrid_smart_rule",
            "keep_the_item_threshold_huf": 15000,
            "approval_gate": "hybrid_confidence_threshold",
            "store_credit_bonus_percent": 10
        }
    }
    
    res = run(payload)
    print(f"Status: {res.get('status')}")
    print(f"Jovahagyasi statusz: {res.get('approval_status')}")
    print(f"Vision besorolas: {res.get('vision_analysis', {}).get('classification')} ({int(res.get('vision_analysis', {}).get('confidence_score', 0)*100)}%)")
    print(f"Retur kod: {res.get('return_logistics', {}).get('return_code')}")
    print(f"Rendezes: {res.get('resolution', {}).get('title')} -> {res.get('resolution', {}).get('coupon_code')} ({res.get('resolution', {}).get('total_credit_value_huf')} Ft)")
    
    assert res.get("status") == "success"
    assert res.get("vision_analysis", {}).get("classification") == "MANUFACTURING_DEFECT"
    assert res.get("return_logistics", {}).get("return_code") is not None
    assert res.get("resolution", {}).get("total_credit_value_huf") == 53790
    print("[OK] Teszt 1 sikeresen lefutott!")


def test_scenario_2_keep_the_item_low_value():
    print("\n--- TESZT 2: Keep-the-Item (< 15 000 Ft gazdasagossagi szabaly) ---")
    payload = {
        "claim_id": "CLM-2026-8942",
        "customer": {
            "name": "Nagy Eva",
            "email": "nagy.eva@pelda.hu",
            "phone": "+36209876543"
        },
        "order": {
            "order_number": "ORD-2026-0312",
            "invoice_number": "SZAMLA-2026-0184",
            "purchase_date": "2026-01-20",
            "item_sku": "PHILIPS-HUE-BULB",
            "item_name": "Philips Hue White E27 Okos Izzon",
            "item_price_gross_huf": 9800,
            "serial_number": "SN-PH-19482"
        },
        "complaint": {
            "issue_description": "A burkolat alatt a gyari LED panel megszakadt, bekapcsolaskor nem vilagit a lampa.",
            "photo_urls": ["https://storage.webshop.hu/claims/CLM-2026-8942/led_hiba.jpg"],
            "preferred_return_channel": "foxpost_box",
            "preferred_resolution": "instant_replacement_order"
        },
        "config": {
            "verification_mode": "hybrid_smart_rule",
            "keep_the_item_threshold_huf": 15000,
            "approval_gate": "autonomous"
        }
    }
    
    res = run(payload)
    print(f"Keep-the-Item aktivalva: {res.get('keep_the_item', {}).get('enabled')}")
    print(f"Indoklas: {res.get('keep_the_item', {}).get('reason')}")
    print(f"Retur csatorna: {res.get('return_logistics', {}).get('channel_title')}")
    print(f"Csere rendeles azonosito: {res.get('resolution', {}).get('replacement_order_id')}")
    
    assert res.get("keep_the_item", {}).get("enabled") is True
    assert res.get("return_logistics", {}).get("courier_cost_saved_huf") == 2200
    print("[OK] Teszt 2 sikeresen lefutott!")


def test_scenario_3_user_mishandling_rejection():
    print("\n--- TESZT 3: Nem rendeltetesszeru hasznalat (beazas / garanciavesztes) ---")
    payload = {
        "claim_id": "CLM-2026-8943",
        "customer": {
            "name": "Toth Bela",
            "email": "toth.bela@pelda.hu",
            "phone": "+36703334444"
        },
        "order": {
            "order_number": "ORD-2025-4491",
            "invoice_number": "SZAMLA-2025-3310",
            "purchase_date": "2025-06-10",
            "item_sku": "MAKITA-DGA-504",
            "item_name": "Makita Akkus Sarokcsiszolon",
            "item_price_gross_huf": 62900,
            "serial_number": "SN-MK-5591"
        },
        "complaint": {
            "issue_description": "Az esoben kint hagytuk a teton, teljesen beazott a gep, viz folyik belole es leejtettuk a foldre.",
            "photo_urls": ["https://storage.webshop.hu/claims/CLM-2026-8943/beazas_serules.jpg"]
        },
        "config": {
            "approval_gate": "hybrid_confidence_threshold"
        }
    }
    
    res = run(payload)
    print(f"Besorolas: {res.get('vision_analysis', {}).get('classification')}")
    print(f"Garancia fedezi-e: {res.get('vision_analysis', {}).get('is_warranty_covered')}")
    print(f"Rendezes cime: {res.get('resolution', {}).get('title')}")
    
    assert res.get("vision_analysis", {}).get("is_warranty_covered") is False
    assert res.get("resolution", {}).get("payout_status") == "REJECTED_USER_FAULT"
    print("[OK] Teszt 3 sikeresen lefutott!")


def test_scenario_4_gls_pick_and_return_refund():
    print("\n--- TESZT 4: GLS Pick & Return futar + Billingo/Szamlazz.hu jovairo szamla ---")
    payload = {
        "claim_id": "CLM-2026-8944",
        "customer": {
            "name": "Kiss Andrea",
            "email": "kiss.andrea@pelda.hu",
            "phone": "+36309998877",
            "zip": "6720",
            "city": "Szeged",
            "address": "Tisza Lajos krt. 33."
        },
        "order": {
            "order_number": "ORD-2026-0518",
            "invoice_number": "SZAMLA-2026-0412",
            "purchase_date": "2026-02-15",
            "item_sku": "DEWALT-DCD-796",
            "item_name": "DeWalt DCD796P2 Akkus Ufuro",
            "item_price_gross_huf": 89900,
            "serial_number": "SN-DW-88910"
        },
        "complaint": {
            "issue_description": "Szallitas kozben a doboz osszenyomodott, a keszulekhaz repedt es a toltotartaly eltorott.",
            "photo_urls": ["https://storage.webshop.hu/claims/CLM-2026-8944/doboz_toreset.jpg"],
            "preferred_return_channel": "gls_pick_and_return",
            "preferred_resolution": "credit_note_refund"
        },
        "config": {
            "approval_gate": "autonomous"
        }
    }
    
    res = run(payload)
    print(f"Futar foglalasi azonosito: {res.get('return_logistics', {}).get('booking_reference')}")
    print(f"Futar idosav: {res.get('return_logistics', {}).get('time_window')}")
    print(f"Jovairo szamla: {res.get('resolution', {}).get('credit_note_number')} ({res.get('resolution', {}).get('refund_amount_huf')} Ft)")
    print(f"Hivatalos jegyzokonyv: {res.get('official_protocol', {}).get('protocol_id')}")
    
    assert res.get("return_logistics", {}).get("booking_reference") is not None
    assert res.get("resolution", {}).get("refund_amount_huf") == 89900
    assert "JEGYZOKONYV" in res.get("official_protocol", {}).get("protocol_id")
    print("[OK] Teszt 4 sikeresen lefutott!")


if __name__ == "__main__":
    print("=== MODULE 4.09: GARANCIALIS REKLAMACIO & VISSZARU MOCK TESZT ===")
    test_scenario_1_manufacturing_defect_foxpost()
    test_scenario_2_keep_the_item_low_value()
    test_scenario_3_user_mishandling_rejection()
    test_scenario_4_gls_pick_and_return_refund()
    print("\n[MINDEN TESZT SIKERESEN LEFUTOTT!]")
