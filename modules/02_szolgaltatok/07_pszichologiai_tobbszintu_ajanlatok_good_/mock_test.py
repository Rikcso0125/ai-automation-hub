"""
Mock teszt a 07_pszichologiai_tobbszintu_ajanlatok_good_ modulhoz.
Teszteli a 3 szintű csomagképzést, a fekvő tájolású összehasonlító PDF-et,
az interaktív HTML választót és az A/B utókövetési / upsell logikát.
"""

import os
import sys
import json

curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, curr_dir)
from handler import run

def test_good_better_best():
    print("=== 1. TESZT: GOOD-BETTER-BEST CSOMAGOK ÉS DOKUMENTUMOK GENERÁLÁSA ===")
    payload = {
        "customer": {
            "name": "Varga Mihály",
            "company": "Varga Tech Kft.",
            "phone": "+36 30 777 8899",
            "email": "varga.mihaly@vargatech.hu",
            "site_address": "1134 Budapest, Váci út 45."
        },
        "project_scope": {
            "category": "Klíma és Hűtés-Fűtés Kialakítás",
            "room_area_m2": 35,
            "base_requirement": "Nappali hűtése és átmeneti fűtése, 3.5 kW-os teljesítményigény",
            "base_material_net": 210000,
            "base_labor_net": 75000
        }
    }
    res = run(payload)
    print(f"Status: {res.get('status')}")
    print(f"Ajánlatszám: {res.get('quote_id')}")
    pkgs = res.get("packages", {})
    print(f"Good (Alap) Bruttó: {pkgs.get('good', {}).get('gross_total'):,} Ft".replace(",", " "))
    print(f"Better (Ajánlott Prémium) Bruttó: {pkgs.get('better', {}).get('gross_total'):,} Ft (Kiemelt: {pkgs.get('better', {}).get('highlighted')})".replace(",", " "))
    print(f"Best (VIP All-Inclusive) Bruttó: {pkgs.get('best', {}).get('gross_total'):,} Ft".replace(",", " "))
    print(f"Interaktív Webes Portál: {res.get('interactive_portal_path')}")
    print(f"3-Hasábos Összehasonlító PDF: {res.get('comparison_pdf_path')}")
    print(f"48 órás utánkövetés beütemezve: {res.get('followup_48h_scheduled')}")
    assert os.path.exists(res.get('comparison_pdf_path')), "PDF fájlnak léteznie kell!"
    assert os.path.exists(res.get('interactive_portal_path')), "HTML fájlnak léteznie kell!"

    print("\n=== 2. TESZT: GOOD CSOMAG KIVÁLASZTÁSA UPSELL HOZZÁADÁSÁVAL (B OPCIÓ) ===")
    payload_upsell = {
        "customer": {"name": "Varga Mihály", "site_address": "1134 Budapest, Váci út 45."},
        "project_scope": {"base_material_net": 210000, "base_labor_net": 75000},
        "selected_package": "good_with_upsell"
    }
    res_upsell = run(payload_upsell)
    sel = res_upsell.get("selected_package_result", {})
    print(f"Kiválasztott csomag: {sel.get('package')}")
    print(f"Upsell kiegészítő: {sel.get('upsell_addon')}")
    print(f"Végösszeg upsell-lel: {sel.get('gross_total'):,} Ft".replace(",", " "))
    print("\n[SIKERES TESZT] Minden teszteset sikeresen lefutott!")

if __name__ == "__main__":
    test_good_better_best()
