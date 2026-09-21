"""
B2B Hideg Lead-Kutatás & Hiper-perszonalizált Megkeresés
Modul: 05_b2b_hideg_lead_kutatas_hiper_perszonaliz
"""

import os
import sys
import json
import datetime
from typing import Dict, Any, List, Optional

class B2BColdLeadOutreachHandler:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.service_mode = self.config.get("service_mode", "mock")
        self.company_name = self.config.get("company_name", "ProfiGépész Nagykereskedelmi Kft.")
        self.sender_name = self.config.get("sender_name", "Kovács László")
        self.sender_title = self.config.get("sender_title", "B2B Értékesítési Igazgató")
        self.sender_email = self.config.get("sender_email", "laszlo.kovacs@profigepesz.hu")
        self.calendar_url = self.config.get("calendar_booking_url", "https://profigepesz.hu/talalkozo-egyeztetes")
        self.sending_mode = self.config.get("sending_mode", "manual_approval_only")
        self.daily_drip_limit = int(self.config.get("daily_drip_limit", 25))
        self.auto_stop_on_reply = self.config.get("auto_stop_on_reply", True)
        self.leads_db_path = self.config.get("leads_db_path", "data/b2b_hideg_leadek_naplo.json")

    def _generate_personalized_sequence(self, prospect: Dict[str, Any]) -> List[Dict[str, Any]]:
        company = prospect.get("company_name", "Vállalkozás")
        dm_name = prospect.get("decision_maker_name", "Tisztelt Cégvezető")
        first_name = dm_name.split()[0] if dm_name else "Partnerünk"
        ref = prospect.get("recent_project_reference", "az igényes épületgépészeti kivitelezéseiket")
        specialty = prospect.get("specialty", "épületgépészet és hűtés-fűtés")

        # 1. LÉPÉS: Értékfókuszú személyre szabott jégtörő (Day 0)
        step_1_lines = [
            f"Kedves {first_name}!",
            "",
            f"Láttuk a(z) {company} legutóbbi szakmai munkáit, különösen {ref} - "
            f"ezúton is gratulálunk a precíz mérnöki megvalósításhoz!",
            "",
            f"A ProfiGépész Nagykereskedelem közvetlen importőrként pontosan olyan specialistákat lát el, "
            f"mint Önök ({specialty}). Tudjuk, hogy a feszes határidők és a növekvő alapanyagárak mellett "
            f"a megbízható szállítás és a tiszta árrés a legfontosabb.",
            "",
            f"Szeretnénk felajánlani a(z) {company} részére kiemelt Arany partneri keretszerződésünket "
            f"(-22% azonnali árréskedvezmény Daikin, Grundfos, Wilo és rézszerelvényekre), "
            f"15 000 m2-es központi raktárunkból 24 órás garantált helyszíni kiszállítással.",
            "",
            f"Nyitott lenne egy kötetlen, 10 perces telefonos egyeztetésre a jövő heti anyagszükségleteik kapcsán?",
            f"Közvetlen naptáram itt érhető el: {self.calendar_url}",
            "",
            "Üdvözlettel:",
            f"{self.sender_name} | {self.sender_title}",
            f"{self.company_name} | {self.sender_email}"
        ]
        step_1_body = chr(10).join(step_1_lines)

        # 2. LÉPÉS: Esettanulmány és kockázatcsökkentés (Day 4)
        step_2_lines = [
            f"Kedves {first_name}!",
            "",
            f"Egy rövid gondolat az előző megkeresésemhez kapcsolódóan:",
            f"A múlt hónapban egy hasonló méretű budapesti gépész kivitelező partnerünk azért igazolt át hozzánk, "
            f"mert a korábbi beszállítójuknál heteket csúsztak az idomok és szelepek, ami kötbérveszélyt okozott.",
            "",
            f"Nálunk 99,4%-os készletpontossággal működik a raktári kiszolgálás, így a szerelőbrigádoknak "
            f"egyetlen órát sem kell feleslegesen a telephelyen várakozniuk.",
            "",
            f"Szívesen elküldjük a legfrissebb 2026-os nagykereskedelmi katalógusunkat és egy díjmentes prémium mintacsomagot!",
            f"Megfelelő lenne egy gyors hívás ezen a héten? -> {self.calendar_url}",
            "",
            "Baráti üdvözlettel:",
            f"{self.sender_name}"
        ]
        step_2_body = chr(10).join(step_2_lines)

        # 3. LÉPÉS: Elegáns lezárás / Breakup email (Day 8)
        step_3_lines = [
            f"Kedves {first_name}!",
            "",
            f"Gondolom most a folyamatban lévő kivitelezési projektek kötik le minden figyelmét, "
            f"így nem szeretném feleslegesen rabolni az idejét.",
            "",
            f"Amennyiben a jövőben mégis szükségük lenne azonnali, megbízható nagykereskedelmi raktárkészletre "
            f"vagy sürgős anyagpótlásra kiemelt kedvezménnyel, közvetlenül elér a mobilomon is: +36 30 123 4567.",
            "",
            f"Sikeres évzárást és jó egészséget kívánok a(z) {company} teljes csapatának!",
            "",
            "Üdvözlettel:",
            f"{self.sender_name} | {self.company_name}"
        ]
        step_3_body = chr(10).join(step_3_lines)

        return [
            {
                "step_number": 1,
                "delay_days": 0,
                "subject": f"Nagykereskedelmi partnerség & raktári árrés - {company}",
                "body": step_1_body,
                "status": "QUEUED"
            },
            {
                "step_number": 2,
                "delay_days": 4,
                "subject": f"Re: Nagykereskedelmi partnerség & raktári árrés - {company}",
                "body": step_2_body,
                "status": "SCHEDULED"
            },
            {
                "step_number": 3,
                "delay_days": 8,
                "subject": f"Utolsó kérdés a gépészeti kapacitásról ({company})",
                "body": step_3_body,
                "status": "SCHEDULED"
            }
        ]

    def create_campaign(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prospects_data = payload.get("prospects", [])
        search_criteria = payload.get("search_criteria", {
            "industries": ["Épületgépészet", "Klímaszerelés"],
            "region": "Országos"
        })

        today = datetime.date.today()
        campaign_id = f"CAMP-B2B-{today.strftime('%Y%m%d')}-{abs(hash(str(prospects_data))) % 9000 + 1000}"

        campaign_prospects = []
        for p in prospects_data:
            sequence = self._generate_personalized_sequence(p)
            campaign_prospects.append({
                "prospect_id": f"P-{abs(hash(p.get('email', p.get('company_name')))) % 90000 + 10000}",
                "company_name": p.get("company_name"),
                "tax_id": p.get("tax_id", "N/A"),
                "decision_maker_name": p.get("decision_maker_name"),
                "decision_maker_title": p.get("decision_maker_title"),
                "email": p.get("email"),
                "sequence": sequence,
                "status": "READY_FOR_DISPATCH",
                "replied": False
            })

        approval_url = f"http://localhost:8000/api/v1/modules/05_b2b_hideg_lead_kutatas_hiper_perszonaliz/approve_campaign?campaign_id={campaign_id}"

        if self.sending_mode == "automated_drip":
            status = "DRIP_CAMPAIGN_ACTIVE"
            action_summary = f"B opció aktív: Drip küldés elindítva (Napi {self.daily_drip_limit} levél / domain védelem)."
        else:
            status = "PENDING_SALES_MANAGER_APPROVAL"
            action_summary = "A opció aktív: Értékesítési vezetői jóváhagyásra vár (1-kattintásos indító gomb)."

        # Értékesítői vezetői riasztás
        alert_lines = [
            "[B2B HIDEG LEAD KAMPÁNY ELŐKÉSZÍTVE]",
            f"Kampany azonosito: {campaign_id}",
            f"Kutatott cegek szama: {len(campaign_prospects)} db",
            f"Celiparag: {', '.join(search_criteria.get('industries', []))}",
            f"Szekvencia: 3-lepcsos hiper-perszonalizalt email sorozat (0., 4., 8. nap)",
            f"Statusz: {status}",
            "",
            "1-KATTINTASOS JOVAHAGYAS ES INDITAS:",
            f"-> {approval_url}"
        ]
        executive_alert = chr(10).join(alert_lines)

        campaign_record = {
            "campaign_id": campaign_id,
            "created_at": datetime.datetime.now().isoformat(),
            "status": status,
            "search_criteria": search_criteria,
            "total_prospects": len(campaign_prospects),
            "sending_mode": self.sending_mode,
            "daily_drip_limit": self.daily_drip_limit,
            "prospects": campaign_prospects,
            "approval_url": approval_url
        }

        self._save_campaign(campaign_record)

        return {
            "status": "success",
            "action_executed": "COLD_OUTREACH_CAMPAIGN_GENERATED",
            "campaign_id": campaign_id,
            "campaign_status": status,
            "sending_mode": self.sending_mode,
            "total_prospects": len(campaign_prospects),
            "prospects": campaign_prospects,
            "one_click_approval_url": approval_url,
            "action_summary": action_summary,
            "executive_alert_message": executive_alert
        }

    def _save_campaign(self, record: Dict[str, Any]):
        os.makedirs(os.path.dirname(self.leads_db_path), exist_ok=True)
        existing = []
        if os.path.exists(self.leads_db_path):
            try:
                with open(self.leads_db_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = []

        existing.insert(0, record)
        with open(self.leads_db_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)

    def approve_campaign(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        campaign_id = payload.get("campaign_id")
        if not campaign_id:
            return {"status": "error", "message": "campaign_id kotelezo!"}

        if os.path.exists(self.leads_db_path):
            try:
                with open(self.leads_db_path, "r", encoding="utf-8") as f:
                    records = json.load(f)
                for rec in records:
                    if rec.get("campaign_id") == campaign_id:
                        rec["status"] = "APPROVED_AND_RUNNING"
                        rec["approved_at"] = datetime.datetime.now().isoformat()
                        with open(self.leads_db_path, "w", encoding="utf-8") as fw:
                            json.dump(records, fw, indent=2, ensure_ascii=False)
                        return {
                            "status": "success",
                            "campaign_id": campaign_id,
                            "new_status": "APPROVED_AND_RUNNING",
                            "message": f"A(z) {campaign_id} B2B hideg megkereso kampany jovahagyva es elinditva!"
                        }
            except Exception as e:
                return {"status": "error", "message": str(e)}

        return {"status": "error", "message": f"A(z) {campaign_id} kampány nem található."}

    def record_reply(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        campaign_id = payload.get("campaign_id")
        prospect_email = payload.get("prospect_email")
        if not campaign_id or not prospect_email:
            return {"status": "error", "message": "campaign_id és prospect_email kötelező!"}

        if os.path.exists(self.leads_db_path):
            try:
                with open(self.leads_db_path, "r", encoding="utf-8") as f:
                    records = json.load(f)
                for rec in records:
                    if rec.get("campaign_id") == campaign_id:
                        for p in rec.get("prospects", []):
                            if p.get("email") == prospect_email:
                                p["replied"] = True
                                p["status"] = "REPLY_RECEIVED_SEQUENCE_STOPPED"
                                # Töröljük vagy állítsuk le a további leveleket
                                for step in p.get("sequence", []):
                                    if step.get("status") == "SCHEDULED":
                                        step["status"] = "CANCELLED_DUE_TO_REPLY"
                                with open(self.leads_db_path, "w", encoding="utf-8") as fw:
                                    json.dump(records, fw, indent=2, ensure_ascii=False)
                                return {
                                    "status": "success",
                                    "campaign_id": campaign_id,
                                    "prospect_email": prospect_email,
                                    "action": "SEQUENCE_STOPPED",
                                    "message": f"Valasz erkezett ({prospect_email}), a tovabbi automata emailek sikeresen leallitva!"
                                }
            except Exception as e:
                return {"status": "error", "message": str(e)}

        return {"status": "error", "message": "Kampány vagy prospect nem található."}

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("action", "PROSPECT_AND_GENERATE_CAMPAIGN")
        if action == "APPROVE_CAMPAIGN":
            return self.approve_campaign(payload)
        elif action == "RECORD_REPLY":
            return self.record_reply(payload)
        return self.create_campaign(payload)

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    handler = B2BColdLeadOutreachHandler(config)
    return handler.execute(payload)

if __name__ == "__main__":
    sample = {
        "prospects": [{
            "company_name": "Teszt Épületgépész Kft.",
            "decision_maker_name": "Teszt János",
            "email": "janos@tesztgepesz.hu",
            "recent_project_reference": "új irodaház hűtése"
        }]
    }
    res = run(sample)
    print(json.dumps(res, indent=2, ensure_ascii=False))
