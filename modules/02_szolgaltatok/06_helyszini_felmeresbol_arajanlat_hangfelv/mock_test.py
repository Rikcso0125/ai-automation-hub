"""
Mock teszt a 06_helyszini_felmeresbol_arajanlat_hangfelv modulhoz.
Teszteli a katalógus párosítást, a ráhagyás számítást, a PDF generálást mind A (Review) mind B (Auto-dispatch) módban.
"""

import os
import sys
import json

curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, curr_dir)
from handler import run

def test_voice_to_quote():
    print("=== 1. TESZT: HANGFELJEGYZÉS FELDOLGOZÁSA (A MÓD: SZAKEMBER JÓVÁHAGYÁS KÉRÉS) ===")
    payload_a = {
        "technician": {
            "id": "TECH-001",
            "name": "Kovács László (Főszerelő)",
            "phone": "+36 30 111 2233",
            "channel": "whatsapp"
        },
        "customer": {
            "name": "Kiss Péter",
            "company": "Kiss & Társa Kft.",
            "phone": "+36 30 987 6543",
            "email": "peter.kiss@example.hu",
            "site_address": "1024 Budapest, Margit körút 12. 3. em. 4."
        },
        "voice_transcript": "Szia! Kiss Péternél jártam a Margit körút 12-ben, harmadik emelet. Egy 3.5 kW-os Gree Comfort X inverteres klíma kell a nappaliba, a kültérit rozsdamentes 450-es konzolra rakjuk. 6 méter rézcső kell hozzá, amiből 3 méter extra nyomvonal kábelcsatornában. A régi split klímát le kell szerelni és elvinni. A betonfalat át kell fúrni gyémánttal, és kell egy Schneider B16-os kismegszakító is a kiselosztóba.",
        "attached_photos": [
            {"url": "https://example.hu/beltéri.jpg", "description": "Nappali falikép"}
        ],
        "requested_mode": "review_required"
    }
    res_a = run(payload_a)
    print(f"Status: {res_a.get('status')}")
    print(f"Ajánlatszám: {res_a.get('quote_id')}")
    print(f"Mód: {res_a.get('dispatch_mode')}")
    print(f"Státusz összegzés: {res_a.get('status_summary')}")
    print(f"Anyagok száma: {res_a.get('materials_count')} tétel | Munkadíjak: {res_a.get('labor_count')} tétel")
    calc_a = res_a.get("calculations", {})
    print(f"Nettó anyag: {calc_a.get('material_net'):,} Ft | Nettó munka: {calc_a.get('labor_net'):,} Ft".replace(",", " "))
    print(f"Biztonsági ráhagyás (+10%): {calc_a.get('waste_margin_net'):,} Ft | Bruttó végösszeg: {calc_a.get('gross_total'):,} Ft".replace(",", " "))
    print(f"Generált PDF: {res_a.get('pdf_generated_path')}")
    print(f"Jóváhagyási link a szakembernek: {res_a.get('one_click_action_link')}")
    assert os.path.exists(res_a.get('pdf_generated_path')), "PDF fájlnak léteznie kell!"

    print("\n=== 2. TESZT: KÖZVETLEN ÜGYFÉL KIKÜLDÉS (B MÓD: AUTO-DISPATCH & ELFOGADÓ LINK) ===")
    payload_b = {
        "technician": {"name": "Szabó Zoltán", "channel": "telegram"},
        "customer": {"name": "Nagy Andrea", "phone": "+36 20 444 5566", "site_address": "1118 Budapest, Rétköz u. 12."},
        "voice_transcript": "Egy 3.5 kW-os Gree Comfort X klíma standard alapszereléssel és rozsdamentes konzollal.",
        "requested_mode": "auto_dispatch"
    }
    res_b = run(payload_b)
    print(f"Status: {res_b.get('status')}")
    print(f"Ajánlatszám: {res_b.get('quote_id')}")
    print(f"Mód: {res_b.get('dispatch_mode')}")
    print(f"Státusz összegzés: {res_b.get('status_summary')}")
    calc_b = res_b.get("calculations", {})
    print(f"Bruttó végösszeg: {calc_b.get('gross_total'):,} Ft".replace(",", " "))
    print(f"Ügyfél 1-kattintásos megrendelő link: {res_b.get('one_click_action_link')}")
    print(f"Kiküldési csatorna: {res_b.get('delivery_details', {}).get('client_channel')}")
    assert os.path.exists(res_b.get('pdf_generated_path')), "PDF fájlnak léteznie kell!"
    print("\n[SIKERES TESZT] Minden teszteset sikeresen lefutott!")

if __name__ == "__main__":
    test_voice_to_quote()
