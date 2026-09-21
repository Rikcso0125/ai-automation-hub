"""
Automatizált Mock Teszt Modul 10:
Kereskedelmi Anomália Detektálás (Árrészuhanás Figyelő & Circuit Breaker)
"""

import os
import sys
import json

curr_dir = os.path.dirname(os.path.abspath(__file__))
if curr_dir not in sys.path:
    sys.path.insert(0, curr_dir)

from handler import CommercialAnomalyCircuitBreakerHandler, run

def run_all_tests():
    print("=" * 65)
    print("[TESZT KEZDES] Modul 10: Kereskedelmi Anomalia Circuit Breaker Teszt")
    print("=" * 65)

    # 1. Payload betöltése
    payload_path = os.path.join(curr_dir, "test_payload.json")
    with open(payload_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    orders_count = len(payload.get("orders", []))
    print(f"[1. TESZT] test_payload.json betoltve ({orders_count} rendelest tartalmaz)")

    # 2. Alapértelmezett audit futtatása (loss_threshold_adaptive, 50k küszöb, 8% min margin)
    handler = CommercialAnomalyCircuitBreakerHandler({
        "service_mode": "mock",
        "minimum_margin_percent": 8.0,
        "max_cumulative_discount_percent": 35.0,
        "circuit_breaker_policy": "loss_threshold_adaptive",
        "hard_block_loss_threshold_huf": 50000.0
    })
    res = handler.execute(payload)

    assert res.get("status") == "success", "Hiba: A folyamat nem success-szel vegzodott!"
    assert res.get("orders_audited_count") == 4, "4 rendelest vartunk!"
    assert res.get("blocked_orders_count") == 2, f"2 zarolt rendelest vartunk, kapott: {res.get('blocked_orders_count')}"

    audited = res.get("audited_orders", [])
    ord1 = next((o for o in audited if o["order_id"] == "ORD-ANOMALY-01"), None)
    ord2 = next((o for o in audited if o["order_id"] == "ORD-ANOMALY-02"), None)
    ord3 = next((o for o in audited if o["order_id"] == "ORD-ANOMALY-03"), None)
    ord4 = next((o for o in audited if o["order_id"] == "ORD-ANOMALY-04"), None)

    print("--- TRANZAKCIOK AUDIT EREDMENYEI ---")
    for o in audited:
        oid = o["order_id"]
        cust = o["customer_name"]
        status = o["circuit_breaker"]["circuit_breaker_status"]
        blocked = "BLOKKOLVA" if o["circuit_breaker"]["dispatch_blocked"] else "ENGEDELYEZVE"
        loss = o["circuit_breaker"]["total_calculated_loss_huf"]
        print(f"[{oid}] {cust} | {status} | Szallitas: {blocked} | Veszteseg: {loss:,.0f} Ft")

    # 3. Rendelés 1 vizsgálata (Daikin klíma ráfizetés: 300,000 Ft veszteség -> Kemény Zárlat)
    assert ord1 is not None, "ORD-ANOMALY-01 hianyzik!"
    assert ord1["circuit_breaker"]["dispatch_blocked"] is True, "ORD-ANOMALY-01 szallitast blokkolni kell!"
    assert ord1["circuit_breaker"]["total_calculated_loss_huf"] >= 300000
    assert ord1["manager_override"] is not None, "Vezetoi feloldo csomag hianyzik!"
    assert "telegram_alert" in ord1["manager_override"]["alert_broadcast"], "Telegram riasztas hianyzik!"
    print("[OK] Rendelés 1 (Daikin klíma ráfizetés): 300,000 Ft veszteség azonnal kemény zárlat alá került")

    # 4. Rendelés 2 vizsgálata (Golyóscsap kedvezményhalmozás -42% -> Kemény Zárlat)
    assert ord2 is not None, "ORD-ANOMALY-02 hianyzik!"
    assert ord2["circuit_breaker"]["dispatch_blocked"] is True, "ORD-ANOMALY-02 szallitast blokkolni kell!"
    anom_codes = [a["code"] for a in ord2["circuit_breaker"]["anomalies_summary"]]
    assert "EXCESSIVE_DISCOUNT_STACKING" in anom_codes, "Kedvezmenyhalmozas anomalia hianyzik!"
    assert "CRITICAL_NEGATIVE_MARGIN" in anom_codes, "Negativ arres anomalia hianyzik!"
    print("[OK] Rendelés 2 (Kedvezményhalmozás -42%): Sikeresen detektálva és zárolva")

    # 5. Rendelés 3 vizsgálata (Alacsony árrés 5.1%, de kis veszteség 4,500 Ft < 50,000 Ft -> Figyelmeztető Zászló)
    assert ord3 is not None, "ORD-ANOMALY-03 hianyzik!"
    assert ord3["circuit_breaker"]["dispatch_blocked"] is False, "ORD-ANOMALY-03 nem lehet kemenyen blokkolva (50k limit alatt)!"
    assert ord3["circuit_breaker"]["circuit_breaker_status"] == "WARNING_PROCEED_WITH_FLAG"
    print("[OK] Rendelés 3 (Alacsony haszon, kis tétel): Intelligensen átengedve audit figyelmeztetéssel")

    # 6. Rendelés 4 vizsgálata (Teljesen szabályos 21.1% árrés -> Tiszta jóváhagyás)
    assert ord4 is not None, "ORD-ANOMALY-04 hianyzik!"
    assert ord4["circuit_breaker"]["dispatch_blocked"] is False
    assert ord4["circuit_breaker"]["circuit_breaker_status"] == "CLEAR_PROCEED"
    print("[OK] Rendelés 4 (Szabályos Grundfos tétel): Tiszta jóváhagyás, 0 akadály")

    # 7. Vezetői feloldási mechanizmus tesztelése (OVERRIDE_TRANSACTION)
    print("[2. TESZT] Vezetői feloldási token és PIN tesztelése...")
    override_payload = {
        "action": "OVERRIDE_TRANSACTION",
        "order_id": "ORD-ANOMALY-01",
        "token": "AUTH-APPROVE-ORD-ANOMALY-01-2026",
        "pin_code": "8842"
    }
    override_res = handler.execute(override_payload)
    assert override_res.get("override_status") == "APPROVED_BY_EXECUTIVE"
    assert override_res.get("dispatch_unblocked") is True
    print("[OK] Vezetoi tokenes feloldas tokeletesen mukodik")

    # 8. Tartós Napló (data/arresvedelem_naplo.json) ellenőrzése
    print("[3. TESZT] Tartós Árrésvédelmi Napló ellenőrzése...")
    db_path = "data/arresvedelem_naplo.json"
    assert os.path.exists(db_path), f"Hiba: {db_path} nem jott letre!"
    with open(db_path, "r", encoding="utf-8") as f:
        db_data = json.load(f)
    assert "protection_summary" in db_data, "Hianyzo protection_summary!"
    saved_loss = db_data["protection_summary"]["total_margin_loss_prevented_huf"]
    assert saved_loss >= 300000, f"Megmentett arresveszteseg keves: {saved_loss}"
    print(f"[OK] Adatbazis rendben ({db_path}) | Megmentett arresveszteseg: {saved_loss:,.0f} Ft")

    # 9. Szabványos run() függvény tesztelése
    print("[4. TESZT] Szabványos run() belépési pont tesztelése...")
    hub_res = run(payload)
    assert hub_res.get("status") == "success", "Hub run() hibat adott!"
    print("[OK] Hub run() fuggveny tokeletesen lefutott")

    print("=" * 65)
    print("[MINDEN TESZT SIKERESEN LEFUTOTT]")
    print("=" * 65)

if __name__ == "__main__":
    run_all_tests()