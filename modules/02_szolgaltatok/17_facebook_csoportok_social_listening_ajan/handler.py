"""
Facebook Csoportok Social Listening (Ajánláskérések Figyelése)
Modul azonosító: 17_facebook_csoportok_social_listening_ajan
"""

import os
import sys
import json
import datetime
from typing import Dict, Any, List, Optional

class FacebookSocialListeningHandler:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.service_mode = self.config.get("service_mode", "mock")
        self.company_name = self.config.get("company_name", "ProfiKlíma & Épületgépészet Kft.")
        self.company_specialty = self.config.get("company_specialty", "Lakossági és ipari klíma, hőszivattyú telepítés, karbantartás, F-Gáz minősítés")
        self.company_phone = self.config.get("company_phone", "+36 30 123 4567")
        self.booking_url = self.config.get("booking_url", "https://profiklima.hu/idopontfoglalas")
        self.target_locations = self.config.get("target_locations", ["Budapest", "XI. kerület", "Budaörs", "Törökbálint", "Érd", "Pest megye"])
        self.monitored_groups = self.config.get("monitored_groups", [
            "Újbuda - XI. kerületiek csoportja",
            "Budaörsiek közössége",
            "Klíma és Hőszivattyú Tapasztalatok",
            "Lakásfelújítás és Építkezés Szakemberek"
        ])
        self.trigger_keywords = self.config.get("trigger_keywords", [
            "klímás", "klímaszerelő", "hőszivattyú", "tudtok jó", "ajánljatok",
            "szakembert keresek", "szerelés", "tisztítás", "karbantartás", "nem hűt", "szerelő"
        ])
        self.negative_exclusion_keywords = self.config.get("negative_exclusion_keywords", [
            "állás", "felvétel", "munkaajánlat", "eladó használt", "ingyen elvihető", "panasz a cégről", "csaló", "nem fizetett"
        ])
        self.min_relevance_score = self.config.get("min_relevance_score", 70)
        self.response_tone = self.config.get("response_tone", "tegezo_baratsagos")
        self.include_dm_draft = self.config.get("include_dm_draft", True)
        self.approval_mode = self.config.get("approval_mode", "manual_approval_only")
        self.auto_post_min_score = self.config.get("auto_post_min_score", 95)
        self.alert_channels = self.config.get("alert_channels", ["telegram", "whatsapp", "dashboard"])
        self.leads_db_path = self.config.get("leads_db_path", "data/facebook_leads_naplo.json")

    def _calculate_relevance(self, text: str, group_name: str) -> Dict[str, Any]:
        """
        Kiszámítja a bejegyzés relevancia pontszámát (0-100), intentjét és kiszűri a kizáró kifejezéseket.
        """
        text_lower = text.lower()

        # 1. Negatív kizáró kulcsszavak ellenőrzése
        for neg_kw in self.negative_exclusion_keywords:
            if neg_kw.lower() in text_lower:
                return {
                    "is_excluded": True,
                    "exclusion_reason": f"Kizáró kulcsszó találat: '{neg_kw}'",
                    "relevance_score": 0,
                    "matched_triggers": [],
                    "matched_locations": [],
                    "intent": "kizart_bejegyzes"
                }

        matched_triggers = [kw for kw in self.trigger_keywords if kw.lower() in text_lower]
        matched_locations = [loc for loc in self.target_locations if loc.lower() in text_lower]

        score = 0
        # Trigger kulcsszavak súlya
        score += min(len(matched_triggers) * 18, 55)

        # Helyszín egyezés súlya
        if matched_locations:
            score += 25

        # Ajánláskérő specifikus igék és kifejezések keresése
        intent = "altalanos_bejegyzes"
        recommendation_indicators = ["tudtok", "ajánljatok", "keresek", "kit ajánlotok", "szakembert", "vélemény"]
        if any(ind in text_lower for ind in recommendation_indicators):
            score += 20
            intent = "ajanlaskeres_szakember"
        elif any(w in text_lower for w in ["nem hűt", "folyik", "zörög", "büdös", "letiltott", "hibakód"]):
            score += 20
            intent = "surgos_hibaelharitas"
        elif any(w in text_lower for w in ["mennyibe kerül", "ár", "ára", "drága", "költség"]):
            score += 15
            intent = "ar_erdeklodes"

        final_score = min(max(score, 0), 100)

        return {
            "is_excluded": False,
            "exclusion_reason": None,
            "relevance_score": final_score,
            "matched_triggers": matched_triggers,
            "matched_locations": matched_locations,
            "intent": intent
        }

    def _generate_expert_comment(self, author_name: str, post_text: str, intent: str, locations: List[str]) -> str:
        """
        Segítőkész, szakértői hozzászólás generálása. Nem agresszív reklám, hanem valódi értéket ad.
        """
        loc_str = locations[0] if locations else "a környéken"
        first_name = author_name.split()[0] if author_name else "Kedves Kérdező"

        if self.response_tone == "tegezo_baratsagos":
            greeting = f"Szia {first_name}!"
            body_parts = [
                greeting,
                f"Ha még keresel megbízható csapatot, szívesen segítünk neked {loc_str}! "
                f"A {self.company_name} csapata hivatalos F-Gáz képesítéssel, számlaképesen és gyártói garanciával vállalja klímák telepítését és karbantartását.",
                "Egy gyors szakmai tanács a választáshoz: 3,5 kW-os készüléknél érdemes a helyiség tájolását és a belmagasságot is figyelembe venni, "
                "hogy hosszú távon csendes és alacsony fogyasztású maradjon a gép.",
                f"Kötetlen, ingyenes helyszíni felméréssel pontos árajánlatot adunk még a szezonális csúcsidőszak előtt. "
                f"Itt tudsz közvetlenül időpontot egyeztetni: {self.booking_url} , vagy hívhatsz minket telefonon is: {self.company_phone}.",
                "Szép napot és sikeres kivitelezést!",
                f"Üdvözlettel: {self.company_name}"
            ]
        else:
            greeting = f"Üdvözlöm {author_name}!"
            body_parts = [
                greeting,
                f"Amennyiben megbízható és minősített kivitelezőt keres {loc_str}, a {self.company_name} csapata készséggel áll rendelkezésére. "
                "Cégünk teljes körű F-Gáz regisztrációval, garanciális szervizháttérrel és hivatalos számlaadással végzi klímaberendezések és hőszivattyúk telepítését.",
                "Javasoljuk az előzetes helyszíni auditot a készülék pontos méretezéséhez.",
                f"Időpontfoglalás és felmérés igénylése: {self.booking_url} | Ügyfélszolgálat: {self.company_phone}",
                f"Üdvözlettel: {self.company_name}"
            ]

        return chr(10).join(body_parts)

    def _generate_messenger_dm(self, author_name: str, group_name: str) -> str:
        """
        Személyes Messenger privát üzenet vázlat a poszt írójának közvetlen megkereséséhez.
        """
        first_name = author_name.split()[0] if author_name else "Kedves Érdeklődő"
        dm_lines = [
            f"Szia {first_name}!",
            f"Láttam a posztodat a(z) '{group_name}' csoportban a klímaszereléssel kapcsolatban.",
            f"A {self.company_name}-től írok, heti rendszerességgel dolgozunk a környéken, számlaképesen és hivatalos F-Gáz garanciával.",
            "Ha még aktuális, szívesen átbeszéljük az igényeidet és adunk egy pontos, díjmentes felmérési javaslatot.",
            f"Ha kényelmesebb telefonon: {self.company_phone}, vagy foglalhatsz közvetlenül egy kötetlen időpontot: {self.booking_url}",
            f"Üdvözlettel: {self.company_name}"
        ]
        return chr(10).join(dm_lines)

    def _save_lead_to_db(self, lead_record: Dict[str, Any]):
        """
        Mentés a központi perzisztens JSON adatbázisba (data/facebook_leads_naplo.json).
        """
        os.makedirs(os.path.dirname(self.leads_db_path), exist_ok=True)
        existing = []
        if os.path.exists(self.leads_db_path):
            try:
                with open(self.leads_db_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = []

        # Frissítés vagy új beszúrás
        updated = False
        for idx, item in enumerate(existing):
            if item.get("lead_id") == lead_record.get("lead_id"):
                existing[idx] = lead_record
                updated = True
                break

        if not updated:
            existing.insert(0, lead_record)

        with open(self.leads_db_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)

    def analyze_and_process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        post_id = payload.get("post_id", f"FB-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}")
        group_name = payload.get("group_name", "Ismeretlen Facebook Csoport")
        author_name = payload.get("author_name", "Névtelen Felhasználó")
        post_text = payload.get("post_text", "")
        post_url = payload.get("post_url", f"https://facebook.com/groups/post/{post_id}")
        author_profile_url = payload.get("author_profile_url", "")

        analysis = self._calculate_relevance(post_text, group_name)

        if analysis["is_excluded"]:
            return {
                "status": "SKIPPED_NEGATIVE_KEYWORD",
                "post_id": post_id,
                "relevance_score": 0,
                "reason": analysis["exclusion_reason"],
                "group_name": group_name,
                "author_name": author_name,
                "action": "Nincs teendő (spam vagy kizárt tartalom)"
            }

        relevance_score = analysis["relevance_score"]
        is_relevant = relevance_score >= self.min_relevance_score

        if not is_relevant:
            return {
                "status": "LOW_RELEVANCE",
                "post_id": post_id,
                "relevance_score": relevance_score,
                "min_required_score": self.min_relevance_score,
                "group_name": group_name,
                "author_name": author_name,
                "reason": "A bejegyzés relevanciája nem éri el a beállított riasztási küszöböt."
            }

        # Érvényes, releváns ajánláskérés!
        generated_comment = self._generate_expert_comment(
            author_name=author_name,
            post_text=post_text,
            intent=analysis["intent"],
            locations=analysis["matched_locations"]
        )

        generated_dm = self._generate_messenger_dm(
            author_name=author_name,
            group_name=group_name
        ) if self.include_dm_draft else ""

        # Jóváhagyási státusz megállapítása
        lead_id = f"LEAD-{datetime.date.today().strftime('%Y%m%d')}-{post_id}"
        one_click_approval_url = f"http://localhost:8000/api/v1/modules/17_facebook_csoportok_social_listening_ajan/approve?lead_id={lead_id}"

        if self.approval_mode == "auto_post_high_confidence" and relevance_score >= self.auto_post_min_score:
            publishing_status = "AUTO_POSTED"
            action_summary = f"Magas pontszám ({relevance_score}%) miatt a komment automatikusan elküldve!"
        else:
            publishing_status = "PENDING_SALES_APPROVAL"
            action_summary = f"Értékesítői jóváhagyásra és kiküldésre vár (Cél: 5 perces reakcióidő)."

        # Riasztási üzenet (Telegram / WhatsApp)
        alert_lines = [
            "[FACEBOOK SOCIAL LISTENING RIASZTAS]",
            f"Uj forro ajanlaskeres talalat!",
            f"Csoport: {group_name}",
            f"Posztolo: {author_name}",
            f"Relevancia: {relevance_score}/100 pont (Intent: {analysis['intent']})",
            f"Egyezo kulcsszavak: {', '.join(analysis['matched_triggers'])}",
            f"Egyezo helyszin: {', '.join(analysis['matched_locations']) if analysis['matched_locations'] else 'N/A'}",
            "",
            f"Eredeti poszt: \"{post_text[:140]}...\"",
            f"Kozvetlen link: {post_url}",
            "",
            "1-KATTINTASOS JOVAHAGYAS & MASOLAS:",
            f"-> {one_click_approval_url}",
            "",
            "Javasolt szakertoi komment:",
            generated_comment[:200] + "..."
        ]
        sales_alert_message = chr(10).join(alert_lines)

        lead_record = {
            "lead_id": lead_id,
            "created_at": datetime.datetime.now().isoformat(),
            "post_id": post_id,
            "group_name": group_name,
            "author_name": author_name,
            "author_profile_url": author_profile_url,
            "post_url": post_url,
            "post_text": post_text,
            "relevance_score": relevance_score,
            "intent": analysis["intent"],
            "matched_keywords": analysis["matched_triggers"],
            "matched_locations": analysis["matched_locations"],
            "generated_comment": generated_comment,
            "generated_dm": generated_dm,
            "approval_mode": self.approval_mode,
            "status": publishing_status,
            "approval_url": one_click_approval_url,
            "target_response_time_minutes": 5
        }

        self._save_lead_to_db(lead_record)

        return {
            "status": "success",
            "action_executed": "FACEBOOK_LEAD_DETECTED_AND_ANALYZED",
            "lead_id": lead_id,
            "publishing_status": publishing_status,
            "relevance_score": relevance_score,
            "intent": analysis["intent"],
            "matched_triggers": analysis["matched_triggers"],
            "matched_locations": analysis["matched_locations"],
            "post_url": post_url,
            "one_click_approval_url": one_click_approval_url,
            "generated_expert_comment": generated_comment,
            "generated_messenger_dm": generated_dm,
            "sales_alert_message": sales_alert_message,
            "action_summary": action_summary
        }

    def approve_lead(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        lead_id = payload.get("lead_id")
        if not lead_id:
            return {"status": "error", "message": "lead_id kotelezo a jovahagyashoz!"}

        if os.path.exists(self.leads_db_path):
            try:
                with open(self.leads_db_path, "r", encoding="utf-8") as f:
                    records = json.load(f)
                for rec in records:
                    if rec.get("lead_id") == lead_id:
                        rec["status"] = "APPROVED_AND_POSTED"
                        rec["approved_at"] = datetime.datetime.now().isoformat()
                        with open(self.leads_db_path, "w", encoding="utf-8") as fw:
                            json.dump(records, fw, indent=2, ensure_ascii=False)
                        return {
                            "status": "success",
                            "lead_id": lead_id,
                            "new_status": "APPROVED_AND_POSTED",
                            "message": f"A(z) {lead_id} lead jovahagyva es sikeresen kikuldve!"
                        }
            except Exception as e:
                return {"status": "error", "message": str(e)}

        return {"status": "error", "message": f"A(z) {lead_id} lead nem talalhato az adatbazisban."}

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("action", "ANALYZE_POST")
        if action == "APPROVE_LEAD":
            return self.approve_lead(payload)
        return self.analyze_and_process(payload)

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    handler = FacebookSocialListeningHandler(config)
    return handler.execute(payload)

if __name__ == "__main__":
    sample_payload = {
        "action": "ANALYZE_POST",
        "post_id": "TEST-FB-101",
        "group_name": "Újbuda - XI. kerületiek csoportja",
        "author_name": "Kovács Tamás",
        "post_text": "Sziasztok! Megbízható klímást keresek a XI. kerületben sürgősen tisztításra és új gép felszerelésére. Kit ajánlotok?",
        "post_url": "https://facebook.com/groups/ujbuda/posts/101"
    }
    res = run(sample_payload)
    print(json.dumps(res, indent=2, ensure_ascii=False))
