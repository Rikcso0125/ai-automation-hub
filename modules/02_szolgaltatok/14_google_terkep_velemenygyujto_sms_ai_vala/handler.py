"""
Google Térkép Véleménygyűjtő SMS & AI Válaszíró (Helyi SEO)
Modul: 14_google_terkep_velemenygyujto_sms_ai_vala
"""

import os
import sys
import json
import datetime
from typing import Dict, Any, List, Optional

class GoogleReviewSeoHandler:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.primary_channel = self.config.get("primary_channel", "whatsapp_first_with_sms_fallback")
        self.send_delay_mode = self.config.get("send_delay_mode", "1_hour_after_job")
        self.google_review_url = self.config.get("google_review_url", "https://g.page/r/profiklima-budapest/review")
        self.gatekeeper_enabled = self.config.get("gatekeeper_enabled", True)
        self.approval_mode = self.config.get("approval_mode", "positive_auto_negative_review")
        self.local_keywords = self.config.get("local_seo_keywords", ["klímaszerelés", "Budapest", "karbantartás"])
        self.company_name = self.config.get("company_name", "ProfiKlíma Kft.")
        self.db_path = "data/google_velemenyek_naplo.json"

    def compose_review_request(self, customer: Dict[str, Any], job: Dict[str, Any], tech: Dict[str, Any]) -> Dict[str, Any]:
        """
        Összeállítja a személyre szabott értékeléskérő üzenetet a Gatekeeper linkkel.
        """
        c_name = customer.get("name", "Ügyfelünk")
        service = job.get("service_name", "munkavégzés")
        t_name = tech.get("name", "kollégánk")

        gatekeeper_link = f"http://127.0.0.1:8000/api/v1/modules/14_google_terkep_velemenygyujto_sms_ai_vala/gate?job_id={job.get('job_id')}"

        message_text = chr(10).join([
            f"Kedves {c_name}!",
            f"Köszönjük, hogy a {self.company_name}-t választotta a(z) {service} elvégzésére.",
            f"Bízunk benne, hogy {t_name} munkájával és a berendezéssel maximálisan elégedett!",
            "",
            "Egyetlen kattintással segítheti munkánkat egy rövid csillagos értékeléssel az alábbi linken:",
            f"-> {gatekeeper_link}",
            "",
            "Hálásan köszönjük támogatását!"
        ])

        return {
            "target_phone": customer.get("phone"),
            "channel_used": self.primary_channel,
            "scheduled_time": "1 órával a befejezés után (14:30)",
            "gatekeeper_link": gatekeeper_link,
            "message_text": message_text
        }

    def generate_seo_reply(self, review: Dict[str, Any], job: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        AI által generált helyi SEO-erősítő vagy diplomáciai válasz.
        """
        rating = int(review.get("rating_stars", 5))
        author = review.get("author_name", "Kedves Ügyfelünk")
        comment = review.get("comment", "")
        district = job.get("site_district", "Budapest") if job else "Budapest"
        service = job.get("service_name", "klímaszerelés") if job else "klímaszerelés"

        if rating >= 4:
            # Pozitív vélemény helyi SEO kulcsszavakkal
            reply_text = (
                f"Kedves {author}! Nagyon köszönjük a megtisztelő {rating} csillagos értékelést és a pozitív visszajelzést! "
                f"Örömünkre szolgál, hogy a {district} területén végzett {service} és szerviztechnikusaink precíz hozzáállása "
                f"elnyerte a tetszését. Bármikor állunk rendelkezésére {self.company_name} megbízható garanciális karbantartással is!"
            )
            is_auto_publish = (self.approval_mode in ["positive_auto_negative_review", "full_auto"])
            status = "PUBLISHED_TO_GOOGLE_MAPS" if is_auto_publish else "PENDING_APPROVAL"
            manager_alert = False
        else:
            # Negatív / Panaszos vélemény (1-3 csillag)
            reply_text = (
                f"Kedves {author}! Nagyon sajnáljuk, hogy tapasztalata nem volt maradéktalanul felhőtlen. "
                f"Cégünk számára a legmagasabb minőség az első. Kérjük, vegye fel a közvetlen kapcsolatot ügyfélszolgálati vezetőnkkel "
                f"a +36 30 555 7788 telefonszámon vagy az ugyfelszolgalat@profiklima.hu címen, hogy azonnal és díjmentesen orvosolhassuk a problémát!"
            )
            status = "PENDING_MANAGER_APPROVAL"
            manager_alert = True

        return {
            "rating_stars": rating,
            "reply_text": reply_text,
            "contains_local_seo": rating >= 4,
            "seo_keywords_injected": [district, service, self.company_name],
            "publication_status": status,
            "manager_alert_triggered": manager_alert
        }

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("action", "SEND_REVIEW_REQUEST")

        if action == "SEND_REVIEW_REQUEST":
            customer = payload.get("customer", {"name": "Ügyfél", "phone": "+36 30 000 0000"})
            job = payload.get("completed_job", {"job_id": "JOB-DEFAULT", "service_name": "Klímaszerelés"})
            tech = payload.get("technician", {"name": "Kollégánk"})

            request_data = self.compose_review_request(customer, job, tech)

            return {
                "status": "success",
                "action_executed": "REVIEW_REQUEST_SCHEDULED",
                "job_id": job.get("job_id"),
                "customer_name": customer.get("name"),
                "delivery_channel": request_data["channel_used"],
                "gatekeeper_enabled": self.gatekeeper_enabled,
                "gatekeeper_link": request_data["gatekeeper_link"],
                "message_preview": request_data["message_text"]
            }

        elif action == "PROCESS_INCOMING_REVIEW":
            review = payload.get("review_data", {"rating_stars": 5, "author_name": "Értékelő"})
            job = payload.get("completed_job")
            reply_result = self.generate_seo_reply(review, job)

            # Riasztási link ha negatív
            approval_link = None
            if reply_result["manager_alert_triggered"]:
                approval_link = f"http://127.0.0.1:8000/api/v1/modules/14_google_terkep_velemenygyujto_sms_ai_vala/approve?review_id={review.get('review_id', 'REV-01')}"

            # Naplózás
            log_record = {
                "timestamp": datetime.datetime.now().isoformat(),
                "author": review.get("author_name"),
                "stars": review.get("rating_stars"),
                "comment": review.get("comment"),
                "reply": reply_result["reply_text"],
                "status": reply_result["publication_status"]
            }
            existing = []
            if os.path.exists(self.db_path):
                try:
                    with open(self.db_path, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                except Exception:
                    pass
            existing.append(log_record)
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)

            return {
                "status": "success",
                "action_executed": "REVIEW_REPLY_GENERATED",
                "rating_stars": reply_result["rating_stars"],
                "publication_status": reply_result["publication_status"],
                "contains_local_seo": reply_result["contains_local_seo"],
                "generated_reply": reply_result["reply_text"],
                "manager_alert_triggered": reply_result["manager_alert_triggered"],
                "one_click_approval_link": approval_link
            }

        return {"status": "error", "message": f"Ismeretlen akció: {action}"}

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    handler = GoogleReviewSeoHandler(config)
    return handler.execute(payload)

if __name__ == "__main__":
    test_p = {
        "action": "SEND_REVIEW_REQUEST",
        "customer": {"name": "Németh Krisztina", "phone": "+36 30 555 9988"},
        "completed_job": {"job_id": "JOB-TEST", "service_name": "Klímaszerelés"}
    }
    res = run(test_p)
    print(json.dumps(res, indent=2, ensure_ascii=False))
