# -*- coding: utf-8 -*-
"""
Mock test for Module 4.04: Utánvét-Megerősítő és Csomagpont Átvételi SMS Értesítő
Tests:
1. Kockázatalapú utánvét (COD) előszűrés (1. Kérdés - B opció).
2. Nem megerősített rendelés csomagfeladási zárlata és ügyfélszolgálati riasztás (2. Kérdés - A opció).
3. Csomagautomata lejárati vészjelzés továbbítható átvételi meghatalmazással (3. Kérdés - C opció).
"""
import sys
import os
import json

# Import local handler directly
sys.path.insert(0, os.path.dirname(__file__))
from handler import run

def test_cod_and_locker_flows():
    print("==================================================")
    print("TESZT: Module 4.04 - Utanvet-Megerosito es Csomagpont Ertesito")
    print("==================================================")

    # 1. Teszt: Kockázatalapú utánvét előszűrés
    payload_risk = {
        "event_type": "VERIFY_COD_ORDER",
        "order": {
            "order_id": "ORD-COD-2026-8812",
            "payment_method": "cod",
            "total_gross_huf": 78900,
            "is_first_purchase": True,
            "customer": {
                "name": "Kovács Dániel",
                "phone": "+36307778899",
                "email": "dani_test99@tempmail.com",
                "shipping_address": {
                    "zip": "1118",
                    "city": "Budapest",
                    "street": "Rétköz utca",
                    "house_number": ""
                }
            }
        },
        "config": {
            "cod_risk_threshold": 45,
            "cod_high_value_limit_huf": 40000
        }
    }

    print("\n1. Teszt: Kockázatalapú utánvét szűrés (Új vevő + Nagy érték + Hiányos cím + Tempmail)")
    res1 = run(payload_risk)
    assert res1.get("status") == "success", "Test 1 failed!"
    data1 = res1.get("result", {})
    print(f"Kockázati pontszám: {data1.get('risk_score')} / 100 (Küszöb: {data1.get('risk_threshold')})")
    print(f"Azonosított kockázati tényezők: {data1.get('risk_factors')}")
    print(f"Fulfillment státusz: {data1.get('fulfillment_status')}")
    print(f"1-kattintásos megerősítő link: {data1.get('confirmation_link')}")
    print(f"SMS értesítő: {data1.get('sms_dispatch', {}).get('message')}")
    assert data1.get("requires_confirmation") is True, "High risk COD should require confirmation!"
    assert data1.get("risk_score") >= 45, "Risk score should exceed threshold!"
    assert data1.get("confirmation_link") is not None, "Missing confirmation link!"
    print("[OK] Kockázatalapú szűrés és 1-kattintásos vevői megerősítő kérés sikeres!")

    # 2. Teszt: Nem megerősített rendelés csomagfeladási zárlata
    payload_hold = {
        "event_type": "CHECK_UNCONFIRMED_ORDERS",
        "order_id": "ORD-COD-2026-8812",
        "order_data": {
            "customer": {"name": "Kovács Dániel", "phone": "+36307778899"},
            "total_gross_huf": 78900
        },
        "config": {
            "confirmation_grace_hours": 24
        }
    }

    print("\n2. Teszt: 24h megerősítés elmaradása miatti szállítási zárlat (Shipping Hold)")
    res2 = run(payload_hold)
    data2 = res2.get("result", {})
    ticket2 = data2.get("escalation_ticket", {})
    print(f"Szállítási zárlat aktív: {data2.get('shipping_hold_active')}")
    print(f"Címkenyomtatás engedélyezve: {data2.get('label_printing_allowed')}")
    print(f"Ügyfélszolgálati jegy: {ticket2.get('ticket_id')} ({ticket2.get('assigned_to')})")
    print(f"Előírt feladat: {ticket2.get('required_action')}")
    assert data2.get("shipping_hold_active") is True, "Shipping hold not triggered!"
    assert data2.get("label_printing_allowed") is False, "Label printing must be blocked!"
    print("[OK] Csomagfeladási zárlat érvényesült, potya futárdíj sikeresen megelőzve!")

    # 3. Teszt: Csomagautomata lejárati vészjelzés és továbbítható meghatalmazás
    payload_locker = {
        "event_type": "LOCKER_DEADLINE_ALERT",
        "locker_data": {
            "parcel_id": "FOX-HU-882211",
            "carrier": "Foxpost",
            "locker_name": "Budapest Mammut I. Bevásárlóközpont",
            "pickup_code": "482910",
            "deadline_datetime": "2026-09-21 20:00 (még 18 óra van hátra)",
            "customer": {
                "name": "Tóth Gábor",
                "phone": "+36301239876",
                "email": "toth.gabor@example.hu"
            }
        },
        "config": {
            "locker_warning_hours_before": 24
        }
    }

    print("\n3. Teszt: Csomagautomata 24h lejárati riasztás és továbbítható átvételi kód")
    res3 = run(payload_locker)
    data3 = res3.get("result", {})
    notifs3 = data3.get("notifications_dispatched", {})
    print(f"Vészjelzés kiküldve: {data3.get('alert_triggered')}")
    print(f"1-kattintásos továbbítható meghatalmazás link: {data3.get('proxy_pickup_url')}")
    print(f"SMS figyelmeztetés: {notifs3.get('sms', {}).get('content')}")
    print(f"Email tárgy: {notifs3.get('email', {}).get('subject')}")
    assert data3.get("alert_triggered") is True, "Locker alert not triggered!"
    assert "proxy?parcel=" in data3.get("proxy_pickup_url"), "Proxy pickup URL missing!"
    print("[OK] Csomagautomata lejárati riasztás és megosztható átvételi kártya sikeres!")

    print("\n==================================================")
    print("MINDEN UTÁNVÉT ÉS CSOMAGPONT TESZT SIKERESEN LEFUTOTT! (3/3)")
    print("==================================================")

if __name__ == "__main__":
    test_cod_and_locker_flows()
