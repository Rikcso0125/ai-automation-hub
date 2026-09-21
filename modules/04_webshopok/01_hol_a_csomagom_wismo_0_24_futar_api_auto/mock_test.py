# -*- coding: utf-8 -*-
"""
Mock test for Module 4.01: WISMO 0-24 Futar API Autopilot
Tests multi-attribute search, omnichannel responses, and proactive exception handling.
"""
import sys
import os
import json

# Import local handler directly
sys.path.insert(0, os.path.dirname(__file__))
from handler import run

def test_wismo_flows():
    print("==================================================")
    print("TESZT: Module 4.01 - WISMO 0-24 Futar API Autopilot")
    print("==================================================")

    # Test Case 1: Active In-Transit Package (Tracking Number Search)
    payload_transit = {
        "inquiry": {
            "search_key": "GLS-HU-987654321",
            "channel": "webchat",
            "customer_query": "Szia, merre jár a GLS csomagom?",
            "customer_name": "Kovács János"
        }
    }

    print("\n1. Teszt: Csomagkovetes modszere (Tracking szam alapjan - GLS folyamatban)")
    res1 = run(payload_transit)
    print(f"Status: {res1.get('status')}")
    inq1 = res1.get("processed_inquiries", [])[0]
    pkg1 = inq1.get("package_found", {})
    print(f"Futar: {pkg1.get('carrier')} | Allapot: {pkg1.get('status_label')}")
    print(f"Becsult erkezes: {pkg1.get('estimated_delivery_window')}")
    print(f"Webchat valasz: {inq1.get('primary_reply')[:90]}...")
    assert res1.get("status") == "success", "Test 1 failed!"
    assert pkg1.get("carrier") == "GLS", "Carrier detection mismatch!"
    print("[OK] GLS Tracking azonositas es 0-24 azonnali chat valasz sikeres!")

    # Test Case 2: Multi-attribute search by Customer Phone / Email
    payload_multi = {
        "inquiries": [
            {
                "channel": "email",
                "customer_email": "toth.eva@example.hu",
                "customer_query": "Jó napot! Megérkezett már a Foxpost automatába a csomag?",
                "search_key": "ORD-WEB-2026-9912"
            }
        ]
    }

    print("\n2. Teszt: Multi-attribute kereses (Email + Rendeles azonosito)")
    res2 = run(payload_multi)
    inq2 = res2.get("processed_inquiries", [])[0]
    pkg2 = inq2.get("package_found", {})
    omni = inq2.get("omnichannel_payloads", {})
    print(f"Azonositott csomagszam: {pkg2.get('tracking_number')}")
    print(f"Kezelt kommunikacios csatornak: {list(omni.keys())}")
    assert "email_body" in omni, "Email message missing!"
    assert "sms_text" in omni, "SMS message missing!"
    print("[OK] Multi-attribute kereses es Omnichannel valasz sablonok generalva!")

    # Test Case 3: Delivery Exception (Sikertelen kezbesites / Proaktiv akcio)
    payload_exception = {
        "inquiry": {
            "channel": "sms",
            "search_key": "DPD-HU-987654321",
            "customer_phone": "+36 20 444 7890",
            "customer_query": "Nem jött meg a futár tegnap."
        }
    }

    print("\n3. Teszt: Kezbesitesi akadalyt detektalo kivetelkezeles (Exception flow)")
    res3 = run(payload_exception)
    inq3 = res3.get("processed_inquiries", [])[0]
    exception_info = inq3.get("exception_handling", {})
    print(f"Kivetel detektalva: {exception_info.get('has_exception')}")
    print(f"Kivetel oka: {exception_info.get('reason')}")
    print(f"1-kattintasos cimmodositas / ujrakuldes link: {exception_info.get('redelivery_link')}")
    print(f"Automata ugyfelszolgalati eszkalacio: {exception_info.get('escalation_ticket_id')}")
    assert exception_info.get("has_exception") is True, "Exception was not flagged!"
    assert exception_info.get("escalation_ticket_id") is not None, "Escalation ticket was not generated!"
    print("[OK] Proaktiv kivetelkezeles es 24h eszkalacios jegy sikeresen legeneralva!")

    print("\n==================================================")
    print("MINDEN WISMO TESZTESET SIKERESEN LEFUTOTT! (3/3)")
    print("==================================================")

if __name__ == "__main__":
    test_wismo_flows()
