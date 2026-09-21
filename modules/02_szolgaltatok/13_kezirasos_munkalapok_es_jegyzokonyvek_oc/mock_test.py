"""
Mock teszt a 13_kezirasos_munkalapok_es_jegyzokonyvek_oc modulhoz.
Teszteli az alakhű OCR felismerést, az aláírások ellenőrzését, a PDF generálást,
a számlatervezet készítést és a hiányzó aláírás miatti Human Review figyelmeztetést.
"""

import os
import sys
import json

curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, curr_dir)
from handler import run

def test_worksheet_ocr():
    print("=== 1. TESZT: SIKERES KÉZÍRÁSOS MUNKALAP ALÁÍRÁSSAL & SZÁMLATERVEZETTEL ===")
    payload_valid = {
        "technician": {"name": "Horváth László", "phone": "+36 30 333 4455"},
        "simulate_ocr_input": {
            "has_technician_signature": True,
            "has_customer_signature": True,
            "confidence_score": 94.0
        }
    }
    res_valid = run(payload_valid)
    print(f"Status: {res_valid.get('status')}")
    print(f"Munkalapszám: {res_valid.get('worksheet_number')}")
    print(f"Ügyfél: {res_valid.get('customer_name')}")
    print(f"OCR Bizonyosság: {res_valid.get('ocr_confidence')}%")
    print(f"Aláírások: Szakember: {res_valid.get('signatures_detected', {}).get('technician')} | Ügyfél: {res_valid.get('signatures_detected', {}).get('customer')}")
    print(f"Human Review szükséges: {res_valid.get('human_review_required')}")
    print(f"Bruttó összeg: {res_valid.get('gross_total_huf'):,} Ft".replace(",", " "))
    print(f"Generált PDF munkalap: {res_valid.get('pdf_worksheet_path')}")
    assert os.path.exists(res_valid.get('pdf_worksheet_path')), "PDF munkalap fájlnak léteznie kell!"
    assert res_valid.get('human_review_required') is False
    assert res_valid.get('invoice_draft') is not None
    print(f"Számlatervezet státusz: {res_valid.get('invoice_draft', {}).get('status')}")

    print("\n=== 2. TESZT: HIÁNYZÓ ÜGYFÉL ALÁÍRÁS MIATTI HUMAN REVIEW FIGYELMEZTETÉS ===")
    payload_unsigned = {
        "technician": {"name": "Horváth László"},
        "simulate_ocr_input": {
            "has_technician_signature": True,
            "has_customer_signature": False,
            "confidence_score": 75.0
        }
    }
    res_unsigned = run(payload_unsigned)
    print(f"Human Review szükséges: {res_unsigned.get('human_review_required')}")
    print(f"Figyelmeztető okok: {res_unsigned.get('review_reasons')}")
    assert res_unsigned.get('human_review_required') is True
    assert len(res_unsigned.get('review_reasons')) >= 2
    print("\n[SIKERES TESZT] Minden teszteset sikeresen lefutott!")

if __name__ == "__main__":
    test_worksheet_ocr()
