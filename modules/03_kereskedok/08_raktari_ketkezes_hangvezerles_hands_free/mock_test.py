"""
Automatizált Mock Teszt Modul 08:
Raktári Kétkezes Hangvezérlés (Hands-Free Voice Picking)
"""

import os
import sys
import json

curr_dir = os.path.dirname(os.path.abspath(__file__))
if curr_dir not in sys.path:
    sys.path.insert(0, curr_dir)

from handler import WarehouseVoicePickingHandler, run

def run_all_tests():
    print("=" * 65)
    print("[TESZT KEZDES] Modul 08: Raktari Hangvezerles Tesztcsomag")
    print("=" * 65)

    # 1. Payload betöltése
    payload_path = os.path.join(curr_dir, "test_payload.json")
    with open(payload_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    order_items = payload.get("order", {}).get("items", [])
    print(f"[1. TESZT] test_payload.json betoltve ({len(order_items)} tetel)")

    # 2. Alapértelmezett túra végrehajtása (check_digit, smart_adaptive, single_order)
    handler = WarehouseVoicePickingHandler({
        "service_mode": "mock",
        "verification_method": "check_digit",
        "shortage_strategy": "smart_adaptive",
        "picking_mode": "single_order"
    })
    res = handler.execute(payload)

    assert res.get("status") == "success", "Hiba: A tura nem success-szel vegzodott!"
    assert res.get("tour_status") == "COMPLETED", "Tura statusz hiba!"
    assert res["metrics"]["total_items_picked"] == 32, f"32 db tetelt vartunk, kapott: {res['metrics']['total_items_picked']}"
    assert res["metrics"]["accuracy_percent"] == 100.0, "Pontossag 100% kell legyen!"

    slip = res.get("packing_slip", {})
    assert slip.get("box_label") is not None, "Dobozcimke hianyzik!"
    print(f"[OK] Tura sikeresen lezarva: {res['order_id']} | Kiszedve: {res['metrics']['total_items_picked']} db | Doboz: {slip['box_label']['barcode']}")

    # 3. Útvonal-optimalizálás ellenőrzése (A-01 -> B-04 -> C-03)
    items_in_slip = slip.get("items", [])
    shelf_order = [it["shelf_location"] for it in items_in_slip]
    assert shelf_order == ["A-01-08", "B-04-12", "C-03-02"], f"Hibas utvonal sorrend: {shelf_order}"
    print(f"[OK] Szedesi utvonal logikusan optimalizalva polcrendszer szerint: {shelf_order}")

    # 4. Ellenőrzési mód tesztelése: sku_last_digits
    print("[2. TESZT] Ellenőrzési mód: sku_last_digits tesztelése...")
    handler_sku = WarehouseVoicePickingHandler({"verification_method": "sku_last_digits"})
    test_item = {"sku": "PUMP-GRUNDFOS-025", "name": "Szivattyú", "quantity_ordered": 1, "shelf_location": "B-01"}
    ok_sku, evt_sku, tts_sku = handler_sku._process_dialogue_step(test_item, "CONFIRM_LOCATION", "025", "sku_last_digits", "smart_adaptive")
    assert ok_sku is True, "SKU utolso 3 jegy ellenorzes nem sikerult!"
    assert evt_sku["event"] == "LOCATION_VERIFIED"
    print("[OK] sku_last_digits ellenorzesi mod tokeletesen mukodik")

    # 5. Készlethiány és sérüléskezelés tesztelése (smart_adaptive + backup shelf)
    print("[3. TESZT] Készlethiány kezelés tesztelése...")
    shortage_item = {
        "sku": "PUMP-GRUNDFOS-25",
        "name": "Keringető szivattyú",
        "quantity_ordered": 4,
        "shelf_location": "B-04-12",
        "check_digit": "42",
        "backup_shelf": "D-02-05"
    }
    ok_short, evt_short, tts_short = handler._process_dialogue_step(
        shortage_item,
        "CONFIRM_QUANTITY",
        "Csak kettő van",
        "check_digit",
        "smart_adaptive"
    )
    assert ok_short is True, "Hiany kezeles sikertelen!"
    assert evt_short["event"] == "SHORTAGE_REDIRECTED_TO_BACKUP"
    assert evt_short["picked_qty"] == 2
    assert evt_short["shortage_qty"] == 2
    assert evt_short["backup_shelf"] == "D-02-05"
    assert "D-02-05" in tts_short, "TTS atiranyitas hianyzik!"
    print(f"[OK] Keszlehiany eseten intelligens atiranyitas a tartalek polchoz ({evt_short['backup_shelf']})")

    # 6. Szedési mód: batch_wave tesztelése
    print("[4. TESZT] Szedési mód: batch_wave tesztelése...")
    payload_wave = dict(payload)
    payload_wave["picking_mode"] = "batch_wave"
    res_wave = handler.execute(payload_wave)
    assert res_wave["picking_mode"] == "batch_wave"
    print("[OK] batch_wave szedesi mod sikeresen lefutott")

    # 7. Tartós Napló (data/raktar_hangvezerles_naplo.json) ellenőrzése
    print("[5. TESZT] Tartós Adatbázis napló ellenőrzése...")
    db_path = "data/raktar_hangvezerles_naplo.json"
    assert os.path.exists(db_path), f"Hiba: {db_path} nem jott letre!"
    with open(db_path, "r", encoding="utf-8") as f:
        db_data = json.load(f)
    assert "warehouse_kpi" in db_data, "Hianyzo warehouse_kpi!"
    tot_tours = db_data["total_completed_tours"]
    tot_items = db_data["warehouse_kpi"]["total_items_picked_hands_free"]
    print(f"[OK] Adatbazis rendben ({db_path}) | Osszes tura: {tot_tours} | Kiszedett tetel: {tot_items} db")

    # 8. Szabványos run() függvény tesztelése
    print("[6. TESZT] Szabványos run() belépési pont tesztelése...")
    hub_res = run(payload)
    assert hub_res.get("status") == "success", "Hub run() hibat adott!"
    print("[OK] Hub run() fuggveny tokeletesen mukodik")

    print("=" * 65)
    print("[MINDEN TESZT SIKERESEN LEFUTOTT]")
    print("=" * 65)

if __name__ == "__main__":
    run_all_tests()