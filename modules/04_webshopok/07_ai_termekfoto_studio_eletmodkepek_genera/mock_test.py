# -*- coding: utf-8 -*-
"""
Mock test for Module 4.07: AI Termékfotó Stúdió & Életmódképek Generálása
Tests:
1. Multi-marketing formátum csomag (1:1, 4:5, 9:16, 16:9) és asztalosműhely stúdiódíszlet.
2. Hibrid prompt finomhangolás és Trust Badge ráillesztés.
3. Négyzetes webshop galéria és interaktív előnézeti galéria linkkel.
"""
import sys
import os
import json

# Import local handler directly
sys.path.insert(0, os.path.dirname(__file__))
from handler import run

def test_ai_photo_studio():
    print("==================================================")
    print("TESZT: Module 4.07 - AI Termekfoto Studio es Eletmodkepek")
    print("==================================================")

    # 1. Teszt: Multi-marketing formátum csomag és asztalosműhely preset
    payload_multi = {
        "product": {
            "sku": "BOSCH-GSR-18V-55",
            "name": "Bosch Professional GSR 18V-55 Akkus Fúrócsavarozó",
            "category": "szerszamgep",
            "raw_image_url": "https://cdn.profigepesz.hu/raw/bosch_gsr18v55_white.jpg"
        },
        "config": {
            "staging_mode": "category_presets",
            "preset_scene": "workshop_woodworking",
            "aspect_ratio_mode": "multi_marketing_pack"
        }
    }

    print("\n1. Teszt: Multi-marketing formátumok (1:1, 4:5, 9:16, 16:9) és műhely preset")
    res1 = run(payload_multi)
    assert res1.get("status") == "success", "Test 1 failed!"
    data1 = res1.get("studio_result", {})
    renders1 = data1.get("marketing_renders", {})
    prompt_meta1 = data1.get("ai_prompt_metadata", {})
    print(f"Termék: {data1.get('product_name')}")
    print(f"Alkalmazott díszlet: {data1.get('staging_scene')} | Világítás: {data1.get('lighting')}")
    print(f"Renderelt marketing formátumok száma: {len(renders1)}")
    for r_key, r_val in renders1.items():
        print(f"  -> [{r_key}] {r_val.get('label')}: {r_val.get('resolution')} ({r_val.get('image_url')})")
    assert len(renders1) == 4, "Expected 4 aspect ratio renders in multi-pack!"
    assert "1:1" in renders1 and "9:16" in renders1, "Missing core aspect ratios!"
    print("[OK] Multi-marketing csomag (Webshop, Feed, Reels, Banner) sikeresen legenerálva!")

    # 2. Teszt: Hibrid prompt finomhangolás és Trust Badge ráillesztés
    payload_badge = {
        "product": {
            "sku": "MAKITA-DHP-484",
            "name": "Makita DHP484Z Akkus Ütvefúró",
            "custom_staging_instructions": "Naplemente meleg fények, fűrészporos tölgyfa deszkák a háttérben, 8k makró részletesség."
        },
        "config": {
            "staging_mode": "custom_prompt_hybrid",
            "preset_scene": "workshop_woodworking",
            "branding_sync_mode": "trust_badge_overlay"
        }
    }

    print("\n2. Teszt: Hibrid prompt finomhangolás és 3 Év Garancia Trust Badge")
    res2 = run(payload_badge)
    data2 = res2.get("studio_result", {})
    prompt2 = data2.get("ai_prompt_metadata", {}).get("positive_prompt", "")
    branding2 = data2.get("branding_and_sync", {})
    print(f"Generált FLUX prompt: {prompt2[:110]}...")
    print(f"Trust Badge típus: {branding2.get('badge_type')} ({branding2.get('badge_text')})")
    print(f"Vízjel elhelyezés: {branding2.get('watermark_position')}")
    assert "Naplemente meleg fények" in prompt2, "Custom prompt was not incorporated!"
    assert branding2.get("badge_enabled") is True, "Trust badge should be enabled!"
    print("[OK] Hibrid prompt és minőségi garancia pecsét sikeresen ráillesztve!")

    # 3. Teszt: Négyzetes webshop galéria és interaktív előnézet
    payload_preview = {
        "product": {
            "sku": "DEWALT-DCD-796",
            "name": "DeWalt DCD796P2 Fúrócsavarozó"
        },
        "config": {
            "aspect_ratio_mode": "square_webshop_only",
            "branding_sync_mode": "interactive_preview_gallery"
        }
    }

    print("\n3. Teszt: 1:1 Négyzetes webshop galéria és interaktív előnézeti kapu")
    res3 = run(payload_preview)
    data3 = res3.get("studio_result", {})
    renders3 = data3.get("marketing_renders", {})
    branding3 = data3.get("branding_and_sync", {})
    print(f"Előnézeti link: {branding3.get('preview_gallery_url')}")
    print(f"Nagyfelbontású ZIP export: {branding3.get('high_res_download_zip')}")
    assert len(renders3) == 1, "Only 1:1 square render should be produced!"
    assert "compare?sku=" in branding3.get("preview_gallery_url", ""), "Missing compare URL!"
    print("[OK] Négyzetes galéria és interaktív előnézeti kapu sikeresen lefutott!")

    print("\n==================================================")
    print("MINDEN AI TERMÉKFOTÓ STÚDIÓ TESZT SIKERESEN LEFUTOTT! (3/3)")
    print("==================================================")

if __name__ == "__main__":
    test_ai_photo_studio()
