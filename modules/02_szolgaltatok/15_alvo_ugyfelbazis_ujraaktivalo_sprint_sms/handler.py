"""
Alvó Ügyfélbázis Újraaktiváló Sprint (SMS / Email / WhatsApp)
Modul: 15_alvo_ugyfelbazis_ujraaktivalo_sprint_sms
"""

import os
import sys
import json
import datetime
from typing import Dict, Any, List, Optional

class DormantClientReactivationHandler:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.inactivity_threshold_days = int(self.config.get("inactivity_threshold_days", 180))
        self.drip_batch_size = int(self.config.get("drip_batch_size_per_day", 25))
        self.require_approval = self.config.get("require_manager_approval", True)
        self.est_revenue_per_client = int(self.config.get("estimated_revenue_per_customer_huf", 24000))
        self.offer_text = self.config.get("offer_text", "Szezon előtti jótállásmegőrző klímatisztítás 15% előfoglalási kedvezménnyel.")
        self.campaigns_file = "data/reaktivacios_kampanyok.json"

    def scan_and_segment_dormant(self, client_list: List[Dict[str, Any]], days_threshold: int) -> List[Dict[str, Any]]:
        """
        Kiszűri azokat az ügyfeleket, akik az inaktivitási küszöbnél régebben vették igénybe a szolgáltatást.
        """
        now = datetime.date.today()
        dormant = []

        for c in client_list:
            last_date_str = c.get("last_service_date")
            is_dormant = True
            if last_date_str:
                try:
                    last_date = datetime.datetime.strptime(last_date_str, "%Y-%m-%d").date()
                    delta = (now - last_date).days
                    is_dormant = (delta >= days_threshold)
                    c["days_since_last_service"] = delta
                except Exception:
                    c["days_since_last_service"] = days_threshold + 30
            else:
                c["days_since_last_service"] = days_threshold + 60

            if is_dormant:
                dormant.append(c)

        return dormant

    def prepare_campaign(self, campaign_name: str, service: str, dormant_clients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Kampány összeállítása: Drip ütemezés, várható bevétel és vezetői jóváhagyási link.
        """
        today_code = datetime.date.today().strftime("%Y%m%d")
        campaign_id = f"SPRINT-{today_code}-{abs(hash(campaign_name))%900 + 100}"

        total_dormant = len(dormant_clients)
        potential_revenue = total_dormant * self.est_revenue_per_client

        # Drip kötegek felosztása
        batch_size = max(1, self.drip_batch_size)
        total_batches = (total_dormant + batch_size - 1) // batch_size

        batches = []
        for i in range(total_batches):
            batch_slice = dormant_clients[i*batch_size : (i+1)*batch_size]
            batches.append({
                "batch_number": i + 1,
                "scheduled_day": f"{i + 1}. munkanap",
                "client_count": len(batch_slice),
                "client_ids": [c.get("id", f"CL-{idx}") for idx, c in enumerate(batch_slice)]
            })

        approve_link = f"http://127.0.0.1:8000/api/v1/modules/15_alvo_ugyfelbazis_ujraaktivalo_sprint_sms/approve_campaign?campaign_id={campaign_id}"

        # Minta üzenet az ügyfélnek
        sample_client = dormant_clients[0] if dormant_clients else {"name": "Ügyfelünk"}
        sample_message = chr(10).join([
            f"Kedves {sample_client.get('name')}!",
            f"Kollégánk legutóbb régebben járt Önöknél klímakarbantartáson.",
            f"A fűtési/hűtési szezon előtt most {self.offer_text} biztosítunk visszatérő ügyfeleinknek.",
            "",
            "Időpontját 1 kattintással lefoglalhatja a naptárunkban:",
            f"-> http://127.0.0.1:8000/api/v1/modules/03_conversational_naptarkezeles_idopontfogl/book?c_id={sample_client.get('id', 'CL-01')}",
            "",
            "Vagy egyszerűen válaszoljon erre az üzenetre a kívánt nappal!"
        ])

        summary = {
            "campaign_id": campaign_id,
            "campaign_name": campaign_name,
            "target_service": service,
            "dormant_clients_count": total_dormant,
            "estimated_potential_revenue_huf": potential_revenue,
            "drip_settings": {
                "batch_size_per_day": self.drip_batch_size,
                "total_drip_days": total_batches,
                "capacity_protected": True
            },
            "batches_preview": batches,
            "sample_message_text": sample_message,
            "status": "WAITING_FOR_MANAGER_APPROVAL" if self.require_approval else "APPROVED",
            "one_click_approval_link": approve_link
        }

        # Mentés adatbázisba
        existing = []
        if os.path.exists(self.campaigns_file):
            try:
                with open(self.campaigns_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                pass
        existing.insert(0, summary)
        with open(self.campaigns_file, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)

        return summary

    def handle_two_way_reply(self, customer_phone: str, incoming_text: str) -> Dict[str, Any]:
        """
        Kétirányú AI csevegés az újraaktiváló üzenetre válaszoló ügyféllel.
        """
        text_lower = incoming_text.lower()
        if "igen" in text_lower or "jó" in text_lower or "kérem" in text_lower or "jövő hét" in text_lower or "szerda" in text_lower:
            reply = (
                "Nagyszerű! Előjegyeztük a jövő heti karbantartást. "
                "Kovács László mesterszerelőnk felkeresi Önt a pontos óra egyeztetésére, "
                "vagy ha kényelmesebb, az alábbi linken választhat fix idősávot: "
                "http://127.0.0.1:8000/api/v1/modules/03_conversational_naptarkezeles_idopontfogl/book"
            )
            intent = "BOOKING_INTERESTED"
            lead_status = "WARM_REACTIVATED"
        elif "nem" in text_lower or "köszi nem" in text_lower or "leiratkoz" in text_lower:
            reply = "Köszönjük a visszajelzést, rögzítettük! Természetesen nem zavarjuk a szezonban. Kellemes napot kívánunk!"
            intent = "DECLINED"
            lead_status = "OPT_OUT"
        else:
            reply = "Köszönjük az üzenetet! Munkatársunk 15 percen belül személyesen visszahívja Önt a részletekkel."
            intent = "QUESTION_INQUIRY"
            lead_status = "IN_PROGRESS"

        return {
            "customer_phone": customer_phone,
            "incoming_text": incoming_text,
            "detected_intent": intent,
            "lead_status": lead_status,
            "automated_reply_text": reply
        }

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("action", "PREPARE_REACTIVATION_CAMPAIGN")

        if action == "PREPARE_REACTIVATION_CAMPAIGN":
            campaign_name = payload.get("campaign_name", "Szezonális Újraaktiváló Sprint")
            service = payload.get("target_service", "Klíma és Fűtés Karbantartás")
            days_threshold = payload.get("custom_inactivity_days", self.inactivity_threshold_days)
            clients_in = payload.get("sample_dormant_clients", [])

            # Kiszűrés
            dormant_clients = self.scan_and_segment_dormant(clients_in, days_threshold)

            # Kampány előkészítés
            campaign_data = self.prepare_campaign(campaign_name, service, dormant_clients)

            return {
                "status": "success",
                "action_executed": "REACTIVATION_CAMPAIGN_PREPARED",
                "campaign": campaign_data
            }

        elif action == "HANDLE_CUSTOMER_REPLY":
            phone = payload.get("customer_phone", "+36 30 123 4567")
            msg = payload.get("reply_message", "Igen, kérem a jövő heti karbantartást.")
            res = self.handle_two_way_reply(phone, msg)

            return {
                "status": "success",
                "action_executed": "TWO_WAY_REPLY_PROCESSED",
                "result": res
            }

        return {"status": "error", "message": f"Ismeretlen akció: {action}"}

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    handler = DormantClientReactivationHandler(config)
    return handler.execute(payload)

if __name__ == "__main__":
    test_p = {
        "action": "PREPARE_REACTIVATION_CAMPAIGN",
        "sample_dormant_clients": [
            {"name": "Kovács Béla", "last_service_date": "2025-10-15"},
            {"name": "Tóth Gábor", "last_service_date": "2026-08-01"}
        ]
    }
    res = run(test_p)
    print(json.dumps(res, indent=2, ensure_ascii=False))
