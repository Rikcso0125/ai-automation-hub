"""
Mock teszt a 09_targyalas_utani_ugyfel_osszefoglalo_foll modulhoz.
Teszteli a tárgyalási hangjegyzet feldolgozását, az emlékeztető emailt,
a 24 órás vita-megelőző záradékot, a PDF jegyzőkönyvet és az A opciós mobil jóváhagyást.
"""

import os
import sys
import json

curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, curr_dir)
from handler import run

def test_follow_up_copilot():
    print("=== 1. TESZT: TÁRGYALÁS UTÁNI EMLÉKEZTETŐ ÉS JEGYZŐKÖNYV GENERÁLÁSA ===")
    payload = {
        "meeting_metadata": {
            "date": "2026-09-20",
            "time": "14:00 - 14:45",
            "location": "Ügyfél irodája (1134 Budapest, Váci út 45.)",
            "subject": "Irodaház szerverterem és irodai hűtés-fűtés korszerűsítés felmérése"
        },
        "participants": {
            "sales_rep": {
                "name": "Kovács László",
                "company": "ProfiKlíma Kft.",
                "phone": "+36 30 111 2233",
                "email": "kovacs.laszlo@profiklima.hu"
            },
            "client": {
                "name": "Varga Mihály",
                "company": "Varga Tech Kft.",
                "phone": "+36 30 777 8899",
                "email": "varga.mihaly@vargatech.hu"
            }
        },
        "input_source": "whatsapp_voice",
        "input_content": "Varga Mihállyal tárgyaltunk. A szerverterembe redundáns 5 kW Daikin klíma kell, az irodába két kazettás egység. Hétvégi kivitelezés. Varga úr hétfő délig küldi az alaprajzot, én szerda 17:00-ig az árajánlatot.",
        "approval_mode": "review_required"
    }
    res = run(payload)
    print(f"Status: {res.get('status')}")
    print(f"Jegyzőkönyv azonosító: {res.get('memo_id')}")
    print(f"Jóváhagyási státusz: {res.get('review_status')}")
    print(f"1-Kattintásos jóváhagyási link: {res.get('one_click_approval_link')}")
    print(f"Megállapodott pontok száma: {res.get('agreed_points_count')}")
    print(f"Ügyféli teendők: {res.get('client_tasks_count')} | Szolgáltatói teendők: {res.get('provider_tasks_count')}")
    print(f"Generált PDF jegyzőkönyv: {res.get('pdf_memo_path')}")
    print(f"Vita-megelőző záradék csatolva: {res.get('dispute_clause_included')}")
    assert os.path.exists(res.get('pdf_memo_path')), "PDF jegyzőkönyv fájlnak léteznie kell!"
    assert res.get('review_status') == "PENDING_SALES_REP_APPROVAL"
    print("\nRiasztás az értékesítőnek mobilra:\n" + res.get('sales_rep_notification', {}).get('message', ''))
    print("\n[SIKERES TESZT] Minden teszteset sikeresen lefutott!")

if __name__ == "__main__":
    test_follow_up_copilot()
