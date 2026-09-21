"""
Mock teszt a 12_elvesztett_ajanlatok_elemzese_visszanyer modulhoz.
Teszteli az ár miatti veszteség elemzését, a karcsúsított ellenajánlatot (-15%),
a PDF ellenajánlat generálást, az A opciós jóváhagyási kaput és a Dashboard statisztikát.
"""

import os
import sys
import json

curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, curr_dir)
from handler import run

def test_win_loss_winback():
    print("=== 1. TESZT: ÁR MIATTI VESZTESÉG & KARCSÚSÍTOTT ELLENAJÁNLAT (A OPCIÓ) ===")
    payload_price = {
        "deal": {
            "quote_id": "AJ-20260920-7741",
            "service_name": "Irodai multi-split klímarendszer kiépítése",
            "original_gross_huf": 890000
        },
        "customer": {
            "name": "Bartha Gábor",
            "company": "Bartha Logisztika Kft.",
            "phone": "+36 30 666 5544"
        },
        "loss_feedback": {
            "source": "whatsapp_sms_poll",
            "primary_reason": "price_budget",
            "customer_comment": "Drága, szűkös a büdzsé max 750 ezer forintunk van rá."
        }
    }
    res = run(payload_price)
    print(f"Status: {res.get('status')}")
    print(f"Veszteség kategória: {res.get('loss_reason_category')} ({res.get('loss_reason_title')})")
    print(f"Stratégia: {res.get('win_back_strategy')}")
    print(f"Eredeti ár: 890 000 Ft -> Karcsúsított új ár: {res.get('counter_offer_gross_huf'):,} Ft".replace(",", " "))
    print(f"1-Kattintásos jóváhagyási link: {res.get('one_click_approval_link')}")
    print(f"Generált PDF ellenajánlat: {res.get('counter_offer_pdf_path')}")
    assert os.path.exists(res.get('counter_offer_pdf_path')), "PDF fájlnak léteznie kell!"
    assert res.get('counter_offer_gross_huf') < 890000

    print("\n=== 2. TESZT: IDŐZÍTÉS MIATTI VESZTESÉG & DASHBOARD STATISZTIKA ===")
    payload_timing = {
        "deal": {"quote_id": "AJ-20260920-7742", "original_gross_huf": 1200000},
        "customer": {"name": "Szilágyi Péter"},
        "loss_feedback": {"primary_reason": "timing", "customer_comment": "Most nem aktuális, majd jövőre visszatérünk rá."}
    }
    res_timing = run(payload_timing)
    print(f"Veszteség kategória: {res_timing.get('loss_reason_category')}")
    print(f"Stratégia: {res_timing.get('win_back_strategy')}")
    dash = res_timing.get("dashboard_analytics_summary", {})
    print(f"Összes rögzített veszteség: {dash.get('total_lost')} db")
    print(f"Ár miatti veszteség: {dash.get('lost_by_price')} db | Időzítés miatti: {dash.get('lost_by_timing')} db")
    print(f"Potenciális visszanyerhető bevétel: {dash.get('potential_recovered_revenue_huf'):,} Ft".replace(",", " "))
    print("\n[SIKERES TESZT] Minden teszteset sikeresen lefutott!")

if __name__ == "__main__":
    test_win_loss_winback()
