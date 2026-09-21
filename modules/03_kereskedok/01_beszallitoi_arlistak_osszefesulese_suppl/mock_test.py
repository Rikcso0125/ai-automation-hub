"""
Beszállítói Árlisták Összefésülése & Árrésvédelem - Komprehenzív Mock Teszt
Modul: 01_beszallitoi_arlistak_osszefesulese_suppl
"""
import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from handler import SupplierFeedHarmonizerHandler, run

def run_all_tests():
    print("=" * 65)
    print(">>> [TESZT] 01_beszallitoi_arlistak_osszefesulese_suppl")
    print("=" * 65)

    handler = SupplierFeedHarmonizerHandler()

    # TESZT 1: Feed feldolgozása, árfolyamváltás és veszteséges tétel észlelése
    print("[1. TESZT] Beszállítói feed beolvasása, Smart Field Mapping & Árrésvédelem...")
    feed_payload = {
        "action": "HARMONIZE_FEED",
        "supplier_name": "EuroGépész Nagyker Kft.",
        "feed_source": "heti_arlista_2026w38.xlsx",
        "currency": "HUF",
        "feed_items": [
            {
                "cikkszam": "CU-PIPE-15",
                "termek_nev": "15x1 mm Rézcső szálban",
                "beszerzesi_ar": 2750,
                "valuta": "HUF"
            },
            {
                "cikkszam": "VALVE-BRASS-12",
                "termek_nev": "1/2 colos olasz réz golyóscsap",
                "beszerzesi_ar": 1720,
                "valuta": "HUF"
            },
            {
                "cikkszam": "PUMP-GRUNDFOS-25",
                "termek_nev": "Grundfos Alpha keringető",
                "beszerzesi_ar": 175.0,
                "valuta": "EUR"
            }
        ]
    }
    res1 = handler.execute(feed_payload)
    assert res1["status"] == "success", f"Hibás státusz: {res1.get('status')}"
    summary = res1["summary"]
    print(f"   [OK] Feldolgozott tételek: {summary['total_items_processed']} db")
    print(f"   [OK] Áremelkedések száma: {summary['price_increase_count']} db")
    print(f"   [OK] Veszélyesen ráfizetéses tételek: {summary['critical_loss_making_count']} db")
    assert summary["critical_loss_making_count"] >= 1, "Nem ismerte fel a CU-PIPE-15 ráfizetéses voltát!"
    print(f"   [OK] Megvédett árrés/profit: {summary['profit_protected_huf']:,} Ft")
    print(f"   [OK] 1-Kattintásos jóváhagyási link: {res1['one_click_approval_url']}")

    # TESZT 2: EUR devizakonverzió és javasolt ár ellenőrzése
    print("\n[2. TESZT] EUR deviza átszámítás és javasolt eladási ár kalkuláció...")
    pump_item = next(i for i in res1["harmonized_items"] if i["sku"] == "PUMP-GRUNDFOS-25")
    expected_cost = round(175.0 * 412.5)
    assert pump_item["new_cost_huf"] == expected_cost, f"Hibás EUR számítás: {pump_item['new_cost_huf']} != {expected_cost}"
    assert pump_item["recommended_price_huf"] > pump_item["new_cost_huf"], "A javasolt ár nem magasabb a beszerzési árnál!"
    print(f"   [OK] EUR konverzió (175 EUR * 412.5): {pump_item['new_cost_huf']:,} Ft")
    print(f"   [OK] Javasolt új eladási ár (haszonkulccsal): {pump_item['recommended_price_huf']:,} Ft")

    # TESZT 3: Vezetői jóváhagyási kapu (Batch Approval & Terméktörzs frissítés)
    print("\n[3. TESZT] Vezetői jóváhagyás (Batch Approval -> ERP & Terméktörzs szinkron)...")
    batch_id = res1["batch_id"]
    approve_payload = {
        "action": "APPROVE_BATCH",
        "batch_id": batch_id
    }
    res3 = handler.execute(approve_payload)
    assert res3["status"] == "success", f"Jóváhagyási hiba: {res3.get('message')}"
    print(f"   [OK] {res3['message']}")
    print(f"   [OK] Frissített termékek a törzsben: {res3['updated_products_count']} db")

    # Audit napló és terméktörzs ellenőrzése
    with open("data/termektorzs_katalogus.json", "r", encoding="utf-8") as f:
        catalog = json.load(f)
    cu_pipe = next(c for c in catalog if c["sku"] == "CU-PIPE-15")
    assert cu_pipe["current_cost_huf"] == 2750, f"Nem frissült a rézcső beszerzési ára: {cu_pipe['current_cost_huf']}"
    print(f"   [OK] Terméktörzs sikeresen frissítve: CU-PIPE-15 új eladási ár = {cu_pipe['current_price_huf']:,} Ft")

    print("\n" + "=" * 65)
    print(">>> MINDEN TESZT SIKERESEN LEFUTOTT! (01_beszallitoi_arlistak)")
    print("=" * 65)

if __name__ == "__main__":
    run_all_tests()
