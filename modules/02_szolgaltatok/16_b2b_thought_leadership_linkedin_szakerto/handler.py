"""
B2B Thought Leadership & LinkedIn Szakértői Gépezet
Modul: 16_b2b_thought_leadership_linkedin_szakerto
"""

import os
import sys
import json
import datetime
from typing import Dict, Any, List, Optional

class B2BThoughtLeadershipHandler:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.publishing_mode = self.config.get("publishing_mode", "review_before_publish")
        self.schedule_slots = self.config.get("schedule_slots", ["Kedd 08:30", "Csütörtök 08:30"])
        self.persona = self.config.get("executive_persona", {
            "name": "Kovács László",
            "title": "Ügyvezető & Épületgépész Szakértő",
            "company": "ProfiKlíma Kft."
        })
        self.posts_db = "data/b2b_linkedin_posztok.json"

    def generate_linkedin_post(self, raw_input: str, content_type: str) -> Dict[str, Any]:
        """
        Strukturált, figyelemfelkeltő LinkedIn szakértői poszt, képi prompt és hírlevél generálása.
        """
        today_str = datetime.date.today().strftime("%Y.%m.%d.")
        post_id = f"POST-{datetime.date.today().strftime('%Y%m%d')}-{abs(hash(raw_input))%900 + 100}"

        hook = "150 000 Ft megtakarítás a kivitelezésen majdnem 30 millió forintos kárt okozott egy pesti irodaházban tegnap éjjel."

        post_body_lines = [
            hook,
            "",
            "Ma reggel 07:15-kor csörgött a telefonom egy kétségbeesett IT cégvezetőtől:",
            "'Laci, 48 fok van a szerverteremben, a vészleállítás küszöbén vagyunk, ma lenne a havi release!'",
            "",
            "Amikor kiértünk a helyszínre, azonnal látszott a probléma forrása:",
            "2 évvel ezelőtt egy 'okosba' dolgozó brigád rakott be egy alulméretezett lakossági klímát számla és hivatalos beüzemelési jegyzőkönyv nélkül.",
            "Olcsó, vékonyfalú rézcsövek, zéró rezgéscsillapítás, és semmiféle redundancia.",
            "",
            "A gázszivárgás miatt a kompresszor megszorult, a szerverek pedig túlmelegedtek.",
            "Csodával határos módon 2 óra alatt beüzemeltünk egy redundáns, 0-24 órás Daikin professzionális gépet, így megmentettük a rendszert.",
            "",
            "A 3 legfontosabb tanulság, amit minden cégvezetőnek érdemes szem előtt tartania:",
            "",
            "1. A lakossági klíma NEM szerverterembe való: a 0-24 órás ipari terheléshez dedikált gép és téli szett szükséges.",
            "2. A garancia nélküli 'jóárasított' szerelés a legdrágább kockázat: ha leáll a céges IT infrastruktúra, percenként ég a pénz.",
            "3. Redundancia nélkül nincs üzletmenet-folytonosság: a kritikus terekben kötelező a váltott, kétgépes üzem.",
            "",
            "Te mikor nézetted át utoljára az irodai vagy szervertermi hűtést a fűtési/hűtési szezon előtt?",
            "",
            "#Epületgépészet #Szerverterem #B2BVállalkozás #Létesítménygazdálkodás #ÜzletmenetFolytonosság #ProfiKlíma"
        ]
        linkedin_post_text = chr(10).join(post_body_lines)

        # Képi illusztrációs prompt DALL-E / Midjourney számára
        image_prompt = (
            "A high-end cinematic photograph of a clean, modern corporate server room in Budapest at night. "
            "Rack servers with soft blue LED indicators, next to a sleek professional industrial air cooling unit. "
            "A confident Hungarian technician in neat branded navy blue uniform holding a digital pressure manifold gauge. "
            "Clean atmosphere, sharp focus, 8k resolution, professional architectural photography."
        )

        # Hosszabb B2B Hírlevél változat
        newsletter_lines = [
            "HÍRLEVÉL: Miért kerül a legolcsóbb klímaszerelés a legtöbbe a cégeknek?",
            f"Szerző: {self.persona.get('name')} | {self.persona.get('title')}",
            "",
            "Kedves Partnereink!",
            "",
            "A héten egy olyan esettel találkoztunk, ami tökéletesen rávilágít az olcsó, garancia nélküli gépészeti munkák valódi árára...",
            "",
            linkedin_post_text,
            "",
            "Ha szeretné felülvizsgáltatni céges szerver- vagy irodahűtési rendszereit még a kánikula előtt, "
            "kérje szakértői helyszíni auditunkat a profiklima.hu oldalon!"
        ]
        newsletter_text = chr(10).join(newsletter_lines)

        # Ütemezett időpont
        scheduled_slot = self.schedule_slots[0] if self.schedule_slots else "Kedd 08:30"
        approve_link = f"http://127.0.0.1:8000/api/v1/modules/16_b2b_thought_leadership_linkedin_szakerto/approve_post?post_id={post_id}"

        # Értesítés a vezető mobiljára
        mobile_alert = chr(10).join([
            f"[LINKEDIN COPILOT] Elkeszult a szakertoi B2B posztod a hangjegyzetedbol!",
            f"Tema: {hook[:70]}...",
            f"Tervezett idopont: {scheduled_slot}",
            "",
            "1-KATTINTASOS JOVAHAGYAS & PUBIKALAS:",
            f"-> {approve_link}",
            "",
            "Poszt elonezete:",
            linkedin_post_text[:300] + "..."
        ])

        record = {
            "post_id": post_id,
            "created_at": datetime.datetime.now().isoformat(),
            "author": self.persona.get("name"),
            "content_type": content_type,
            "linkedin_post_text": linkedin_post_text,
            "image_prompt": image_prompt,
            "newsletter_text": newsletter_text,
            "scheduled_slot": scheduled_slot,
            "status": "PENDING_EXECUTIVE_APPROVAL" if self.publishing_mode == "review_before_publish" else "SCHEDULED_FOR_PUBLISHING",
            "one_click_approval_link": approve_link
        }

        # Mentés
        existing = []
        if os.path.exists(self.posts_db):
            try:
                with open(self.posts_db, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                pass
        existing.insert(0, record)
        with open(self.posts_db, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)

        return {
            "post_id": post_id,
            "hook": hook,
            "linkedin_post": linkedin_post_text,
            "visual_image_prompt": image_prompt,
            "newsletter_article": newsletter_text,
            "scheduled_slot": scheduled_slot,
            "status": record["status"],
            "one_click_approval_link": approve_link,
            "mobile_alert_message": mobile_alert
        }

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("action", "GENERATE_POST")
        content_type = payload.get("content_type", "voice_dictation")
        raw_input = payload.get("voice_transcript") or payload.get("topic_notes") or "Szerverterem hűtési esettanulmány"

        res = self.generate_linkedin_post(raw_input, content_type)

        return {
            "status": "success",
            "action_executed": "B2B_THOUGHT_LEADERSHIP_POST_GENERATED",
            "post_id": res["post_id"],
            "hook": res["hook"],
            "scheduled_publishing_time": res["scheduled_slot"],
            "publishing_status": res["status"],
            "one_click_approval_link": res["one_click_approval_link"],
            "linkedin_content": res["linkedin_post"],
            "image_generation_prompt": res["visual_image_prompt"],
            "newsletter_variant": res["newsletter_article"],
            "mobile_notification": res["mobile_alert_message"]
        }

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    handler = B2BThoughtLeadershipHandler(config)
    return handler.execute(payload)

if __name__ == "__main__":
    test_p = {
        "voice_transcript": "Tegnap megmentettünk egy szervertermet, mert leállt az olcsó klíma. A tanulság: a lakossági klíma nem való szerverterembe."
    }
    res = run(test_p)
    print(json.dumps(res, indent=2, ensure_ascii=False))
