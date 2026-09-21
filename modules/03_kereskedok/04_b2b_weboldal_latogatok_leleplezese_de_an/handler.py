"""
B2B Weboldal Látogatók Leleplezése (De-Anonymization)
Modul: 04_b2b_weboldal_latogatok_leleplezese_de_an
"""

import os
import sys
import json
import datetime
from typing import Dict, Any, List, Optional

class B2BDeAnonymizationHandler:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.service_mode = self.config.get("service_mode", "mock")
        self.min_hot_score = int(self.config.get("min_hot_intent_score", 70))
        self.excluded_isps = [
            isp.lower() for isp in self.config.get("excluded_isps", [
                "magyar telekom", "telekom", "vodafone", "one hungary",
                "digi", "yettel", "invitel", "t-home", "upc"
            ])
        ]
        self.target_industries = self.config.get("target_industries", [
            "Épületgépészet", "Klímaszerelés", "Építőipar", "Kivitelezés", "Létesítményüzemeltetés"
        ])
        self.visitors_db_path = self.config.get("visitors_db_path", "data/b2b_weboldal_latogatok.json")

    def _is_residential_isp(self, isp_name: str) -> bool:
        isp_clean = (isp_name or "").lower()
        return any(ex in isp_clean for ex in self.excluded_isps)

    def _calculate_intent(self, pages: List[Dict[str, Any]], time_seconds: int, visits: int) -> Dict[str, Any]:
        score = 0
        high_intent_keywords = ["arlista", "viszontelado", "szerzodes", "nagyker", "partner", "kapcsolat"]
        catalog_keywords = ["termek", "klima", "szivattyu", "cso", "hoszivattyu", "fitting"]

        matched_high_intent = []
        for p in pages:
            url = str(p.get("url", "")).lower()
            if any(k in url for k in high_intent_keywords):
                score += 35
                matched_high_intent.append(url)
            elif any(k in url for k in catalog_keywords):
                score += 15

        # Időtartam pontozása
        if time_seconds >= 180:
            score += 20
        elif time_seconds >= 60:
            score += 10

        # Visszatérő látogatás bónusz
        if visits > 1:
            score += 20

        final_score = min(max(score, 10), 100)

        if final_score >= 75:
            tier = "BURNING_HOT"
            tier_label = "FORRÓ B2B ÉRDEKLŐDŐ (Azonnali hívás javasolt)"
        elif final_score >= 50:
            tier = "WARM"
            tier_label = "MELEG ÉRDEKLŐDŐ (Napi követés)"
        else:
            tier = "COLD_BROWSING"
            tier_label = "HIDEG BÖNGÉSZŐ"

        return {
            "score": final_score,
            "tier": tier,
            "tier_label": tier_label,
            "high_intent_pages": matched_high_intent
        }

    def _resolve_company_info(self, domain: str, hint: str) -> Dict[str, Any]:
        name = hint or ("Duna-ÉpítőGépész Kivitelező Zrt." if "duna" in domain.lower() else "TermoPartner Épületgépészet Kft.")
        dom_clean = domain or "duna-epgep.hu"

        return {
            "company_name": name,
            "tax_id": "14567890-2-41",
            "industry": "Épületgépészeti generálkivitelezés & Ipari Hűtés",
            "headcount": "35-50 fő",
            "estimated_annual_revenue": "1.4 Mrd Ft",
            "headquarters": "1117 Budapest, Budafoki út 111.",
            "domain": dom_clean,
            "website": f"https://{dom_clean}"
        }

    def _find_decision_makers(self, company_name: str, domain: str) -> List[Dict[str, Any]]:
        dom = domain or "ceg.hu"
        return [
            {
                "name": "Kovács Tamás",
                "title": "Ügyvezető Igazgató",
                "linkedin_url": f"https://www.linkedin.com/in/tamas-kovacs-{dom.split('.')[0]}",
                "email_pattern": f"t.kovacs@{dom}",
                "phone": "+36 30 111 2233"
            },
            {
                "name": "Szabó Zoltán",
                "title": "Beszerzési és Logisztikai Vezető",
                "linkedin_url": f"https://www.linkedin.com/in/zoltan-szabo-beszerzes",
                "email_pattern": f"beszerzes@{dom}",
                "phone": "+36 30 444 5566"
            },
            {
                "name": "Varga Béla",
                "title": "Főmérnök / Műszaki Igazgató",
                "linkedin_url": f"https://www.linkedin.com/in/bela-varga-fomernok",
                "email_pattern": f"muszaki@{dom}",
                "phone": "+36 30 777 8899"
            }
        ]

    def _generate_outreach_scripts(self, company: Dict[str, Any], intent: Dict[str, Any], dm: Dict[str, Any]) -> Dict[str, str]:
        company_name = company["company_name"]
        contact_name = dm["name"]

        phone_script = chr(10).join([
            f"TELEFONOS ÉRTÉKESÍTÉSI NYITÓSZÖVEG (Nem tolakodó, szakértői megkeresés):",
            f"• Hívandó: {contact_name} ({dm['title']}) - {company_name}",
            f"• Nyitás: 'Jó napot kívánok, {contact_name}! Kovács László vagyok a ProfiGépész Nagykereskedéstől.",
            f"  Azért keresem, mert a térségben dolgozó kiemelt épületgépész partnereinkkel épp a heti kapacitástervezést végezzük",
            f"  az új ipari klíma és rézcső keretszerződések kapcsán.",
            f"• Híd: 'Tudom, hogy rengeteg projektjük fut most a régióban. Adódik-e olyan beruházásuk a következő hetekben,",
            f"  ahol 22-25%-os garantált nagykereskedelmi árréssel és azonnali raktárkészlettel segíteni tudnánk Önöknek?'",
            f"• Cél: 10 perces rövid termékkatalógus és egyedi kedvezmény-egyeztetés lebeszélése."
        ])

        email_draft = chr(10).join([
            f"Tárgy: Nagykereskedelmi viszonteladói együttműködés - {company_name} & ProfiGépész",
            f"Címzett: {dm['email_pattern']}",
            "",
            f"Tisztelt {contact_name}!",
            "",
            f"Kovács László vagyok a ProfiGépész Nagykereskedelmi Kft.-től. Cégünk közvetlen gyári importőrként és nagykereskedőként "
            f"szolgálja ki a vezető hazai épületgépész kivitelezőket Daikin, Grundfos és prémium rézszerelvények területén.",
            "",
            f"Figyelemmel kísérjük a {company_name} színvonalas projektjeit, és szeretnénk felajánlani Önöknek kiemelt Arany/Platina "
            f"szerződéses partneri kedvezményszintünket, amellyel jelentős anyagköltség-megtakarítást érhetnek el a folyamatban lévő munkáiknál.",
            "",
            f"Mellékelten átküldhetjük a legfrissebb 2026-os B2B nagykereskedelmi katalógusunkat és partneri feltételeinket?",
            "",
            f"Üdvözlettel:",
            f"Kovács László | B2B Értékesítési Igazgató",
            f"ProfiGépész Nagykereskedelmi Kft. | +36 30 123 4567"
        ])

        return {
            "phone_script": phone_script,
            "email_draft": email_draft
        }

    def analyze_visitor(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        session_id = payload.get("session_id", f"SESS-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}")
        ip_address = payload.get("ip_address", "127.0.0.1")
        isp_name = payload.get("isp_name", "Corporate Leased Network")
        domain = payload.get("domain", "duna-epgep.hu")
        company_hint = payload.get("company_hint", "")
        time_on_site = int(payload.get("time_on_site_seconds", 120))
        visit_count = int(payload.get("visit_count", 1))
        pages_visited = payload.get("pages_visited", [])

        # 1. LAKOSSÁGI SZOLGÁLTATÓ SZŰRŐ
        if self._is_residential_isp(isp_name):
            return {
                "status": "SKIPPED_RESIDENTIAL_ISP",
                "session_id": session_id,
                "ip_address": ip_address,
                "isp_name": isp_name,
                "reason": f"Lakossági internetszolgáltató kiszűrve: '{isp_name}'. Nincs B2B érdeklődés (0 fals riasztás)."
            }

        # 2. INTENT PONTOZÁS
        intent = self._calculate_intent(pages_visited, time_on_site, visit_count)
        intent_score = intent["score"]

        # 3. CÉGADATOK GAZDAGÍTÁSA (ENRICHMENT)
        company = self._resolve_company_info(domain, company_hint)

        # 4. DÖNTÉSHOZÓK FELKUTATÁSA (LINKEDIN & EMAIL)
        decision_makers = self._find_decision_makers(company["company_name"], company["domain"])
        primary_dm = decision_makers[0]

        # 5. HIDEG ÉRTÉKESÍTÉSI FORGATÓKÖNYV (SCRIPTS)
        outreach_scripts = self._generate_outreach_scripts(company, intent, primary_dm)

        lead_id = f"LEAD-DEANON-{datetime.date.today().strftime('%Y%m%d')}-{abs(hash(company['company_name'])) % 9000 + 1000}"
        claim_url = f"http://localhost:8000/api/v1/modules/04_b2b_weboldal_latogatok_leleplezese_de_an/claim_lead?lead_id={lead_id}"

        is_hot = intent_score >= self.min_hot_score
        lead_status = "HOT_B2B_LEAD_DISCOVERED" if is_hot else "WARM_VISITOR_LOGGED"

        # Értékesítői mobilos riasztás
        alert_lines = [
            "[B2B WEBOLDAL LATOGATO LELEPLEZVE!]",
            f"Azonositott ceg: {company['company_name']}",
            f"Iparag: {company['industry']} | Letszam: {company['headcount']}",
            f"Becsult arbevetel: {company['estimated_annual_revenue']}",
            f"Vasarolasi szandek (Intent Score): {intent_score}/100 pont ({intent['tier']})",
            f"Eltoltott ido: {time_on_site} mp | Meglatogatott oldalak: {len(pages_visited)} db",
            f"Kiemelt oldalak: {', '.join(intent['high_intent_pages']) if intent['high_intent_pages'] else 'Katalogus'}",
            "",
            f"Kulcs donteshozo: {primary_dm['name']} ({primary_dm['title']})",
            f"LinkedIn: {primary_dm['linkedin_url']}",
            f"Email: {primary_dm['email_pattern']}",
            "",
            "1-KATTINTASOS LEAD ATVETELE A CRM-BEN:",
            f"-> {claim_url}"
        ]
        sales_alert = chr(10).join(alert_lines)

        visitor_record = {
            "lead_id": lead_id,
            "created_at": datetime.datetime.now().isoformat(),
            "session_id": session_id,
            "ip_address": ip_address,
            "isp_name": isp_name,
            "company": company,
            "intent_score": intent_score,
            "intent_tier": intent["tier"],
            "pages_count": len(pages_visited),
            "time_on_site_seconds": time_on_site,
            "visit_count": visit_count,
            "decision_makers": decision_makers,
            "status": lead_status,
            "claim_url": claim_url,
            "sales_scripts": outreach_scripts
        }

        self._save_visitor(visitor_record)

        return {
            "status": "success",
            "action_executed": "B2B_VISITOR_DE_ANONYMIZED",
            "lead_id": lead_id,
            "lead_status": lead_status,
            "is_hot_lead": is_hot,
            "intent_score": intent_score,
            "intent_tier": intent["tier"],
            "company_intelligence": company,
            "decision_makers": decision_makers,
            "sales_outreach_scripts": outreach_scripts,
            "sales_alert_message": sales_alert,
            "one_click_crm_claim_url": claim_url
        }

    def _save_visitor(self, record: Dict[str, Any]):
        os.makedirs(os.path.dirname(self.visitors_db_path), exist_ok=True)
        existing = []
        if os.path.exists(self.visitors_db_path):
            try:
                with open(self.visitors_db_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = []

        existing.insert(0, record)
        with open(self.visitors_db_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)

    def claim_lead(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        lead_id = payload.get("lead_id")
        sales_rep = payload.get("sales_rep", "Értékesítő Munkatárs")
        if not lead_id:
            return {"status": "error", "message": "lead_id kotelezo az atvetelhez!"}

        if os.path.exists(self.visitors_db_path):
            try:
                with open(self.visitors_db_path, "r", encoding="utf-8") as f:
                    records = json.load(f)
                for rec in records:
                    if rec.get("lead_id") == lead_id:
                        rec["status"] = "CLAIMED_IN_CRM"
                        rec["assigned_sales_rep"] = sales_rep
                        rec["claimed_at"] = datetime.datetime.now().isoformat()
                        with open(self.visitors_db_path, "w", encoding="utf-8") as fw:
                            json.dump(records, fw, indent=2, ensure_ascii=False)
                        return {
                            "status": "success",
                            "lead_id": lead_id,
                            "new_status": "CLAIMED_IN_CRM",
                            "assigned_sales_rep": sales_rep,
                            "message": f"A(z) {lead_id} forró lead sikeresen rögzítve a CRM-ben ({sales_rep} felelőssel)!"
                        }
            except Exception as e:
                return {"status": "error", "message": str(e)}

        return {"status": "error", "message": f"A(z) {lead_id} lead nem található."}

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("action", "DE_ANONYMIZE_VISITOR")
        if action == "CLAIM_LEAD":
            return self.claim_lead(payload)
        return self.analyze_visitor(payload)

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    handler = B2BDeAnonymizationHandler(config)
    return handler.execute(payload)

if __name__ == "__main__":
    sample = {
        "action": "DE_ANONYMIZE_VISITOR",
        "ip_address": "194.149.24.88",
        "isp_name": "Corporate Leased Network",
        "domain": "duna-epgep.hu",
        "company_hint": "Duna-ÉpítőGépész Zrt.",
        "time_on_site_seconds": 200,
        "visit_count": 2,
        "pages_visited": [{"url": "/nagyker-arlista"}]
    }
    res = run(sample)
    print(json.dumps(res, indent=2, ensure_ascii=False))
