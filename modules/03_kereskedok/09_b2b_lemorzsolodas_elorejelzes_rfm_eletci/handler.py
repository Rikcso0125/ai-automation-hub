"""
B2B Lemorzsolódás Előrejelzés & RFM Életciklus Figyelő
Modul: 09_b2b_lemorzsolodas_elorejelzes_rfm_eletci
"""

import os
import sys
import json
import datetime
from typing import Dict, Any, List, Optional

class B2BChurnPredictionHandler:
    """
    Prediktív B2B Lemorzsolódás-megelőző és RFM Elemző Motor.
    Kiszámítja az egyéni vásárlási ciklusidőt, a költés visszaesést,
    detektálja a konkurenciához való átpártolást, és automatikus VIP visszatartó ajánlatot generál.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.service_mode = self.config.get("service_mode", "mock")
        
        # Kockázati küszöbértékek
        sens = self.config.get("churn_sensitivity", {})
        self.cycle_delay_threshold = float(sens.get("cycle_delay_multiplier_threshold", 1.5))
        self.revenue_drop_threshold = float(sens.get("revenue_drop_percent_threshold", 40.0))
        
        self.retention_mode = self.config.get("retention_strategy_mode", "tier_adaptive")
        self.vip_extra_discount = float(self.config.get("vip_retention_extra_discount_percent", 5.0))
        self.escalation_mode = self.config.get("escalation_mode", "hybrid_dual_channel")
        self.partners_db_path = self.config.get("partners_db_path", "data/b2b_partnerek.json")
        self.churn_log_path = self.config.get("churn_log_path", "data/b2b_lemorzsolodas_naplo.json")

    def _analyze_partner(self, partner: Dict[str, Any], ref_date_str: str) -> Dict[str, Any]:
        """Egyetlen partner komplett RFM és lemorzsolódási analízise"""
        code = partner.get("partner_code", "N/A")
        name = partner.get("company_name", "Ismeretlen Partner")
        tier = partner.get("tier", "BRONZE")
        contact = partner.get("contact_person", "Beszerzési Vezető")
        phone = partner.get("contact_phone", "")
        email = partner.get("contact_email", "")
        
        hist = partner.get("historical_metrics", {})
        recent = partner.get("recent_activity", {})
        
        avg_cycle_days = int(hist.get("avg_order_interval_days", 14))
        monthly_avg_spend = float(hist.get("monthly_avg_spend_huf", 1000000))
        last_order_str = recent.get("last_order_date", "2026-08-01")
        spend_30d = float(recent.get("spend_last_30_days_huf", 0))
        
        try:
            ref_date = datetime.date.fromisoformat(ref_date_str)
            last_order_date = datetime.date.fromisoformat(last_order_str)
            days_since_last_order = max(0, (ref_date - last_order_date).days)
        except Exception:
            days_since_last_order = 20
            
        # Ciklusidő késési arány és költés visszaesés
        delay_ratio = round(days_since_last_order / max(1, avg_cycle_days), 2)
        revenue_drop_pct = round(max(0.0, (monthly_avg_spend - spend_30d) / max(1.0, monthly_avg_spend) * 100.0), 1)
        
        # Churn Score számítás (0 - 100)
        # 1. Ciklusidő faktor (max 50 pont)
        if delay_ratio <= 1.0:
            delay_pts = 0
        elif delay_ratio <= self.cycle_delay_threshold:  # <= 1.5x
            delay_pts = 20
        elif delay_ratio <= 2.5:
            delay_pts = 35
        else:
            delay_pts = 50
            
        # 2. Forgalom visszaesési faktor (max 50 pont)
        drop_pts = min(50, round(revenue_drop_pct / 2.0))
        
        total_churn_score = min(100, delay_pts + drop_pts)
        
        # Kockázati szint besorolás
        if total_churn_score >= 70 or (delay_ratio >= self.cycle_delay_threshold and revenue_drop_pct >= self.revenue_drop_threshold):
            risk_level = "HIGH_RISK_CHURN"
            risk_label = "Magas Kockázat – Lemorzsolódás Szélén"
            action_urgency = "IMMEDIATE_48H_ACTION"
        elif total_churn_score >= 40 or delay_ratio >= 1.2 or revenue_drop_pct >= 25.0:
            risk_level = "WATCHLIST_DRIFTING"
            risk_label = "Figyelmeztető – Lassuló Rendelési Ütem"
            action_urgency = "MONITOR_WEEKLY"
        else:
            risk_level = "HEALTHY_ACTIVE"
            risk_label = "Egészséges – Rendszeresen Vásárló"
            action_urgency = "NO_ACTION_REQUIRED"
            
        # RFM Szegmentáció
        rfm_segment = "Champions" if risk_level == "HEALTHY_ACTIVE" and tier in ["GOLD", "PLATINUM"] else (
            "At-Risk VIPs" if risk_level == "HIGH_RISK_CHURN" and tier in ["GOLD", "PLATINUM"] else (
                "At-Risk Standard" if risk_level == "HIGH_RISK_CHURN" else "Drifting Customers"
            )
        )
        
        # Konkurencia-átpártolás vizsgálata
        freq_cats = hist.get("frequent_categories", [])
        last_cat = recent.get("last_ordered_category", "")
        missing_categories = [c for c in freq_cats if c != last_cat]
        
        competitor_warning = None
        if len(missing_categories) > 0 and (risk_level in ["HIGH_RISK_CHURN", "WATCHLIST_DRIFTING"]):
            competitor_warning = {
                "suspected": True,
                "missing_categories": missing_categories,
                "message": f"Konkurencia veszély: A partner korábban rendszeresen vásárolta a(z) {missing_categories} kategóriákat, de az elmúlt időszakban nem rendelt belőlük. Valószínűleg konkurens beszállító lépett be!"
            }
            
        # Visszatartó és Reaktivációs Akcióterv
        retention_plan = self._generate_retention_plan(partner, risk_level, delay_ratio, revenue_drop_pct, competitor_warning)
        
        # Riasztási és Eszkalációs csatorna
        escalation = self._generate_escalation(partner, risk_level, total_churn_score, retention_plan)
        
        return {
            "partner_code": code,
            "company_name": name,
            "tier": tier,
            "contact_person": contact,
            "contact_phone": phone,
            "contact_email": email,
            "analyzed_at": datetime.datetime.now().isoformat(),
            "metrics": {
                "avg_cycle_days": avg_cycle_days,
                "days_since_last_order": days_since_last_order,
                "cycle_delay_ratio": delay_ratio,
                "monthly_avg_spend_huf": monthly_avg_spend,
                "spend_last_30_days_huf": spend_30d,
                "revenue_drop_percent": revenue_drop_pct,
                "total_orders_last_12m": hist.get("total_orders_last_12m", 0),
                "lifetime_spend_huf": hist.get("lifetime_spend_huf", 0)
            },
            "churn_assessment": {
                "churn_risk_score": total_churn_score,
                "risk_level": risk_level,
                "risk_label": risk_label,
                "rfm_segment": rfm_segment,
                "action_urgency": action_urgency
            },
            "competitor_switch_analysis": competitor_warning,
            "retention_strategy": retention_plan,
            "escalation": escalation
        }

    def _generate_retention_plan(
        self,
        partner: Dict[str, Any],
        risk_level: str,
        delay_ratio: float,
        drop_pct: float,
        competitor_warning: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Testreszabható visszatartó ajánlat és értékesítési forgatókönyv generálás"""
        tier = partner.get("tier", "BRONZE")
        name = partner.get("company_name", "Partner")
        contact = partner.get("contact_person", "Cégvezető")
        top_skus = partner.get("historical_metrics", {}).get("top_skus", [])
        
        if risk_level == "HEALTHY_ACTIVE":
            return {
                "strategy_type": "LOYALTY_MAINTENANCE",
                "title": "Ügyfél elégedettség fenntartása",
                "offer_details": "Normál partneri kapcsolattartás, nincs szükség beavatkozásra.",
                "sales_script": None
            }
            
        # Ha VIP (Gold / Platinum) partner van veszélyben
        if tier in ["GOLD", "PLATINUM"] and (self.retention_mode in ["tier_adaptive", "bonus_discount_offer"]):
            bonus_discount = self.vip_extra_discount
            title = f"Exkluzív VIP Reaktivációs Ajánlat (+{bonus_discount:.0f}% Extra Bónusz Kedvezmény)"
            offer = (
                f"Ajánljunk fel a(z) {name} részére egy 14 napig érvényes extra +{bonus_discount:.0f}% visszatérő kedvezményt " 
                f"a leggyakrabban rendelt cikkszámaikra ({top_skus}), valamint díjmentes expressz helyszíni kiszállítást a következő megrendelésükre!"
            )
            pitch = (
                f"Tisztelt {contact}! Észrevettük, hogy az elmúlt hetekben lelassult a közös munka, " 
                f"és szeretnénk biztosítani, hogy a kiemelt {tier} partneri státuszuk előnyeit a jövőben is maximálisan kihasználhassák. " 
                f"Egyeztessünk egy 10 perces telefonos auditot: felajánlunk egy egyedi +{bonus_discount:.0f}% projekt-bónuszt a kedvenc termékeikre!"
            )
            action_steps = [
                "1. KAM telefonos visszahívás indítása 48 órán belül.",
                f"2. Speciális +{bonus_discount:.0f}% kedvezménykupon aktiválása az ERP-ben 14 napra.",
                "3. Személyes igényfelmérés: van-e új kivitelezési projekt vagy konkurens árajánlat."
            ]
        else:
            # Silver / Bronze vagy kérdéssor mód
            title = "Diagnosztikai Elégedettségi Feltárás (Kedvezmény nélkül)"
            offer = "Részletes kérdéssor a rendelési elmaradás okának tisztázására (projektcsúszás vs konkurencia).",
            pitch = (
                f"Kedves {contact}! Látjuk, hogy mostanában nem érkezett megrendelés a(z) {name}-től. " 
                "Szeretnénk megkérdezni: van-e olyan folyamatban lévő munkájuk, amiben segíteni tudunk, " 
                "vagy tapasztaltak-e bármilyen minőségi/ár problémát a legutóbbi szállításainknál?"
            )
            action_steps = [
                "1. Baráti érdeklődő hívás az értékesítő által.",
                "2. Konkurencia árszint felmérése, ha átpártolás gyanúja merül fel."
            ]
            
        is_vip_bonus = (tier in ["GOLD", "PLATINUM"]) and (self.retention_mode in ["tier_adaptive", "bonus_discount_offer"])
        return {
            "strategy_type": "VIP_BONUS_RETENTION" if is_vip_bonus else "DIAGNOSTIC_CHECK_IN",
            "title": title,
            "offer_details": offer,
            "sales_pitch": pitch,
            "action_steps": action_steps
        }

    def _generate_escalation(
        self,
        partner: Dict[str, Any],
        risk_level: str,
        churn_score: int,
        retention: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Eszkalációs útvonal kijelölése"""
        tier = partner.get("tier", "BRONZE")
        phone = partner.get("contact_phone", "")
        clean_phone = "".join([c for c in phone if c.isdigit() or c == "+"])
        
        is_instant = False
        if risk_level == "HIGH_RISK_CHURN" and tier in ["GOLD", "PLATINUM"]:
            is_instant = True
            
        return {
            "instant_alert_triggered": is_instant,
            "channels": ["TELEGRAM_BOT", "DASHBOARD_BANNER", "SALES_EMAIL"] if is_instant else ["WEEKLY_SALES_DIGEST"],
            "assigned_to": "Kovács László (B2B Értékesítési Igazgató)" if tier == "PLATINUM" else "Területi Key Account Manager",
            "sla_deadline_hours": 48 if is_instant else 168,
            "one_click_dial": f"tel:{clean_phone}" if clean_phone else None,
            "alert_message": f"LEMORZSOLÓDÁSI VÉSZJELZÉS: {partner.get('company_name')} ({tier}) kockázati pontszám: {churn_score}/100! 48 órán belüli visszahívás szükséges!" if is_instant else None
        }

    def _persist_audit_log(self, analyzed_partners: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Tartós naplózás és statisztikák frissítése"""
        os.makedirs(os.path.dirname(self.churn_log_path), exist_ok=True)
        existing = []
        if os.path.exists(self.churn_log_path):
            try:
                with open(self.churn_log_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        existing = data
                    elif isinstance(data, dict) and "partners" in data:
                        existing = data.get("partners", [])
            except Exception:
                existing = []
                
        m = {p["partner_code"]: idx for idx, p in enumerate(existing)}
        for ap in analyzed_partners:
            c = ap["partner_code"]
            if c in m:
                existing[m[c]] = ap
            else:
                existing.append(ap)
                m[c] = len(existing) - 1
                
        high_risk_count = sum(1 for p in existing if p.get("churn_assessment", {}).get("risk_level") == "HIGH_RISK_CHURN")
        drifting_count = sum(1 for p in existing if p.get("churn_assessment", {}).get("risk_level") == "WATCHLIST_DRIFTING")
        healthy_count = sum(1 for p in existing if p.get("churn_assessment", {}).get("risk_level") == "HEALTHY_ACTIVE")
        revenue_at_risk = sum(
            p.get("metrics", {}).get("monthly_avg_spend_huf", 0)
            for p in existing if p.get("churn_assessment", {}).get("risk_level") == "HIGH_RISK_CHURN"
        )
        
        db_payload = {
            "last_updated": datetime.datetime.now().isoformat(),
            "total_monitored_partners": len(existing),
            "summary_kpis": {
                "high_risk_churn_count": high_risk_count,
                "watchlist_drifting_count": drifting_count,
                "healthy_active_count": healthy_count,
                "monthly_revenue_at_risk_huf": round(revenue_at_risk)
            },
            "partners": existing
        }
        
        with open(self.churn_log_path, "w", encoding="utf-8") as f:
            json.dump(db_payload, f, indent=2, ensure_ascii=False)
            
        return db_payload["summary_kpis"]

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fő belépési pont"""
        ref_date = payload.get("reference_date") or datetime.date.today().isoformat()
        
        partners_input = []
        if "partners" in payload and isinstance(payload["partners"], list):
            partners_input = payload["partners"]
        elif "partner" in payload and isinstance(payload["partner"], dict):
            partners_input = [payload["partner"]]
        elif "sample_data" in payload and isinstance(payload["sample_data"], dict):
            partners_input = [payload["sample_data"]]
        else:
            partners_input = [payload]
            
        results = []
        for p in partners_input:
            results.append(self._analyze_partner(p, ref_date))
            
        # Rendezés a legsürgősebb kockázati pontszám szerint elöl
        results.sort(key=lambda x: x.get("churn_assessment", {}).get("churn_risk_score", 0), reverse=True)
        
        kpis = self._persist_audit_log(results)
        high_risk = [r for r in results if r["churn_assessment"]["risk_level"] == "HIGH_RISK_CHURN"]
        instant_alerts = [r for r in results if r["escalation"]["instant_alert_triggered"]]
        
        return {
            "status": "success",
            "module_id": "09_b2b_lemorzsolodas_elorejelzes_rfm_eletci",
            "analyzed_at": datetime.datetime.now().isoformat(),
            "reference_date": ref_date,
            "partners_analyzed_count": len(results),
            "summary_kpis": kpis,
            "high_risk_count": len(high_risk),
            "instant_alerts_count": len(instant_alerts),
            "immediate_actions": [
                {
                    "partner_code": r["partner_code"],
                    "company_name": r["company_name"],
                    "tier": r["tier"],
                    "churn_risk_score": r["churn_assessment"]["churn_risk_score"],
                    "risk_level": r["churn_assessment"]["risk_level"],
                    "assigned_to": r["escalation"]["assigned_to"],
                    "one_click_dial": r["escalation"]["one_click_dial"],
                    "retention_title": r["retention_strategy"]["title"]
                }
                for r in high_risk
            ],
            "analyzed_partners": results
        }

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Szabványos hub belépési pont"""
    handler = B2BChurnPredictionHandler(config)
    return handler.execute(payload)

if __name__ == "__main__":
    sample = {
        "partners": [
            {
                "partner_code": "TEST-01",
                "company_name": "Teszt Klíma Kft.",
                "tier": "GOLD",
                "historical_metrics": {"avg_order_interval_days": 10, "monthly_avg_spend_huf": 2000000},
                "recent_activity": {"last_order_date": "2026-08-01", "spend_last_30_days_huf": 0}
            }
        ]
    }
    res = run(sample)
    print(json.dumps(res, indent=2, ensure_ascii=False))