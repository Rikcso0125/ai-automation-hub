# -*- coding: utf-8 -*-
"""
Mock test for Module 4.06: Tömeges Termékleírás és SEO Optimalizáló Motor
Tests:
1. Kettős hibrid leírás és teljes SEO suite (SERP + Schema.org JSON-LD).
2. Szakmai B2B mérnöki leírás és CSV/Excel export.
3. Interaktív diff előnézeti kapu 1-kattintásos jóváhagyó linkkel.
"""
import sys
import os
import json

# Import local handler directly
sys.path.insert(0, os.path.dirname(__file__))
from handler import run

def test_seo_copilot():
    print("==================================================")
    print("TESZT: Module 4.06 - Tomeges Termekleiras es SEO Copilot")
    print("==================================================")

    # 1. Teszt: Kettős hibrid leírás és teljes SEO csomag
    payload_hybrid = {
        "raw_product": {
            "sku": "BOSCH-GSR-18V-55",
            "supplier_title": "BOSCH GSR 18V-55 AKKUS FUROCSAVAROZO SOLO 06019H5202",
            "supplier_raw_text": "Szenkefementes EC motor. 55 Nm nyomatek. 13 mm fem tokmany.",
            "category": "Akkus fúró-csavarozók",
            "brand": "Bosch Professional",
            "price_gross_huf": 49990,
            "key_specs": {
                "Feszültség": "18 V",
                "Nyomaték": "55 Nm",
                "Tokmány": "13 mm fém"
            }
        },
        "config": {
            "style_tone_mode": "hybrid_dual",
            "seo_package_mode": "full_seo_suite",
            "sync_approval_mode": "diff_review_gate"
        }
    }

    print("\n1. Teszt: Kettős hibrid leírás és Teljes SEO csomag (SERP + Schema.org)")
    res1 = run(payload_hybrid)
    assert res1.get("status") == "success", "Test 1 failed!"
    data1 = res1.get("product_seo_data", {})
    seo1 = data1.get("seo", {})
    sync1 = data1.get("sync_result", {})
    print(f"Generált cím: {data1.get('title')}")
    print(f"Meta Title ({len(seo1.get('meta_title'))} kar): {seo1.get('meta_title')}")
    print(f"Meta Description ({len(seo1.get('meta_description'))} kar): {seo1.get('meta_description')}")
    print(f"URL Slug: {seo1.get('url_slug')}")
    print(f"Schema Product Context: {seo1.get('schema_product_jsonld', {}).get('@context')}")
    print(f"Schema FAQ kérdések: {len(seo1.get('schema_faq_jsonld', {}).get('mainEntity', []))} db")
    print(f"Jóváhagyási kapu URL: {sync1.get('approval_action_url')}")
    assert len(seo1.get("meta_title")) <= 60, "Meta title exceeds 60 chars!"
    assert len(seo1.get("meta_description")) <= 160, "Meta description exceeds 160 chars!"
    assert seo1.get("schema_product_jsonld") is not None, "Product schema missing!"
    print("[OK] Kettős hibrid leírás és teljes SEO csomag sikeresen elkészült!")

    # 2. Teszt: B2B Mérnöki Mód és CSV/Excel Export
    payload_b2b = {
        "raw_product": {
            "sku": "MAKITA-DHP-484",
            "supplier_title": "MAKITA DHP484Z AKKUS UTVEFURO 18V SOLO",
            "supplier_raw_text": "Utvefuro funkcio. Ketsebesseges. BL motor.",
            "category": "Ipari gépek",
            "brand": "Makita",
            "price_gross_huf": 64990,
            "key_specs": {"Ütvefúrás": "Igen", "Motor": "BL Brushless"}
        },
        "config": {
            "style_tone_mode": "b2b_technical",
            "sync_approval_mode": "csv_excel_export"
        }
    }

    print("\n2. Teszt: B2B Műszaki Leírás és CSV/Excel Export")
    res2 = run(payload_b2b)
    data2 = res2.get("product_seo_data", {})
    sync2 = data2.get("sync_result", {})
    print(f"Generált B2B Cím: {data2.get('title')}")
    print(f"Export Státusz: {sync2.get('status')} ({sync2.get('export_filename')})")
    print(f"Minta CSV sor: {sync2.get('sample_row', {}).get('Variant SKU')} -> {sync2.get('sample_row', {}).get('SEO Title')}")
    assert sync2.get("status") == "EXPORT_READY", "Export not ready!"
    print("[OK] B2B műszaki leírás és CSV importfájl sikeresen legenerálva!")

    # 3. Teszt: Közvetlen API szinkron Shopify mód
    payload_api = {
        "raw_product": {
            "sku": "DEWALT-DCD-796",
            "supplier_title": "DEWALT DCD796P2 AKKUS UTVEFURO-CSAVAROZO",
            "supplier_raw_text": "18V XR Li-Ion akkus utvefuro-csavarozo 2x5.0Ah.",
            "brand": "DeWalt",
            "price_gross_huf": 89990
        },
        "config": {
            "sync_approval_mode": "direct_api_bulk_sync",
            "target_ecommerce_platform": "shopify"
        }
    }

    print("\n3. Teszt: Közvetlen webáruház API publikálás (Shopify Zero-Touch)")
    res3 = run(payload_api)
    data3 = res3.get("product_seo_data", {})
    sync3 = data3.get("sync_result", {})
    print(f"Publikálási mód: {sync3.get('mode')} -> Státusz: {sync3.get('status')}")
    print(f"API Végpont: {sync3.get('api_endpoint')}")
    assert sync3.get("status") == "PUBLISHED_VIA_API", "API publishing failed!"
    print("[OK] Közvetlen API szinkronizáció sikeres!")

    print("\n==================================================")
    print("MINDEN TERMÉKLEÍRÁS ÉS SEO TESZT SIKERESEN LEFUTOTT! (3/3)")
    print("==================================================")

if __name__ == "__main__":
    test_seo_copilot()
