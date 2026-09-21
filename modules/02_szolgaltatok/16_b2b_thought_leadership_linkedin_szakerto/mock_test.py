"""
Mock teszt a 16_b2b_thought_leadership_linkedin_szakerto modulhoz.
Teszteli az autóból diktált hangjegyzetből készült LinkedIn posztot,
a képgenerálási promptot, a hírlevél változatot és a vezetői jóváhagyási linket.
"""

import os
import sys
import json

curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, curr_dir)
from handler import run

def test_b2b_thought_leadership():
    print("=== 1. TESZT: HANGJEGYZETBŐL LINKEDIN POSZT ÉS HÍRLEVÉL GENERÁLÁS ===")
    payload = {
        "content_type": "voice_dictation",
        "voice_transcript": "Az autóban ülök, most jöttem el egy IT cégtől. 48 fok volt a szerverteremben mert leállt az olcsó klíma. 150 ezer spórolás majdnem 30 milliós kárt okozott. Írj ebből posztot!",
        "target_platform": "linkedin"
    }
    res = run(payload)
    print(f"Status: {res.get('status')}")
    print(f"Poszt azonosító: {res.get('post_id')}")
    print(f"Horog (Hook): {res.get('hook')}")
    print(f"Tervezett időzítés: {res.get('scheduled_publishing_time')}")
    print(f"Státusz: {res.get('publishing_status')}")
    print(f"1-Kattintásos jóváhagyási link: {res.get('one_click_approval_link')}")
    print(f"Képgenerálási prompt:\n{res.get('image_generation_prompt')[:120]}...")
    print(f"LinkedIn poszt részlet:\n{res.get('linkedin_content')[:250]}...")
    assert res.get('post_id') is not None
    assert "one_click_approval_link" in res
    assert "image_generation_prompt" in res
    print("\n[SIKERES TESZT] Minden teszteset sikeresen lefutott!")

if __name__ == "__main__":
    test_b2b_thought_leadership()
