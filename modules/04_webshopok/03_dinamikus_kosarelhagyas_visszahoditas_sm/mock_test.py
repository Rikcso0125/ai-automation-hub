# -*- coding: utf-8 -*-
"""
Mock test for Module 4.03: Dinamikus Kosárelhagyás Visszahódítás (SMS és Email)
Tests:
1. Szerkeszthető 2-lépcsős szekvencia és 1-kattintásos restore direkt link (A opció).
2. Saját szerkesztésű ösztönző szabályok és kategória-specifikus aggálykezelés.
3. Kupon nélküli tiszta érték- és garanciafókuszú visszahódítás.
"""
import sys
import os
import json

# Import local handler directly
sys.path.insert(0, os.path.dirname(__file__))
from handler import run

def test_abandoned_cart_recovery():
    print("==================================================")
    print("TESZT: Module 4.03 - Dinamikus Kosarelhagyas Visszahoditas")
    print("==================================================")

    # 1. Teszt: Szerkeszthető 2-lépcsős szekvencia és 1-kattintásos restore direkt link
    payload_step1 = {
        "cart_session_id": "CART-SESS-982314",
        "customer": {
            "name": "Nagy Zoltán",
            "email": "nagy.zoltan@example.hu",
            "phone": "+36309876543"
        },
        "cart_items": [
            {
                "sku": "MAKITA-DHP-484",
                "name": "Makita DHP484Z Akkus Ütvefúró",
                "category": "szerszamgep",
                "quantity": 1,
                "unit_price_gross": 64990,
                "stock_remaining": 2
            }
        ],
        "config": {
            "sms_delay_minutes": 20,
            "email_delay_hours": 12,
            "incentive_mode": "tiered_discount"
        }
    }

    print("\n1. Teszt: Szerkeszthető 2-lépcsős szekvencia (SMS 20p + Email 12h + 1-kattintásos link)")
    res1 = run(payload_step1)
    assert res1.get("status") == "success", "Test 1 failed!"
    rec1 = res1.get("recovery_data", {})
    steps1 = rec1.get("sequence_steps", [])
    print(f"Vásárló: {rec1.get('customer', {}).get('name')}")
    print(f"Kosárérték: {rec1.get('cart_total_gross_huf')} Ft | Fő termék: {rec1.get('hero_product')}")
    print(f"1-kattintásos kosár-visszaállító link: {rec1.get('restore_cart_url')}")
    print(f"1. Lépés (SMS ütemezés): {steps1[0].get('scheduled_at')} ({steps1[0].get('delay_minutes')} perc múlva)")
    print(f"SMS Szöveg: {steps1[0].get('content')}")
    print(f"2. Lépés (Email ütemezés): {steps1[1].get('scheduled_at')} ({steps1[1].get('delay_hours')} óra múlva)")
    assert len(steps1) == 2, "Expected 2 steps in sequence!"
    assert "https://profigepesz.hu/cart/restore" in rec1.get("restore_cart_url"), "Invalid restore link!"
    assert steps1[0].get("delay_minutes") == 20, "SMS delay custom editing failed!"
    print("[OK] Szerkeszthető 2-lépcsős szekvencia és direkt visszaállító link sikeresen legenerálva!")

    # 2. Teszt: Saját szerkesztésű ösztönző és kategória-specifikus aggálykezelés
    payload_custom = {
        "cart_session_id": "CART-VIP-7788",
        "customer": {
            "name": "Kovács Péter",
            "email": "kovacs.p@example.hu",
            "phone": "+36201234567"
        },
        "cart_items": [
            {
                "sku": "BOSCH-GSR-18V-55",
                "name": "Bosch Professional GSR 18V-55 Fúrócsavarozó",
                "category": "szerszamgep",
                "quantity": 1,
                "unit_price_gross": 54990
            }
        ],
        "config": {
            "incentive_mode": "custom_rules",
            "custom_rules": [
                {
                    "min_cart_value": 50000,
                    "coupon_code": "SAJATVIP10",
                    "discount_label": "10% Extra Kupon",
                    "highlight_benefit": "3 év garancia és azonnali prémium futár"
                }
            ]
        }
    }

    print("\n2. Teszt: Saját szerkesztésű szabályzat (50 000 Ft felett SAJATVIP10)")
    res2 = run(payload_custom)
    rec2 = res2.get("recovery_data", {})
    inc2 = rec2.get("incentive_applied", {})
    print(f"Alkalmazott egyedi kupon: {inc2.get('coupon_code')} ({inc2.get('discount_label')})")
    print(f"Kiemelt előny: {inc2.get('benefit')}")
    assert inc2.get("coupon_code") == "SAJATVIP10", "Custom coupon rule was not applied!"
    print("[OK] Saját szerkesztésű ösztönző szabályzat hibátlanul érvényesült!")

    # 3. Teszt: Kupon nélküli tiszta értékajánlat és garanciafókusz
    payload_no_coupon = {
        "cart_session_id": "CART-NOCOUPON-11",
        "customer": {
            "name": "Szabó Anna",
            "email": "szabo.anna@example.hu",
            "phone": "+36709871122"
        },
        "cart_items": [
            {
                "sku": "BASIC-ITEM",
                "name": "Standard Kiegészítő Csomag",
                "category": "altalanos",
                "quantity": 2,
                "unit_price_gross": 12000
            }
        ],
        "config": {
            "incentive_mode": "no_coupon_value_only"
        }
    }

    print("\n3. Teszt: Kupon nélküli tiszta értékajánlat (nem szoktat leárazásra)")
    res3 = run(payload_no_coupon)
    rec3 = res3.get("recovery_data", {})
    inc3 = rec3.get("incentive_applied", {})
    print(f"Ösztönző mód: {inc3.get('discount_label')}")
    print(f"Kupon kód: {inc3.get('coupon_code')}")
    assert inc3.get("coupon_code") is None, "Coupon should be None in value-only mode!"
    print("[OK] Kuponmentes érték- és garanciaközpontú meggyőzés sikeres!")

    print("\n==================================================")
    print("MINDEN KOSARELHAGYAS TESZT SIKERESEN LEFUTOTT! (3/3)")
    print("==================================================")

if __name__ == "__main__":
    test_abandoned_cart_recovery()
