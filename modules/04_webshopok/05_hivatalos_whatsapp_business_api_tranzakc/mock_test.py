# -*- coding: utf-8 -*-
"""
Mock test for Module 4.05: Hivatalos WhatsApp Business API Tranzakciós Vevőszolgálat
Tests:
1. Kimenő tranzakciós értesítés és Add-to-Order csomagbővítés.
2. Hibrid kézbesítés SMS tartalék útvonallal, ha a számon nincs WhatsApp fiók.
3. 0-24 bejövő AI csevegés érzékeny kérésnél jóváhagyási kapuval (HITL).
"""
import sys
import os
import json

# Import local handler directly
sys.path.insert(0, os.path.dirname(__file__))
from handler import run

def test_whatsapp_support_flows():
    print("==================================================")
    print("TESZT: Module 4.05 - WhatsApp Business API Vevoszolgalat")
    print("==================================================")

    # 1. Teszt: Kimenő tranzakciós értesítés és Add-to-Order csomagbővítés
    payload_outbound = {
        "event_type": "ORDER_CONFIRMATION_OUTBOUND",
        "order": {
            "order_id": "ORD-WEB-2026-7711",
            "customer_name": "Balogh Ádám",
            "customer_phone": "+36304445566",
            "has_whatsapp_account": True,
            "total_gross_huf": 49990,
            "carrier": "GLS",
            "items": [
                {
                    "sku": "BOSCH-GSR-18V-55",
                    "name": "Bosch Professional GSR 18V-55 Akkus Fúrócsavarozó",
                    "quantity": 1,
                    "price": 49990
                }
            ]
        },
        "config": {
            "template_delivery_mode": "interactive_buttons",
            "enable_add_to_order": True,
            "add_to_order_window_minutes": 15
        }
    }

    print("\n1. Teszt: Kimenő WhatsApp értesítő és 15 perces Add-to-Order csomagbővítés")
    res1 = run(payload_outbound)
    assert res1.get("status") == "success", "Test 1 failed!"
    data1 = res1.get("whatsapp_data", {})
    rep1 = data1.get("delivery_report", {})
    offer1 = data1.get("add_to_order_offer", {})
    print(f"Kézbesítési csatorna: {rep1.get('channel')} | Státusz: {rep1.get('status')}")
    print(f"Meta WAMID azonosító: {rep1.get('meta_wamid')}")
    print(f"Add-to-Order ajánlat aktív: {offer1.get('active')} ({offer1.get('time_window_minutes')} perc)")
    print(f"Ajánlott kiegészítő: {offer1.get('recommended_name')} ({offer1.get('special_price_huf')} Ft, Szállítás: {offer1.get('shipping_cost_huf')} Ft)")
    assert rep1.get("status") == "DELIVERED_TO_WHATSAPP", "Delivery failed!"
    assert offer1.get("active") is True, "Add-to-order not activated!"
    print("[OK] WhatsApp tranzakciós üzenet és Add-to-Order ajánlat sikeresen kiküldve!")

    # 2. Teszt: Hibrid SMS Fallback nem WhatsApp-képes számnál
    payload_fallback = {
        "event_type": "ORDER_CONFIRMATION_OUTBOUND",
        "order": {
            "order_id": "ORD-WEB-2026-7712",
            "customer_name": "Kiss Béla",
            "customer_phone": "+36208889900",
            "has_whatsapp_account": False,
            "total_gross_huf": 32000,
            "carrier": "Foxpost"
        },
        "config": {
            "template_delivery_mode": "hybrid_sms_fallback"
        }
    }

    print("\n2. Teszt: Hibrid kézbesítés (Telnyx SMS fallback WhatsApp hiányában)")
    res2 = run(payload_fallback)
    data2 = res2.get("whatsapp_data", {})
    rep2 = data2.get("delivery_report", {})
    print(f"Kézbesítési csatorna: {rep2.get('channel')}")
    print(f"Kiváltó ok: {rep2.get('reason')}")
    print(f"Kiküldött SMS: {rep2.get('sms_content')}")
    assert rep2.get("channel") == "SMS_FALLBACK_TELNYX", "SMS fallback should be triggered!"
    print("[OK] Hibrid SMS tartalék kézbesítés hibátlanul lefutott!")

    # 3. Teszt: Bejövő AI Csevegés és Jóváhagyási Kapu (HITL)
    payload_inbound = {
        "event_type": "CUSTOMER_MESSAGE_INBOUND",
        "message": {
            "sender_phone": "+36304445566",
            "text": "Szeretném módosítani a szállítási címet a Rétköz utca 14-re!",
            "order_reference": "ORD-WEB-2026-7711"
        },
        "config": {
            "ai_support_mode": "hitl_approval_gate"
        }
    }

    print("\n3. Teszt: Bejövő AI csevegés címváltoztatási kéréssel (Jóváhagyási Kapu)")
    res3 = run(payload_inbound)
    data3 = res3.get("whatsapp_data", {})
    res_obj3 = data3.get("resolution", {})
    card3 = res_obj3.get("human_approval_card", {})
    print(f"Felismert szándék: {data3.get('intent_detected')}")
    print(f"AI Hatáskör mód: {data3.get('ai_support_mode')}")
    print(f"Válasz státusz: {res_obj3.get('status')}")
    print(f"AI válaszpiszkozat: {res_obj3.get('ai_draft_response')}")
    print(f"Emberi jóváhagyási kártya: {card3.get('approve_button_url')}")
    assert data3.get("intent_detected") == "SENSITIVE_ORDER_MODIFICATION", "Wrong intent detected!"
    assert res_obj3.get("status") == "APPROVAL_CARD_CREATED", "Approval card should be created!"
    assert card3.get("approve_button_url") is not None, "Missing approval link!"
    print("[OK] Érzékeny ügyféli kérés jóváhagyási kapuval biztosítva!")

    print("\n==================================================")
    print("MINDEN WHATSAPP BUSINESS TESZT SIKERESEN LEFUTOTT! (3/3)")
    print("==================================================")

if __name__ == "__main__":
    test_whatsapp_support_flows()
