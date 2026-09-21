# -*- coding: utf-8 -*-
"""
Mock test for Module 4.02: Többcsatornás Készlet- és Árszinkron (Webshop + eMAG + Alza + POS)
Tests:
1. Fix puffer és túladás-védelem (alacsony készletnél piactéri nullázás).
2. Jutalékkal növelt árrésvédett árképzés és csatornaszabályok.
3. POS fizikai kassza eladás és hibrid szinkronizáció <3s SLA-val.
"""
import sys
import os
import json

# Import local handler directly
sys.path.insert(0, os.path.dirname(__file__))
from handler import run

def test_stock_sync():
    print("==================================================")
    print("TESZT: Module 4.02 - Többcsatornás Készlet- és Árszinkron")
    print("==================================================")

    # 1. Teszt: Fix puffer és túladás-védelem alacsony készletnél
    payload_buffer = {
        "event_type": "ORDER_PLACED",
        "source_channel": "webshop",
        "event_data": {
            "sku": "MAKITA-DHP-484",
            "quantity": 1
        },
        "config": {
            "buffer_stock_mode": "fixed_buffer",
            "buffer_threshold": 2
        }
    }

    print("\n1. Teszt: Fix puffer stratégia (Makita készlet <= 2 db esetén)")
    res1 = run(payload_buffer)
    assert res1.get("status") == "success", "Test 1 failed!"
    sync1 = res1.get("sync_result", {})
    inv1 = sync1.get("inventory_state", {})
    vis1 = inv1.get("channel_visibility", {})
    flags1 = sync1.get("system_flags", [])
    print(f"Eredeti raktárkészlet módosulás után elérhető: {inv1.get('available_stock')} db")
    print(f"Csatornák látható készlete: Webshop={vis1.get('webshop')} db | POS={vis1.get('pos')} db | eMAG={vis1.get('emag')} db | Alza={vis1.get('alza')} db")
    print(f"Rendszer zászlók: {flags1}")
    assert vis1.get("emag") == 0, "eMAG stock should be zeroed to protect from overselling!"
    assert vis1.get("alza") == 0, "Alza stock should be zeroed to protect from overselling!"
    assert vis1.get("webshop") > 0, "Webshop should keep remaining units!"
    print("[OK] Piactéri készletnullázás és kötbérvédelem sikeresen érvényesült!")

    # 2. Teszt: Jutalékkal növelt árrésvédett árképzés
    payload_pricing = {
        "event_type": "ORDER_PLACED",
        "source_channel": "emag",
        "event_data": {
            "sku": "BOSCH-GSR-18V-55",
            "quantity": 1
        },
        "config": {
            "pricing_mode": "margin_protected",
            "min_floor_margin_pct": 12.0
        }
    }

    print("\n2. Teszt: Csatornánkénti jutalék-kompenzált árrésvédelem (eMAG +16%, Alza +14%)")
    res2 = run(payload_pricing)
    sync2 = res2.get("sync_result", {})
    prices2 = sync2.get("pricing_state", {}).get("channel_prices_gross", {})
    margins2 = sync2.get("pricing_state", {}).get("channel_margins_pct", {})
    print(f"Eladási bruttó árak: Webshop={prices2.get('webshop')} Ft | eMAG={prices2.get('emag')} Ft | Alza={prices2.get('alza')} Ft")
    print(f"Számított tiszta árrések: Webshop={margins2.get('webshop')}% | eMAG={margins2.get('emag')}% | Alza={margins2.get('alza')}%")
    assert prices2.get("emag") > prices2.get("webshop"), "eMAG price must be higher to cover commission!"
    assert prices2.get("alza") > prices2.get("webshop"), "Alza price must be higher to cover commission!"
    assert all(m >= 12.0 for m in margins2.values()), "All margins must exceed min floor margin!"
    print("[OK] Jutalékvédelem sikeres, nettó profit minden felületen garantált!")

    # 3. Teszt: POS Fizikai Kassza Eladás és Hibrid Szinkron (<3s SLA)
    payload_pos = {
        "event_type": "POS_SALE",
        "source_channel": "pos",
        "event_data": {
            "sku": "BOSCH-GSR-18V-55",
            "quantity": 3
        },
        "config": {
            "pos_sync_mode": "hybrid",
            "low_stock_threshold": 5
        }
    }

    print("\n3. Teszt: Fizikai kassza (POS) eladás és azonnali hibrid szinkron leküldés")
    res3 = run(payload_pos)
    sync3 = res3.get("sync_result", {})
    pos_status = sync3.get("pos_sync_status", {})
    sla_info = sync3.get("execution_sla", {})
    dispatch = sync3.get("dispatch_results", {})
    print(f"POS Szinkron Státusz: {pos_status.get('status')}")
    print(f"Végrehajtási idő: {sla_info.get('elapsed_ms')} ms (Garantált SLA: <{sla_info.get('target_sla_ms')} ms)")
    print(f"Célcsatornák frissítve: {list(dispatch.keys())}")
    assert sla_info.get("sla_met") is True, "SLA exceeded!"
    assert "TRIGGERED_INSTANT_PUSH" in pos_status.get("status", ""), "Low stock should trigger instant push!"
    print("[OK] POS kassza eladás valós időben, 3 másodpercen belül szinkronizálva!")

    print("\n==================================================")
    print("MINDEN TÖBBCSATORNÁS SZINKRON TESZT SIKERESEN LEFUTOTT! (3/3)")
    print("==================================================")

if __name__ == "__main__":
    test_stock_sync()
