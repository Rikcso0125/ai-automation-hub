"""
AI Lead Scoring – A Forró Viszonteladó-Jelöltek Kiszűrése
Modul: 06_ai_lead_scoring_a_forro_viszontelado_jel
"""

import os
import sys
import json
import datetime
from typing import Dict, Any, List, Optional

class B2BLeadScoringHandler:
    """
    Autonóm B2B AI Lead Scoring és Prioritási Rendszer.
    Kiértékeli a beérkező partnereket pénzügyi, iparági és beszerzési szempontok alapján,
    majd Tier A / B / C kategóriába rendezi és értékesítőhöz továbbítja őket.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.service_mode = self.config.get("service_mode", "mock")
        self.routing_mode = self.config.get("routing_mode", "specialized_sales_routing")
        
        # Tier határértékek
        thresholds = self.config.get("tier_thresholds", {})
        self.tier_a_min = int(thresholds.get("tier_a_min_score", 80))
        self.tier_b_min = int(thresholds.get("tier_b_min_score", 50))
        
        # Egyedi szabályok
        self.custom_rules = self.config.get("custom_rules", [
            {
                "field": "has_iso_cert",
                "operator": "is_true",
                "points": 5,
                "description": "ISO minősítés bónusz"
            },
            {
                "field": "has_negative_credit_event",
                "operator": "is_true",
                "points": -25,
                "description": "Negatív hitelesemény / végrehajtás büntetés"
            },
            {
                "field": "is_returning_customer",
                "operator": "is_true",
                "points": 10,
                "description": "Korábbi pozitív vásárlói múlt bónusz"
            }
        ])
        
        # KAM területi felelősök
        self.kam_assignments = self.config.get("kam_assignments", {
            "Közép-Magyarország": "Kovács László (B2B Értékesítési Igazgató)",
            "Nyugat-Magyarország": "Nagy Péter (Senior KAM Nyugat)",
            "Kelet-Magyarország": "Szabó Gábor (Senior KAM Kelet)",
            "default": "Központi B2B Értékesítési Csapat"
        })
        
        self.storage_path = self.config.get("storage_path", "data/b2b_lead_scoring_naplo.json")

    def _score_financial_and_scale(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """1. Dimenzió: Pénzügyi Stabilitás és Cégméret (max 35 pont)"""
        points = 0
        breakdown = {}
        
        # Munkavállalói létszám (max 10 pont)
        headcount = int(lead.get("headcount", 1))
        if headcount >= 20:
            hc_pts = 10
        elif headcount >= 10:
            hc_pts = 7
        elif headcount >= 5:
            hc_pts = 5
        elif headcount >= 2:
            hc_pts = 3
        else:
            hc_pts = 1
        points += hc_pts
        breakdown["headcount_points"] = {"value": headcount, "points": hc_pts, "max": 10}
        
        # Éves árbevétel (max 12 pont)
        revenue = float(lead.get("annual_revenue_huf", 0))
        if revenue >= 500000000:
            rev_pts = 12
        elif revenue >= 200000000:
            rev_pts = 9
        elif revenue >= 50000000:
            rev_pts = 5
        elif revenue >= 15000000:
            rev_pts = 2
        else:
            rev_pts = 0
        points += rev_pts
        breakdown["revenue_points"] = {"value": revenue, "points": rev_pts, "max": 12}
        
        # Saját tőke & eredmény (max 6 pont)
        positive_equity = bool(lead.get("positive_equity", True))
        if positive_equity:
            equity_pts = 6
        else:
            equity_pts = -5  # Tőkeproblémás cég kockázat
        points += equity_pts
        breakdown["equity_points"] = {"positive_equity": positive_equity, "points": equity_pts, "max": 6}
        
        # NAV Köztartozásmentes státusz & Hitelkockázat (max 7 pont)
        nav_free = bool(lead.get("nav_tax_debt_free", True))
        neg_credit = bool(lead.get("has_negative_credit_event", False))
        if nav_free and not neg_credit:
            nav_pts = 7
        elif not nav_free and not neg_credit:
            nav_pts = -5
        else:
            nav_pts = -15
        points += nav_pts
        breakdown["compliance_points"] = {"nav_free": nav_free, "negative_credit": neg_credit, "points": nav_pts, "max": 7}
        
        final_pts = max(0, min(35, points))
        return {
            "score": final_pts,
            "max_possible": 35,
            "breakdown": breakdown
        }

    def _score_industry_and_icp(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """2. Dimenzió: Iparági és ICP Illeszkedés (max 35 pont)"""
        points = 0
        breakdown = {}
        
        # Szakterület & Főtevékenység (max 20 pont)
        industry = str(lead.get("industry", "")).lower()
        primary_keywords = ["hvac", "épületgépész", "gepesz", "fűtés", "hűtés", "klíma", "csőszerel", "villany", "kivitelez", "fővállalkoz"]
        secondary_keywords = ["nagyker", "keresked", "barkács", "szerelvénybolt", "szaküzlet"]
        retail_keywords = ["lakosság", "magánszemély", "egyéni vásárló", "bérlő"]
        
        if any(kw in industry for kw in retail_keywords):
            ind_pts = 0
            ind_match = "Retail / Lakossági kizárás"
        elif any(kw in industry for kw in primary_keywords):
            ind_pts = 20
            ind_match = "Elsődleges B2B Célcsoport (Gépész / Kivitelező)"
        elif any(kw in industry for kw in secondary_keywords):
            ind_pts = 14
            ind_match = "Másodlagos B2B Célcsoport (Viszonteladó / Kereskedés)"
        else:
            ind_pts = 6
            ind_match = "Egyéb iparági szereplő"
        points += ind_pts
        breakdown["industry_match"] = {"industry": lead.get("industry", ""), "classification": ind_match, "points": ind_pts, "max": 20}
        
        # Működési idő / cégkor (max 8 pont)
        years = int(lead.get("years_in_business", 1))
        if years >= 5:
            yr_pts = 8
        elif years >= 2:
            yr_pts = 5
        else:
            yr_pts = 2
        points += yr_pts
        breakdown["experience_points"] = {"years_in_business": years, "points": yr_pts, "max": 8}
        
        # Transzparens digitális jelenlét / weboldal (max 7 pont)
        has_web = bool(lead.get("has_active_website", False))
        web_pts = 7 if has_web else 2
        points += web_pts
        breakdown["digital_presence"] = {"has_active_website": has_web, "points": web_pts, "max": 7}
        
        final_pts = max(0, min(35, points))
        return {
            "score": final_pts,
            "max_possible": 35,
            "breakdown": breakdown
        }

    def _score_volume_and_urgency(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """3. Dimenzió: Vásárlási Potenciál és Sürgősség (max 30 pont)"""
        points = 0
        breakdown = {}
        
        # Várható havi forgalom (max 15 pont)
        vol = float(lead.get("estimated_monthly_volume_huf", 0))
        if vol >= 3000000:
            vol_pts = 15
        elif vol >= 1000000:
            vol_pts = 10
        elif vol >= 300000:
            vol_pts = 5
        else:
            vol_pts = 2
        points += vol_pts
        breakdown["volume_points"] = {"monthly_volume_huf": vol, "points": vol_pts, "max": 15}
        
        # Projekt sürgősség (max 10 pont)
        urgency = str(lead.get("project_urgency", "")).lower()
        if "azonnali" in urgency or "1_het" in urgency or "surgos" in urgency:
            urg_pts = 10
            urg_desc = "Azonnali / 1 héten belüli megrendelés"
        elif "honap" in urgency or "kozepes" in urgency:
            urg_pts = 6
            urg_desc = "1 hónapon belüli projektigény"
        else:
            urg_pts = 2
            urg_desc = "Általános tájékozódás / jövőbeli terv"
        points += urg_pts
        breakdown["urgency_points"] = {"urgency": lead.get("project_urgency", ""), "classification": urg_desc, "points": urg_pts, "max": 10}
        
        # Konkrét tételes igény (max 5 pont)
        details = str(lead.get("requested_quote_details", "")).strip()
        if len(details) >= 20:
            req_pts = 5
            req_desc = "Részletes, konkrét terméklista megadva"
        elif len(details) > 0:
            req_pts = 3
            req_desc = "Általános termékkör megjelölve"
        else:
            req_pts = 1
            req_desc = "Nincs specifikus igény"
        points += req_pts
        breakdown["quote_readiness"] = {"details": details, "classification": req_desc, "points": req_pts, "max": 5}
        
        final_pts = max(0, min(30, points))
        return {
            "score": final_pts,
            "max_possible": 30,
            "breakdown": breakdown
        }

    def _evaluate_custom_rules(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """Egyedi testreszabható szabályok (Bonus / Malus) kiértékelése"""
        bonus_malus = 0
        triggered_rules = []
        
        for rule in self.custom_rules:
            field = rule.get("field")
            op = rule.get("operator", "is_true")
            pts = int(rule.get("points", 0))
            desc = rule.get("description", field)
            
            val = lead.get(field)
            is_match = False
            
            if op == "is_true" and bool(val) is True:
                is_match = True
            elif op == "equals" and str(val).lower() == str(rule.get("value", "")).lower():
                is_match = True
            elif op == "contains" and str(rule.get("value", "")).lower() in str(val).lower():
                is_match = True
            elif op == "greater_than":
                try:
                    if float(val) > float(rule.get("value", 0)):
                        is_match = True
                except (TypeError, ValueError):
                    is_match = False
            
            if is_match:
                bonus_malus += pts
                triggered_rules.append({
                    "rule": desc,
                    "field": field,
                    "points": pts
                })
        
        return {
            "total_adjustment": bonus_malus,
            "triggered_rules": triggered_rules
        }

    def _assign_tier_and_strategy(self, total_score: int, lead: Dict[str, Any]) -> Dict[str, Any]:
        """Partnerminősítés (Tier A, B, C) és értékesítési stratégia generálás"""
        now = datetime.datetime.now()
        company = lead.get("company_name", "Partner")
        contact = lead.get("contact_person", "Ügyvezető")
        phone = lead.get("contact_phone", "")
        email = lead.get("contact_email", "")
        vol = float(lead.get("estimated_monthly_volume_huf", 0))
        
        if total_score >= self.tier_a_min:
            tier = "TIER_A"
            tier_label = "Tier A (Hot Key Account / Kiemelt Forró Jelölt)"
            priority = "URGENT_HIGH"
            sla_minutes = 15
            deadline = (now + datetime.timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
            discount_package = "Arany (-22%) / Platina (-28%) keretszerződés, 30 napos átutalási hitelkeret elbírálás"
            action_title = "Azonnali Senior KAM telefonos megkeresés és VIP tárgyalási meghívó"
            
            sales_pitch = (
                f"Tisztelt {contact}! Észrevettük a(z) {company} kiemelt nagyságrendű igényét ({vol:,.0f} Ft/hó potenciál). "
                f"Cégünk mint közvetlen vezérképviselet személyre szabott Arany partneri kondíciókat (-22% azonnali árrés) "
                f"és garantált 24 órás projekt-kiszállítást biztosít az Önök számára. Kérem, egyeztessünk egy 10 perces telefonos auditot!"
            )
            action_steps = [
                f"1. Visszahívás indítása 15 percen belül ({deadline}-ig) a(z) {phone} telefonszámon.",
                "2. Arany keretszerződés tervezet összeállítása a terméktörzsből.",
                "3. Személyes raktárlátogatási időpont felajánlása."
            ]
        elif total_score >= self.tier_b_min:
            tier = "TIER_B"
            tier_label = "Tier B (Normál B2B Partner / Mid-Market)"
            priority = "NORMAL_B2B"
            sla_minutes = 1440  # 24 óra
            deadline = (now + datetime.timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
            discount_package = "Bronz (-10%) / Ezüst (-15%) standard nagykereskedelmi partnercsomag"
            action_title = "Digitális B2B önkiszolgáló onboarding és nagyker árlista küldése"
            
            sales_pitch = (
                f"Kedves {contact}! Köszönjük a(z) {company} megkeresését. Elkészítettük a B2B partnerfiókját, "
                f"ahol azonnal elérheti a szakipari viszonteladói árakat és leadhatja próbarendelését online webshopunkban."
            )
            action_steps = [
                f"1. Automatikus regisztrációs link és katalógus kiküldése az emailre ({email}).",
                "2. 48 órán belüli utánkövetés, ha nem aktiválja a partnerfiókot."
            ]
        else:
            tier = "TIER_C"
            tier_label = "Tier C (Retail / Kis Volumenű Lakossági Érdeklődő)"
            priority = "LOW_AUTOMATED_FILTER"
            sla_minutes = 0
            deadline = "Azonnali automatizált válasz"
            discount_package = "0% (Listaár / Lakossági kiskereskedelem)"
            action_title = "Udvarias automatikus elirányítás lakossági webáruházhoz vagy partnerboltokhoz"
            
            sales_pitch = (
                f"Tisztelt {contact}! Köszönjük érdeklődését! Cégünk nagykereskedelmi központként működik, "
                f"azonban kis tételes igényét készséggel kiszolgálják hivatalos lakossági viszonteladó partnereink és webáruházunk: https://bolt.profigepesz.hu"
            )
            action_steps = [
                "1. Értékesítői beavatkozás nem szükséges (0 perc sales time).",
                "2. Automatikus lakossági terelő email elküldve partnerbolt-keresővel."
            ]
        
        return {
            "tier": tier,
            "tier_label": tier_label,
            "priority": priority,
            "sla_minutes": sla_minutes,
            "sla_deadline": deadline,
            "discount_package": discount_package,
            "action_title": action_title,
            "sales_pitch": sales_pitch,
            "action_steps": action_steps
        }

    def _route_lead(self, tier_info: Dict[str, Any], lead: Dict[str, Any]) -> Dict[str, Any]:
        """Lead értékesítői kiosztása (Mód A: Területi KAM, Mód B: CRM Pool)"""
        region = lead.get("region", "Közép-Magyarország")
        assigned_kam = self.kam_assignments.get(region, self.kam_assignments.get("default", "Központi KAM Csapat"))
        phone = lead.get("contact_phone", "")
        clean_phone = "".join([c for c in phone if c.isdigit() or c == "+"])
        
        one_click_dial = f"tel:{clean_phone}" if clean_phone else None
        phone_digits = clean_phone.replace("+", "") if clean_phone else ""
        one_click_whatsapp = f"https://wa.me/{phone_digits}" if phone_digits else None
        
        if self.routing_mode == "specialized_sales_routing":
            # Mód A: Dedikált területi Key Account Manager
            routing_details = {
                "routing_mode": "specialized_sales_routing (Mód A)",
                "assigned_to": assigned_kam,
                "region": region,
                "notification_dispatched": True,
                "notification_channel": "Instant Senior KAM Alert (Telegram & Dashboard)",
                "one_click_dial": one_click_dial,
                "one_click_whatsapp": one_click_whatsapp,
                "routing_status": "ASSIGNED_TO_REGIONAL_KAM"
            }
        else:
            # Mód B: Központi CRM Lead Pool pontszám szerinti prioritással
            routing_details = {
                "routing_mode": "central_crm_pool (Mód B)",
                "assigned_to": "Központi B2B Lead Várólista",
                "pool_priority_rank": "P1" if tier_info["tier"] == "TIER_A" else ("P2" if tier_info["tier"] == "TIER_B" else "P3"),
                "notification_dispatched": True,
                "notification_channel": "CRM Pool Queue Broadcast",
                "one_click_dial": one_click_dial,
                "one_click_whatsapp": one_click_whatsapp,
                "routing_status": "QUEUED_IN_CRM_POOL"
            }
            
        return routing_details

    def score_single_lead(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """Egyetlen lead komplett multi-faktoros pontozása és kiértékelése"""
        now_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        lead_id = lead.get("lead_id") or f"LEAD-{now_str}"
        company_name = lead.get("company_name", "Ismeretlen Cég")
        
        # Dimenziók pontozása
        dim1 = self._score_financial_and_scale(lead)
        dim2 = self._score_industry_and_icp(lead)
        dim3 = self._score_volume_and_urgency(lead)
        custom = self._evaluate_custom_rules(lead)
        
        raw_score = dim1["score"] + dim2["score"] + dim3["score"] + custom["total_adjustment"]
        final_score = max(0, min(100, raw_score))
        
        # Minősítés és stratégia
        strategy = self._assign_tier_and_strategy(final_score, lead)
        routing = self._route_lead(strategy, lead)
        
        scored_record = {
            "lead_id": lead_id,
            "company_name": company_name,
            "tax_number": lead.get("tax_number", "N/A"),
            "contact_person": lead.get("contact_person", "N/A"),
            "contact_email": lead.get("contact_email", "N/A"),
            "contact_phone": lead.get("contact_phone", "N/A"),
            "evaluated_at": datetime.datetime.now().isoformat(),
            "final_lead_score": final_score,
            "tier": strategy["tier"],
            "tier_label": strategy["tier_label"],
            "priority": strategy["priority"],
            "dimension_scores": {
                "financial_and_scale": dim1,
                "industry_and_icp": dim2,
                "volume_and_urgency": dim3,
                "custom_rules_adjustment": custom
            },
            "sales_strategy": {
                "sla_minutes": strategy["sla_minutes"],
                "sla_deadline": strategy["sla_deadline"],
                "discount_package": strategy["discount_package"],
                "action_title": strategy["action_title"],
                "sales_pitch": strategy["sales_pitch"],
                "action_steps": strategy["action_steps"]
            },
            "routing": routing,
            "audit_trail": {
                "scored_by": "06_ai_lead_scoring_a_forro_viszontelado_jel",
                "service_mode": self.service_mode,
                "status": "PROCESSED"
            }
        }
        return scored_record

    def _persist_records(self, new_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Eredmények tartós mentése és statisztikák frissítése a naplóban"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        existing_records = []
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        existing_records = data
                    elif isinstance(data, dict) and "records" in data:
                        existing_records = data.get("records", [])
            except Exception:
                existing_records = []
        
        # Frissítés vagy hozzáfűzés
        existing_ids = {r.get("lead_id"): idx for idx, r in enumerate(existing_records)}
        for nr in new_records:
            lid = nr.get("lead_id")
            if lid in existing_ids:
                existing_records[existing_ids[lid]] = nr
            else:
                existing_records.append(nr)
                existing_ids[lid] = len(existing_records) - 1
        
        # Statisztikák számítása
        tier_a_count = sum(1 for r in existing_records if r.get("tier") == "TIER_A")
        tier_b_count = sum(1 for r in existing_records if r.get("tier") == "TIER_B")
        tier_c_count = sum(1 for r in existing_records if r.get("tier") == "TIER_C")
        avg_score = round(sum(r.get("final_lead_score", 0) for r in existing_records) / max(1, len(existing_records)), 1)
        
        persisted_data = {
            "last_updated": datetime.datetime.now().isoformat(),
            "total_scored_leads": len(existing_records),
            "summary_metrics": {
                "tier_a_hot_leads": tier_a_count,
                "tier_b_mid_market": tier_b_count,
                "tier_c_filtered_out": tier_c_count,
                "average_lead_score": avg_score
            },
            "records": existing_records
        }
        
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(persisted_data, f, indent=2, ensure_ascii=False)
            
        return persisted_data["summary_metrics"]

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fő végrehajtási belépési pont"""
        action = payload.get("action", "SCORE_LEADS")
        
        # Egyedi vagy tömeges lead bemenet kezelése
        leads_to_score = []
        if "leads" in payload and isinstance(payload["leads"], list):
            leads_to_score = payload["leads"]
        elif "lead" in payload and isinstance(payload["lead"], dict):
            leads_to_score = [payload["lead"]]
        elif "sample_data" in payload and isinstance(payload["sample_data"], dict):
            leads_to_score = [payload["sample_data"]]
        else:
            # Ha a payload maga egy lead
            leads_to_score = [payload]
            
        scored_results = []
        for lead in leads_to_score:
            scored_results.append(self.score_single_lead(lead))
            
        # Eredmények rendezése prioritás szerint (magas pontszám elöl)
        scored_results.sort(key=lambda x: x.get("final_lead_score", 0), reverse=True)
        
        # Tartós naplózás
        summary = self._persist_records(scored_results)
        
        tier_a_leads = [r for r in scored_results if r.get("tier") == "TIER_A"]
        
        return {
            "status": "success",
            "module_id": "06_ai_lead_scoring_a_forro_viszontelado_jel",
            "processed_at": datetime.datetime.now().isoformat(),
            "scoring_engine": "B2B Multi-Factor AI Scoring Engine v1.0",
            "leads_processed_count": len(scored_results),
            "summary_metrics": summary,
            "hot_leads_tier_a_count": len(tier_a_leads),
            "hot_leads_immediate_actions": [
                {
                    "lead_id": hl["lead_id"],
                    "company_name": hl["company_name"],
                    "score": hl["final_lead_score"],
                    "assigned_kam": hl["routing"]["assigned_to"],
                    "sla_deadline": hl["sales_strategy"]["sla_deadline"],
                    "one_click_dial": hl["routing"]["one_click_dial"]
                }
                for hl in tier_a_leads
            ],
            "scored_leads": scored_results
        }

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Szabványos hub belépési pont"""
    handler = B2BLeadScoringHandler(config)
    return handler.execute(payload)

if __name__ == "__main__":
    test_sample = {
        "leads": [
            {
                "lead_id": "TEST-01",
                "company_name": "Teszt Klíma Kft.",
                "industry": "HVAC épületgépészet",
                "headcount": 25,
                "annual_revenue_huf": 600000000,
                "positive_equity": True,
                "nav_tax_debt_free": True,
                "years_in_business": 6,
                "has_active_website": True,
                "estimated_monthly_volume_huf": 3500000,
                "project_urgency": "azonnali_1_het",
                "requested_quote_details": "Ipari Daikin szivattyúk"
            }
        ]
    }
    res = run(test_sample)
    print(json.dumps(res, indent=2, ensure_ascii=False))
