# -*- coding: utf-8 -*-
"""
Mock test for Module 4.08: Szemantikus Kereső & Webes Virtuális Eladó Bot
Tests:
1. Kötetlen vásárlói szándék felismerése és döntéstámogató összehasonlító mátrix.
2. Készlethiány detektálása és raktári egyenértékű alternatíva felajánlása.
3. Smart cross-sell tartozék csomagajánlás 1-kattintásos kosárba helyezéssel.
"""
import sys
import os
import json

# Import local handler directly
sys.path.insert(0, os.path.dirname(__file__))
from handler import run

def test_semantic_advisor():
    print("==================================================")
    print("TESZT: Module 4.08 - Szemantikus Kereso es Virtualis Elado")
    print("==================================================")

    # 1. Teszt: Kötetlen vásárlói szándék felismerése és összehasonlító mátrix
    payload_query = {
        "user_query": "olyan akkus gépet keresek, amivel panel betonfalba tudok polcot feltenni és kéne hozzá fúrószár is",
        "session_id": "SESS-CONCRETE-001",
        "config": {
            "search_mode": "hybrid_full_semantic",
            "ui_dialogue_mode": "comparative_decision_matrix",
            "cross_sell_mode": "combined_inventory_and_bundle"
        }
    }

    print("\n1. Teszt: Szemantikus szándékértelmezés (Panel betonfalhoz fúrás)")
    res1 = run(payload_query)
    assert res1.get("status") == "success", "Test 1 failed!"
    data1 = res1.get("advisor_result", {})
    intent1 = data1.get("intent_analysis", {})
    matrix1 = data1.get("comparative_matrix", [])
    print(f"Lekérdezés: {data1.get('user_query')}")
    print(f"Felismerve: Pneumatikus fúrókalapács szükséges = {intent1.get('requires_pneumatic_hammer')}")
    print(f"Szakértői indoklás: {intent1.get('expert_advice')[:110]}...")
    print(f"Összehasonlító mátrix tételei ({len(matrix1)} db):")
    for card in matrix1:
        print(f"  -> [{card.get('tier')}] {card.get('name')}: {card.get('price_gross_huf')} Ft (Raktáron: {card.get('stock_count')} db) | Link: {card.get('add_to_cart_url')}")
    assert intent1.get("requires_pneumatic_hammer") is True, "Intent failed to detect pneumatic hammer requirement!"
    assert len(matrix1) >= 2, "Matrix should contain multiple tiered options!"
    print("[OK] Szándékfelismerés és döntéstámogató termékkártyák sikeresen legenerálva!")

    # 2. Teszt: Készlethiány detektálása és raktáron lévő alternatíva
    alt1 = data1.get("alternative_replacement", {})
    print("\n2. Teszt: Készlethiány intelligens pótlása raktári alternatívával")
    print(f"Hiánycikk: {alt1.get('original_name')} ({alt1.get('original_requested_sku')})")
    print(f"Ajánlott azonnali cseregép: {alt1.get('recommended_name')} ({alt1.get('recommended_alternative_sku')})")
    print(f"Raktári készlet: {alt1.get('in_stock_units')} db")
    print(f"Indoklás a vevőnek: {alt1.get('explanation')}")
    assert alt1.get("recommended_alternative_sku") is not None, "Missing alternative recommendation!"
    assert alt1.get("in_stock_units") > 0, "Alternative must be in stock!"
    print("[OK] Raktári helyettesítő termék sikeresen felajánlva!")

    # 3. Teszt: Smart Cross-Sell tartozék csomagajánlás
    bundle1 = data1.get("smart_cross_sell_bundle", {})
    print("\n3. Teszt: Kompatibilis tartozék csomagajánlás (Smart Cross-Sell)")
    print(f"Kiegészítő: {bundle1.get('accessory_name')}")
    print(f"Eredeti ár: {bundle1.get('original_price_huf')} Ft -> Csomagár: {bundle1.get('bundle_price_huf')} Ft (Megtakarítás: {bundle1.get('savings_huf')} Ft)")
    print(f"Miért szükséges: {bundle1.get('why_needed')}")
    print(f"1-kattintásos csomag link: {bundle1.get('add_bundle_to_cart_url')}")
    assert bundle1.get("accessory_sku") is not None, "Missing bundle accessory!"
    assert "add-bundle?" in bundle1.get("add_bundle_to_cart_url"), "Invalid bundle URL!"
    print("[OK] Intelligens fúrószár-csomag ajánlat és kedvezmény sikeresen legenerálva!")

    print("\n==================================================")
    print("MINDEN SZEMANTIKUS KERESŐ TESZT SIKERESEN LEFUTOTT! (3/3)")
    print("==================================================")

if __name__ == "__main__":
    test_semantic_advisor()
