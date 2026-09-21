"""
Ajánlat Megnyitás-Követés & Hőtérkép Riasztás
Modul: 08_ajanlat_megnyitas_kovetes_hoterkep_riasz
"""

import os
import sys
import json
import datetime
from typing import Dict, Any, List, Optional

class OfferTrackingHandler:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.alert_channels = self.config.get("alert_channels", ["whatsapp", "telegram", "sms", "dashboard_push"])
        self.alert_timing_mode = self.config.get("alert_timing_mode", "instant")
        self.reopen_alert_enabled = self.config.get("reopen_alert_enabled", True)
        self.session_db_path = "data/ajanlat_kovetes_sessionok.json"

    def calculate_heat_score(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI Döntési Forróság Index kalkuláció (0-100)
        """
        session_num = int(telemetry.get("session_number", 1))
        dwell_sec = int(telemetry.get("total_dwell_seconds", 0))
        scroll_pct = int(telemetry.get("scroll_depth_percent", 0))
        clicked = telemetry.get("clicked_elements", [])
        sections = telemetry.get("sections_visited", {})

        score = 0
        # 1. Olvasási idő pontok (max 40)
        if dwell_sec >= 120:
            score += 40
        elif dwell_sec >= 60:
            score += 30
        elif dwell_sec >= 30:
            score += 20
        elif dwell_sec >= 10:
            score += 10

        # 2. Görgetési mélység (max 20)
        if scroll_pct >= 80:
            score += 20
        elif scroll_pct >= 50:
            score += 10

        # 3. Újramegnyitás szorzó (max 25)
        if session_num >= 3:
            score += 25
        elif session_num == 2:
            score += 15

        # 4. Interakciók / Kártya részletek / Garancia nézés (max 15)
        if "pricing_packages" in sections and sections["pricing_packages"].get("dwell_seconds", 0) >= 30:
            score += 10
        if len(clicked) > 0:
            score += 5

        # Kategória besorolás
        if score >= 85:
            heat_level = "BURNING_HOT"
            heat_badge = "[EGETOEN FORRO LEAD - AZONNALI HIVAS AJANLOTT]"
            action_recommendation = "Az ugyfel tobb mint 1 perce tanulmanyozza a szamokat es mar ujranyitotta. Hivja fel a kovetkezo 2 percben!"
        elif score >= 60:
            heat_level = "HOT"
            heat_badge = "[FORRO ERDEKLODES]"
            action_recommendation = "Az ugyfel alaposan atnezte a csomagokat es a garanciat. Kivallo pillanat a telefonos kapcsolatteremtesre."
        elif score >= 35:
            heat_level = "WARM"
            heat_badge = "[MELEG ERDEKLODO]"
            action_recommendation = "Az ugyfel atfutotta az ajanlatot, erdemes rovid koveto uzenetet vagy hivast inditani."
        else:
            heat_level = "COLD"
            heat_badge = "[HIDEG / GYORS ATTEKINTES]"
            action_recommendation = "Rovid megnyitas, egyelore nincs szukseg azonnali surgos hivasra."

        return {
            "score": min(100, score),
            "heat_level": heat_level,
            "heat_badge": heat_badge,
            "action_recommendation": action_recommendation
        }

    def generate_sales_alert_message(self, quote_id: str, customer: Dict[str, Any], telemetry: Dict[str, Any], heat_data: Dict[str, Any]) -> str:
        """
        Strukturált, kattintható híváslinkes riasztási üzenet összeállítása az értékesítőnek.
        """
        cust_name = customer.get("name", "Ugyfel")
        cust_phone = customer.get("phone", "")
        call_link = f"tel:{cust_phone}" if cust_phone else ""
        session_num = telemetry.get("session_number", 1)
        dwell_sec = telemetry.get("total_dwell_seconds", 0)
        device = telemetry.get("device_type", "Mobil")
        sections = telemetry.get("sections_visited", {})

        top_section = "Arak es Csomagok"
        max_sec = 0
        for s_name, s_data in sections.items():
            if s_data.get("dwell_seconds", 0) > max_sec:
                max_sec = s_data.get("dwell_seconds", 0)
                top_section = s_name

        reopen_marker = f"[FIGYELEM: {session_num}. UJRAMEGNYITAS!]" if session_num > 1 else "[ELSO MEGNYITAS]"

        icebreaker_pitch = f"Javasolt nyitasi duma a hivashoz: 'Kedves {cust_name}! Kovacs Laszlo vagyok a ProfiKlimatol. Lattam, hogy az iment erkezett meg onhoz a felmeresi ajanlatunk, gondoltam rakerdezek, minden reszlet egyertelmu-e a csomagokkal kapcsolatban?'"

        lines = [
            f"{heat_data['heat_badge']} {reopen_marker}",
            f"Ajanlatszam: {quote_id}",
            f"Ugyfel: {cust_name} ({customer.get('company', 'Maganszemely')})",
            f"Telefon: {cust_phone}",
            "",
            f"-> 1-KATTINTASOS HIVAS INDITASA: {call_link}",
            "",
            "HOTERKEP & ELEMZES:",
            f"- Forrosagi pontszam: {heat_data['score']}/100 ({heat_data['heat_level']})",
            f"- Eltoltott olvasasi ido: {dwell_sec} masodperc",
            f"- Gorgetesi melyseg: {telemetry.get('scroll_depth_percent', 0)}%",
            f"- Eszkoz: {device}",
            f"- Legjobban tanulmanyozott resz: {top_section} ({max_sec} mp)",
            "",
            f"AKCIO JAVASLAT: {heat_data['action_recommendation']}",
            "",
            icebreaker_pitch
        ]
        return chr(10).join(lines)

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        quote_id = payload.get("quote_id", "AJ-DEFAULT")
        sales_rep = payload.get("sales_rep", {
            "id": "SALES-001",
            "name": "Kovács László",
            "phone": "+36 30 111 2233",
            "preferred_channel": "whatsapp"
        })
        customer = payload.get("customer", {
            "name": "Kiss Péter",
            "phone": "+36 30 987 6543",
            "company": "Kiss & Társa Kft."
        })
        telemetry = payload.get("telemetry", {
            "session_number": 1,
            "device_type": "Mobile (Android / Chrome)",
            "total_dwell_seconds": 45,
            "scroll_depth_percent": 80,
            "sections_visited": {"pricing_packages": {"dwell_seconds": 30}}
        })

        # 1. Forrósági pontszám kalkuláció
        heat_data = self.calculate_heat_score(telemetry)

        # 2. Riasztási üzenet és tárcsázó link generálás
        alert_message = self.generate_sales_alert_message(quote_id, customer, telemetry, heat_data)
        call_link = f"tel:{customer.get('phone', '')}"

        # 3. Kézbesítés szimuláció a választott csatornákra
        dispatched_channels = []
        for ch in self.alert_channels:
            dispatched_channels.append({
                "channel": ch,
                "target": sales_rep.get("phone") if ch in ["whatsapp", "sms"] else sales_rep.get("name"),
                "delivery_status": "DELIVERED_INSTANT",
                "timestamp": datetime.datetime.now().isoformat()
            })

        return {
            "status": "success",
            "action_executed": "OFFER_VIEW_HEATMAP_RECORDED",
            "quote_id": quote_id,
            "customer_name": customer.get("name"),
            "customer_phone": customer.get("phone"),
            "click_to_call_link": call_link,
            "session_number": telemetry.get("session_number", 1),
            "is_reopened": telemetry.get("session_number", 1) > 1,
            "dwell_seconds": telemetry.get("total_dwell_seconds", 0),
            "heat_analytics": heat_data,
            "channels_alerted": dispatched_channels,
            "sales_alert_message": alert_message
        }

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    handler = OfferTrackingHandler(config)
    return handler.execute(payload)

if __name__ == "__main__":
    test_p = {
        "quote_id": "AJ-20260920-6067",
        "sales_rep": {"name": "Kovács László", "phone": "+36 30 111 2233"},
        "customer": {"name": "Kiss Péter", "phone": "+36 30 987 6543"},
        "telemetry": {"session_number": 2, "total_dwell_seconds": 110, "scroll_depth_percent": 90}
    }
    res = run(test_p)
    print(json.dumps(res, indent=2, ensure_ascii=False))
