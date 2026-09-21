# -*- coding: utf-8 -*-
"""
Mock teszt a Social Selling: Kommentbol Messenger / Instagram Vasarlasi Tolcser modulhoz.
4 kulonbozo uzleti forgatokonyv tesztelese:
1. Instagram erdeklodo komment (ar + szallitas + kupon) -> DM tolcser + public valasz
2. Egyetlen kulcsszavas komment ("KUPON") -> Azonnali villamkupon kiallitas
3. Pozitiv rajongoi komment ("Szuper gep, imadom! Top minoseg") -> Engagement tolcser
4. Spam komment ("Crypto promo follow me") -> Szures, tolcser letiltasa
"""

import sys
import os
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from handler import run


def test_scenario_1_high_intent_instagram():
    print("\n--- TESZT 1: Instagram erdeklodo komment (ar + kupon szandek) ---")
    payload = {
        "event_id": "EVT-IG-2026-001",
        "platform": "instagram",
        "post": {
            "post_id": "POST-IG-1102",
            "post_title": "Bosch Professional GBH 2-28 Furokalapacs L-BOXX",
            "featured_product_sku": "BOSCH-GBH-2-28",
            "featured_product_name": "Bosch GBH 2-28 Furokalapacs",
            "regular_price_huf": 68900
        },
        "comment": {
            "comment_id": "CMT-101",
            "username": "bence_diy",
            "user_full_name": "Bence",
            "comment_text": "Mennyibe kerul szallitassal egyutt, es van meg kupon hozza? Kerem a linket!"
        },
        "config": {
            "trigger_mode": "hybrid_smart_matching",
            "public_reply_strategy": "hybrid_safe_boost",
            "dm_funnel_type": "hybrid_omnichannel_funnel",
            "flash_coupon_percent": 10,
            "flash_coupon_validity_hours": 2,
            "auto_like_comment": True
        }
    }
    
    res = run(payload)
    print(f"Status: {res.get('status')}")
    print(f"Szandek: {res.get('intent_analysis', {}).get('intent')} ({int(res.get('intent_analysis', {}).get('confidence_score', 0)*100)}%)")
    print(f"Nyilvanos valasz: {res.get('public_comment_action', {}).get('reply_text')}")
    print(f"Lajkolva: {res.get('public_comment_action', {}).get('like_user_comment')}")
    print(f"DM Kupon: {res.get('private_dm_action', {}).get('flash_coupon', {}).get('code')} -> {res.get('private_dm_action', {}).get('flash_coupon', {}).get('discounted_price_huf')} Ft")
    print(f"Checkout link: {res.get('private_dm_action', {}).get('product_card', {}).get('direct_checkout_link')}")
    
    assert res.get("status") == "success"
    assert res.get("intent_analysis", {}).get("should_trigger_funnel") is True
    assert res.get("private_dm_action", {}).get("flash_coupon", {}).get("discounted_price_huf") == 62010
    print("[OK] Teszt 1 sikeresen lefutott!")


def test_scenario_2_keyword_only_kupon():
    print("\n--- TESZT 2: Egyetlen kulcsszavas komment (KUPON) ---")
    payload = {
        "event_id": "EVT-FB-2026-002",
        "platform": "facebook",
        "post": {
            "post_id": "POST-FB-449",
            "post_title": "Makita Akkus Csiszolo Tavaszi Vasar",
            "featured_product_sku": "MAK-DGA-504",
            "featured_product_name": "Makita DGA504 Sarokcsiszolo",
            "regular_price_huf": 54900
        },
        "comment": {
            "comment_id": "CMT-102",
            "username": "zoltan_epitesz",
            "user_full_name": "Zoltan",
            "comment_text": "KUPON"
        },
        "config": {
            "trigger_mode": "keyword_only",
            "flash_coupon_percent": 15
        }
    }
    
    res = run(payload)
    print(f"Status: {res.get('status')}")
    print(f"Szandek: {res.get('intent_analysis', {}).get('intent')}")
    print(f"Kupon ertek: -{res.get('private_dm_action', {}).get('flash_coupon', {}).get('discount_percent')}%")
    print(f"Kedvezmenyes ar: {res.get('private_dm_action', {}).get('flash_coupon', {}).get('discounted_price_huf')} Ft")
    
    assert res.get("status") == "success"
    assert res.get("private_dm_action", {}).get("flash_coupon", {}).get("discount_percent") == 15
    print("[OK] Teszt 2 sikeresen lefutott!")


def test_scenario_3_positive_engagement():
    print("\n--- TESZT 3: Pozitiv rajongoi komment ---")
    payload = {
        "event_id": "EVT-IG-2026-003",
        "platform": "instagram",
        "post": {
            "post_id": "POST-IG-991",
            "featured_product_name": "DeWalt Utofuron",
            "regular_price_huf": 79900
        },
        "comment": {
            "comment_id": "CMT-103",
            "username": "profi_mester",
            "comment_text": "Szuper gep, nagyon jo a minoseg es tartos!"
        },
        "config": {
            "trigger_mode": "ai_semantic_nlp"
        }
    }
    
    res = run(payload)
    print(f"Status: {res.get('status')}")
    print(f"Szandek: {res.get('intent_analysis', {}).get('intent')}")
    
    assert res.get("status") == "success"
    assert res.get("intent_analysis", {}).get("intent") == "POSITIVE_ENGAGEMENT"
    print("[OK] Teszt 3 sikeresen lefutott!")


def test_scenario_4_spam_filtering():
    print("\n--- TESZT 4: Spam komment kiszurese ---")
    payload = {
        "event_id": "EVT-IG-2026-004",
        "platform": "instagram",
        "post": {
            "post_id": "POST-IG-991"
        },
        "comment": {
            "comment_id": "CMT-104",
            "username": "crypto_bot_99",
            "comment_text": "Follow me for 100x crypto bitcoin trading signals!"
        },
        "config": {
            "trigger_mode": "hybrid_smart_matching"
        }
    }
    
    res = run(payload)
    print(f"Status: {res.get('status')}")
    print(f"Indoklas: {res.get('reason')}")
    
    assert res.get("status") == "ignored"
    assert "SPAM" in res.get("reason", "")
    print("[OK] Teszt 4 sikeresen lefutott!")


if __name__ == "__main__":
    print("=== MODULE 4.10: SOCIAL SELLING KOMMENTBOL DM MOCK TESZT ===")
    test_scenario_1_high_intent_instagram()
    test_scenario_2_keyword_only_kupon()
    test_scenario_3_positive_engagement()
    test_scenario_4_spam_filtering()
    print("\n[MINDEN TESZT SIKERESEN LEFUTOTT!]")
