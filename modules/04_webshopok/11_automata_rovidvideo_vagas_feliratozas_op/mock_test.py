# -*- coding: utf-8 -*-
"""
Mock teszt az Automata Rovidvideo Vagas & Feliratozas modulhoz.
3 uzleti forgatokonyv tesztelese:
1. Hibrid virality scoring + Hormozi viralis felirat + zaro CTA kartya kuponnal
2. Tematikus termekteszt fokuszu vagas + minimalista premium felirat + ZIP HITL jovahagyas
3. Direct Auto-Publish pipeline TikTok, Reels es Shorts platformokra
"""

import sys
import os
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from handler import run


def test_scenario_1_hybrid_viral_clips():
    print("\n--- TESZT 1: Hibrid virality scoring + Hormozi stilus + Zaro CTA kuponnal ---")
    payload = {
        "video_id": "VID-TEST-001",
        "video_title": "Bosch Professional GBH 2-28 Furokalapacs Teljes Teszt",
        "source_video_url": "https://storage.webshop.hu/raw/bosch_gbh228.mp4",
        "duration_seconds": 960,
        "product": {
            "sku": "BOSCH-GBH-2-28",
            "name": "Bosch Professional GBH 2-28 Furokalapacs L-BOXX",
            "price_huf": 68900,
            "product_url": "https://webshop.hu/termekek/bosch-gbh-2-28"
        },
        "config": {
            "clipping_strategy": "hybrid_smart_clips",
            "caption_style": "selectable_dual_style",
            "publishing_pipeline": "hybrid_publish_or_review",
            "add_closing_cta_card": True,
            "flash_coupon_code": "REELS10"
        }
    }
    
    res = run(payload)
    print(f"Status: {res.get('status')}")
    print(f"Generalva: {res.get('total_clips_generated')} db klip")
    print(f"Pipeline statusz: {res.get('pipeline_status')}")
    
    clips = res.get("clips", [])
    top_clip = clips[0]
    print(f"Top klip cime: {top_clip.get('title')}")
    print(f"Virality Score: {top_clip.get('virality_score')}/100")
    print(f"Hook szoveg: {top_clip.get('hook_text')}")
    print(f"Renderelt MP4: {top_clip.get('rendered_video_url')}")
    print(f"Zaro kartya kupon: {top_clip.get('closing_cta_card', {}).get('coupon_display')}")
    print(f"TikTok caption reszlet: {top_clip.get('publishing_metadata', {}).get('tiktok', {}).get('caption')[:60]}...")
    
    assert res.get("status") == "success"
    assert res.get("total_clips_generated") == 3
    assert top_clip.get("virality_score") >= 90
    assert "REELS10" in top_clip.get("closing_cta_card", {}).get("coupon_display")
    print("[OK] Teszt 1 sikeresen lefutott!")


def test_scenario_2_thematic_minimalist_hitl():
    print("\n--- TESZT 2: Tematikus termekteszt + Minimalista felirat + ZIP export HITL ---")
    payload = {
        "video_id": "VID-TEST-002",
        "video_title": "DeWalt DCD796 Utofuroncsavarozo melysegi bemutato",
        "duration_seconds": 720,
        "product": {
            "sku": "DEWALT-DCD796",
            "name": "DeWalt DCD796 Utofuroncsavarozo",
            "price_huf": 84900
        },
        "config": {
            "clipping_strategy": "thematic_product_focus",
            "caption_style": "minimal_premium_clean",
            "publishing_pipeline": "zip_export_hitl_review",
            "flash_coupon_code": "DEWALT15"
        }
    }
    
    res = run(payload)
    print(f"Pipeline statusz: {res.get('pipeline_status')}")
    print(f"Szerkesztoi jovahagyas szukseges: {res.get('requires_human_approval')}")
    print(f"ZIP letoltes: {res.get('zip_package_download_url')}")
    print(f"Aktiv feliratstilus: {res.get('caption_styling', {}).get('active_style', {}).get('style_name')}")
    
    assert res.get("status") == "success"
    assert res.get("requires_human_approval") is True
    assert res.get("zip_package_download_url") is not None
    print("[OK] Teszt 2 sikeresen lefutott!")


def test_scenario_3_direct_auto_publish():
    print("\n--- TESZT 3: Direct Auto-Publish pipeline (TikTok, Reels, Shorts) ---")
    payload = {
        "video_id": "VID-TEST-003",
        "video_title": "Makita Akkus Furesz 30 masodperces unboxing",
        "duration_seconds": 300,
        "product": {
            "sku": "MAKITA-DUC254",
            "name": "Makita DUC254 Akkus Lanccfuresz",
            "price_huf": 92900
        },
        "config": {
            "clipping_strategy": "virality_score_auto",
            "caption_style": "hormozi_mrbeast_viral",
            "publishing_pipeline": "direct_auto_publish",
            "flash_coupon_code": "MAKITA10"
        }
    }
    
    res = run(payload)
    print(f"Pipeline statusz: {res.get('pipeline_status')}")
    print(f"Jovahagyas kikerulve (autonom): {not res.get('requires_human_approval')}")
    
    assert res.get("status") == "success"
    assert res.get("pipeline_status") == "QUEUED_FOR_AUTO_PUBLISHING"
    assert res.get("requires_human_approval") is False
    print("[OK] Teszt 3 sikeresen lefutott!")


if __name__ == "__main__":
    print("=== MODULE 4.11: AUTOMATA ROVIDVIDEO VAGAS & FELIRATOZAS MOCK TESZT ===")
    test_scenario_1_hybrid_viral_clips()
    test_scenario_2_thematic_minimalist_hitl()
    test_scenario_3_direct_auto_publish()
    print("\n[MINDEN TESZT SIKERESEN LEFUTOTT!]")
