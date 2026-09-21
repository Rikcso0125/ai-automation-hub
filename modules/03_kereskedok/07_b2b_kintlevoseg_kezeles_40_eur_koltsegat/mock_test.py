"""
Automatizált Mock Teszt Modul 07:
B2B Kintlévőség-kezelés 40 EUR Költségátalánnyal
"""

import os
import sys
import json

curr_dir = os.path.dirname(os.path.abspath(__file__))
if curr_dir not in sys.path:
    sys.path.insert(0, curr_dir)

from handler import B2BDebtCollectionHandler, run

def run_all_tests():
    print("=" * 65)
    print("[TESZT KEZDES] Modul 07: B2B Kintlevoseg-kezeles Tesztcsomag")
    print("=" * 65)

    # 1. Payload betöltése
    payload_path = os.path.join(curr_dir, "test_payload.json")
    with open(payload_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    inv_count = len(payload.get("invoices", []))
    print(f"[1. TESZT] test_payload.json betoltve ({inv_count} szamla)")

    # 2. Alapértelmezett futtatás (Grace period 15 nap, VIP waiver engedélyezve, Both combined eszkaláció)
    handler = B2BDebtCollectionHandler({
        "service_mode": "mock",
        "credit_hold_policy": "grace_period_days",
        "credit_hold_grace_days": 15,
        "fee_calculation_mode": "configurable_per_partner",
        "allow_vip_fee_waiver": True,
        "escalation_mode": "both_combined"
    })
    res = handler.execute(payload)

    assert res.get("status") == "success", "Hiba: A folyamat nem success-szel tert vissza!"
    assert res.get("invoices_processed_count") == 3, "Hiba: 3 szamlat vartunk!"

    invs = res.get("processed_invoices", [])
    inv_gold = next((i for i in invs if i["invoice_number"] == "SZAMLA-2026-0891"), None)
    inv_silver = next((i for i in invs if i["invoice_number"] == "SZAMLA-2026-0945"), None)
    inv_bronze = next((i for i in invs if i["invoice_number"] == "SZAMLA-2026-0712"), None)

    print("--- FELDOLGOZOTT SZAMLAK ES KINTLEVOSEGEK ---")
    for iv in invs:
        num = iv["invoice_number"]
        pname = iv["partner_name"]
        days = iv["delay_analysis"]["days_overdue"]
        lvl = iv["delay_analysis"]["level"]
        tot = iv["penalties"]["total_payable_huf"]
        hold = iv["credit_hold"]["is_hold_active"]
        fmh = "IGEN" if iv.get("fmh_dossier") else "NEM"
        print(f"[{num}] {pname} | {days} nap | {lvl} | Tartozas: {tot:,.0f} Ft | Zarlat: {hold} | FMH: {fmh}")

    # 3. Gold Partner (26 napos késedelem - Level 3): Raktári Zárolás + VIP Waiver
    assert inv_gold is not None, "Gold szamla hianyzik!"
    assert inv_gold["delay_analysis"]["days_overdue"] == 26, "26 napos keses vart!"
    assert inv_gold["delay_analysis"]["level"] == "LEVEL_3_STRICT_HOLD_AND_FEE", "Level 3 besorolas hianyzik!"
    assert inv_gold["credit_hold"]["is_hold_active"] is True, "26 nap utan a raktari zarlatnak aktivnak kell lennie!"
    assert inv_gold["credit_hold"]["pending_orders"][0]["dispatch_status"] == "LOCKED_CREDIT_HOLD", "Fuggo rendeles nincs zarolva!"
    assert inv_gold["penalties"]["fee_waived"] is True, "Gold partnernel a 40 EUR dijat el kellett engedni!"
    assert inv_gold["penalties"]["billed_recovery_fee_huf"] == 0, "Elengedett dij eseten 0 Ft kell legyen a szamlazott dij!"
    assert inv_gold["penalties"]["accumulated_interest_huf"] > 0, "Kamatot fel kellett szamitani!"
    assert inv_gold["kam_alert"] is not None, "KAM riasztas hianyzik!"
    print("[OK] Gold partner (KlímaMaster): Raktári szállítási stop aktív, 40 EUR VIP méltányosságból elengedve, kamat számolva")

    # 4. Silver Partner (10 napos késedelem - Level 2): Türelmi idő, nincs még zárolás
    assert inv_silver is not None, "Silver szamla hianyzik!"
    assert inv_silver["delay_analysis"]["days_overdue"] == 10, "10 napos keses vart!"
    assert inv_silver["delay_analysis"]["level"] == "LEVEL_2_FORMAL_NOTICE", "Level 2 besorolas vart!"
    assert inv_silver["credit_hold"]["is_hold_active"] is False, "15 napos turelmi idon belul meg nem aktiv a zarlat!"
    assert inv_silver["credit_hold"]["pending_orders"][0]["dispatch_status"] == "APPROVED_FOR_DISPATCH", "Kiadhato kell legyen!"
    print("[OK] Silver partner (TermoGépész): 10 napos csúszás, hivatalos figyelmeztetés kiadva, raktári kiadás még engedélyezve")

    # 5. Bronze Partner (41 napos súlyos késedelem - Level 4): 40 EUR terhelve + MOKK FMH Dosszié
    assert inv_bronze is not None, "Bronze szamla hianyzik!"
    assert inv_bronze["delay_analysis"]["days_overdue"] == 41, "41 napos keses vart!"
    assert inv_bronze["delay_analysis"]["level"] == "LEVEL_4_LEGAL_FMH_ESCALATION", "Level 4 vart!"
    assert inv_bronze["credit_hold"]["is_hold_active"] is True, "Raktari zarlat aktiv!"
    assert inv_bronze["penalties"]["fee_waived"] is False, "Bronze partnernel nincs fee waiver!"
    assert inv_bronze["penalties"]["billed_recovery_fee_huf"] == 16220, f"40 EUR dij (16,220 Ft) vart, kapott: {inv_bronze['penalties']['billed_recovery_fee_huf']}"
    assert inv_bronze["fmh_dossier"] is not None, "FMH dosszie hianyzik!"
    fmh = inv_bronze["fmh_dossier"]
    assert "claim_breakdown" in fmh, "Hianyzo claim_breakdown az FMH-ban!"
    assert "2016. évi IX. törvény" in fmh["claim_breakdown"]["legal_basis_recovery_fee"], "40 EUR torvenyi hivatkozas hianyzik!"
    print("[OK] Bronze partner (Hűtés-Fűtés Kisker): 41 napos késés, 40 EUR kiszámlázva, MOKK FMH jogi csomag összeállítva")

    # 6. Credit Hold Policy: immediate_freeze tesztelése
    print("[2. TESZT] Credit Hold: immediate_freeze szabalyzat tesztelese...")
    handler_freeze = B2BDebtCollectionHandler({"credit_hold_policy": "immediate_freeze"})
    res_freeze = handler_freeze.process_single_invoice(payload["invoices"][1])  # 10 napos késés
    assert res_freeze["credit_hold"]["is_hold_active"] is True, "Immediate freeze eseten 10 napos kesesnel mar aktivnak kell lennie!"
    assert res_freeze["credit_hold"]["hold_type"] == "IMMEDIATE_DISPATCH_FREEZE"
    print("[OK] immediate_freeze szabalyzat sikeresen blokkolta a szallitast mar a korai fazisban")

    # 7. Fee Calculation Mode: auto_invoice_immediate tesztelése
    print("[3. TESZT] 40 EUR Stratégia: auto_invoice_immediate tesztelése...")
    handler_fee = B2BDebtCollectionHandler({
        "fee_calculation_mode": "auto_invoice_immediate",
        "allow_vip_fee_waiver": False
    })
    res_fee = handler_fee.process_single_invoice(payload["invoices"][1])  # 10 napos
    assert res_fee["penalties"]["billed_recovery_fee_huf"] == 16220, "Azonnali szamlazas modban 10 nap utan is ki kell terhelni a 40 EUR-t!"
    print("[OK] auto_invoice_immediate modban a 40 EUR dij azonnal felszamitasra kerult")

    # 8. Tartós Napló (data/b2b_kintlevosegek_naplo.json) ellenőrzése
    print("[4. TESZT] Tartós Adatbázis mentés ellenőrzése...")
    db_path = "data/b2b_kintlevosegek_naplo.json"
    assert os.path.exists(db_path), f"Hiba: {db_path} nem jott letre!"
    with open(db_path, "r", encoding="utf-8") as f:
        db_data = json.load(f)
    assert "collection_metrics" in db_data, "Hianyzo collection_metrics!"
    assert db_data["collection_metrics"]["accounts_under_credit_hold"] >= 2, "Zarolt partnerek szama tul keves!"
    tot_claim = db_data["collection_metrics"]["total_payable_claims_huf"]
    print(f"[OK] Adatbazis rendben ({db_path}), koveteles osszesen: {tot_claim:,.0f} Ft, FMH dossziek: {db_data['collection_metrics']['fmh_legal_dossiers_prepared']}")

    # 9. Szabványos run() függvény ellenőrzése
    print("[5. TESZT] Szabványos run() belépési pont tesztelése...")
    hub_res = run(payload)
    assert hub_res.get("status") == "success", "Hub run() hibat adott!"
    print("[OK] Hub run() fuggveny tokeletesen lefutott")

    print("=" * 65)
    print("[MINDEN TESZT SIKERESEN LEFUTOTT]")
    print("=" * 65)

if __name__ == "__main__":
    run_all_tests()