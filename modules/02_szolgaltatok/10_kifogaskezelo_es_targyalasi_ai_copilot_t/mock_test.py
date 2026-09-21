"""
Mock teszt a 10_kifogaskezelo_es_targyalasi_ai_copilot_t modulhoz.
Teszteli az árkifogás és a halogatás felismerését, a 3 szintű stratégiát
(ROI, Socratic, Downsell), a másolható sablonokat és a mobilos bot kimenetet.
"""

import os
import sys
import json

curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, curr_dir)
from handler import run

def test_objection_copilot():
    print("=== 1. TESZT: ÁRKIFOGÁS ÉS KONKURENCIA 'OKOSBA' KEZELÉSE ===")
    payload_price = {
        "customer": {"name": "Molnár Zoltán", "company": "Molnár Építőipari Kft."},
        "quoted_deal": {
            "quote_id": "AJ-20260920-5512",
            "service": "2 db Daikin split klíma irodai telepítése",
            "total_gross_huf": 720000
        },
        "customer_objection_input": "A Molnár úr szerint túl drágák vagyunk, mert a szomszéd Józsi meg a másik brigád 180 ezerrel olcsóbban megcsinálja számla nélkül."
    }
    res_price = run(payload_price)
    print(f"Status: {res_price.get('status')}")
    det = res_price.get("detected_objection", {})
    print(f"Felismerve: {det.get('category')} (Megbízhatóság: {det.get('confidence')*100:.0f}%)")
    print(f"Cím: {det.get('title')}")
    strat = res_price.get("strategies", {})
    print(f"ROI érvek száma: {len(strat.get('strategy_roi_tco', {}).get('verbal_pitch_points', []))}")
    print(f"Rávezető kérdések száma: {len(strat.get('strategy_socratic', {}).get('probing_questions', []))}")
    print(f"Karcsúsított alternatívák: {len(strat.get('strategy_downsell', {}).get('action_steps', []))}")
    assert det.get("category") == "price_too_high"
    assert "whatsapp_sms" in strat.get("ready_to_send_templates", {})

    print("\n=== 2. TESZT: HALOGATÁS ÉS BIZONYTALANSÁG KEZELÉSE ===")
    payload_delay = {
        "customer": {"name": "Nagy Andrea", "company": "Nagy & Társa Bt."},
        "quoted_deal": {"service": "Hőszivattyús fűtéskorszerűsítés", "total_gross_huf": 2400000},
        "customer_objection_input": "Köszönjük az ajánlatot, még gondolkodunk rajta a férjemmel, majd visszatérünk rá később ősszel."
    }
    res_delay = run(payload_delay)
    det_delay = res_delay.get("detected_objection", {})
    print(f"Felismerve: {det_delay.get('category')} (Megbízhatóság: {det_delay.get('confidence')*100:.0f}%)")
    print(f"Cím: {det_delay.get('title')}")
    assert det_delay.get("category") == "delay_thinking"
    print("\nMobilos összefoglaló az értékesítőnek:\n" + res_price.get("mobile_copilot_quick_response", ""))
    print("\n[SIKERES TESZT] Minden teszteset sikeresen lefutott!")

if __name__ == "__main__":
    test_objection_copilot()
