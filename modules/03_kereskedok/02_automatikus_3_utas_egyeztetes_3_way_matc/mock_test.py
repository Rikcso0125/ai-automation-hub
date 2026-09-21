"""
Automatikus 3-Utas Egyeztetés & Csalásszűrés - Komprehenzív Mock Teszt
Modul: 02_automatikus_3_utas_egyeztetes_3_way_matc
"""
import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from handler import ThreeWayMatchingHandler, run

def run_all_tests():
    print("=" * 65)
    print(">>> [TESZT] 02_automatikus_3_utas_egyeztetes_3_way_matc")
    print("=" * 65)

    handler = ThreeWayMatchingHandler()

    # TESZT 1: Túlszámlázás és Mennyiségi hiány észlelése
    print("[1. TESZT] Túlszámlázás és mennyiségi hiány detektálása...")
    discrepancy_payload = {
        "action": "RECONCILE_3WAY",
        "invoice": {
            "invoice_number": "SZAMLA-2026-DISC-01",
            "supplier_name": "EuroGépész Nagyker Kft.",
            "supplier_iban": "HU42 1170 5008 2011 2233 4455 6677",
            "total_net": 367500,
            "items": [
                {
                    "sku": "CU-PIPE-15",
                    "name": "15x1 mm Rézcső",
                    "quantity": 100,
                    "unit_price": 2750,
                    "line_net": 275000
                },
                {
                    "sku": "VALVE-BRASS-12",
                    "name": "1/2 colos golyóscsap",
                    "quantity": 50,
                    "unit_price": 1850,
                    "line_net": 92500
                }
            ]
        },
        "purchase_order": {
            "po_number": "PO-2026-0412",
            "registered_iban": "HU42 1170 5008 2011 2233 4455 6677",
            "items": [
                {"sku": "CU-PIPE-15", "quantity": 100, "approved_unit_price": 2750},
                {"sku": "VALVE-BRASS-12", "quantity": 50, "approved_unit_price": 1650}
            ]
        },
        "goods_receipt": {
            "receipt_number": "BEVET-1102",
            "items": [
                {"sku": "CU-PIPE-15", "accepted_qty": 85},
                {"sku": "VALVE-BRASS-12", "accepted_qty": 50}
            ]
        }
    }
    res1 = handler.execute(discrepancy_payload)
    assert res1["status"] == "success"
    assert res1["reconciliation_status"] == "DISCREPANCY_PAYMENT_HOLD"
    assert res1["payment_authorized"] is False
    overbilled = res1["summary"]["overbilled_huf"]
    # CU-PIPE-15 hiány: 15 db * 2750 = 41250 Ft. VALVE-BRASS-12 felár: 50 db * 200 = 10000 Ft. Összesen: 51250 Ft.
    assert overbilled == 51250.0, f"Hibás túlszámlázási összeg: {overbilled} != 51250"
    assert len(res1["dispute_letter_for_supplier"]) > 100
    print(f"   [OK] Státusz: {res1['reconciliation_status']} | Fizetés zárolva: IGEN")
    print(f"   [OK] Azonosított túlszámlázás: {overbilled:,} Ft nettó")
    print(f"   [OK] Hivatalos kifogásolási levél és jóváíró számla igény legenerálva.")

    # TESZT 2: IBAN Számlacsalás kísérlet kivédése (Fraud Guard)
    print("\n[2. TESZT] IBAN Számlacsalás kísérlet kiszűrése (Csaló bankszámlaszám)...")
    fraud_payload = {
        "action": "RECONCILE_3WAY",
        "invoice": {
            "invoice_number": "SZAMLA-2026-FRAUD-02",
            "supplier_name": "EuroGépész Nagyker Kft.",
            "supplier_iban": "HU99 9999 8888 7777 6666 5555 4444",  # Csaló IBAN!
            "total_net": 100000,
            "items": [{"sku": "CU-PIPE-15", "quantity": 10, "unit_price": 2750}]
        },
        "purchase_order": {
            "po_number": "PO-2026-9999",
            "registered_iban": "HU42 1170 5008 2011 2233 4455 6677",  # Valódi regisztrált IBAN
            "items": [{"sku": "CU-PIPE-15", "quantity": 10, "approved_unit_price": 2750}]
        },
        "goods_receipt": {
            "receipt_number": "BEVET-9999",
            "items": [{"sku": "CU-PIPE-15", "accepted_qty": 10}]
        }
    }
    res2 = handler.execute(fraud_payload)
    assert res2["fraud_risk_detected"] is True
    assert res2["reconciliation_status"] == "SUSPECTED_FRAUD_PAYMENT_FROZEN"
    assert res2["payment_authorized"] is False
    print(f"   [OK] Csalásszűrő azonnal zárolta: {res2['reconciliation_status']}")
    print(f"   [OK] Vészjelzés: {res2['fraud_message']}")

    # TESZT 3: 100%-os Hibátlan Egyezés (Automatikus fizetési jóváhagyás)
    print("\n[3. TESZT] 100%-os hibátlan 3-utas egyezés (Auto-Approve)...")
    clean_payload = {
        "action": "RECONCILE_3WAY",
        "invoice": {
            "invoice_number": "SZAMLA-2026-CLEAN-03",
            "supplier_name": "EuroGépész Nagyker Kft.",
            "supplier_iban": "HU42 1170 5008 2011 2233 4455 6677",
            "total_net": 275000,
            "items": [{"sku": "CU-PIPE-15", "quantity": 100, "unit_price": 2750}]
        },
        "purchase_order": {
            "po_number": "PO-2026-CLEAN",
            "registered_iban": "HU42 1170 5008 2011 2233 4455 6677",
            "items": [{"sku": "CU-PIPE-15", "quantity": 100, "approved_unit_price": 2750}]
        },
        "goods_receipt": {
            "receipt_number": "BEVET-CLEAN",
            "items": [{"sku": "CU-PIPE-15", "accepted_qty": 100}]
        }
    }
    res3 = handler.execute(clean_payload)
    assert res3["reconciliation_status"] == "PERFECT_MATCH_APPROVED_FOR_PAYMENT"
    assert res3["payment_authorized"] is True
    print(f"   [OK] Státusz: {res3['reconciliation_status']}")
    print(f"   [OK] Fizetés engedélyezve: IGEN")

    # TESZT 4: Gazdasági vezetői kézi felülbírálat (Override)
    print("\n[4. TESZT] Gazdasági vezetői felülbírálati kapu tesztelése...")
    rec_id = res1["reconciliation_id"]
    override_payload = {
        "action": "OVERRIDE_APPROVAL",
        "reconciliation_id": rec_id,
        "reason": "Beszállító kiállította a CN-991 jóváíró számlát, fizetés engedélyezve"
    }
    res4 = handler.execute(override_payload)
    assert res4["status"] == "success"
    assert res4["payment_authorized"] is True
    print(f"   [OK] {res4['message']}")

    # Adatbázis ellenőrzése
    db_path = Path("data/3way_matching_naplo.json")
    assert db_path.exists(), "A 3-way matching napló nem jött létre!"
    with open(db_path, "r", encoding="utf-8") as f:
        logs = json.load(f)
    print(f"   [OK] Perzisztens naplóban tárolt audit egyeztetések száma: {len(logs)}")

    print("\n" + "=" * 65)
    print(">>> MINDEN TESZT SIKERESEN LEFUTOTT! (02_automatikus_3_utas_egyeztetes)")
    print("=" * 65)

if __name__ == "__main__":
    run_all_tests()
