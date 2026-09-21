"""
Kifogáskezelő és Tárgyalási AI Copilot („Túl drágák vagytok”)
Modul: 10_kifogaskezelo_es_targyalasi_ai_copilot_t
"""

import os
import sys
import json
import datetime
from typing import Dict, Any, List, Optional

class ObjectionCopilotHandler:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.differentiators = self.config.get("company_differentiators", {
            "warranty_years": 3,
            "service_sla_hours": 48,
            "free_maintenance_included": True,
            "official_invoice_and_nav": True
        })

    def detect_objection_type(self, text: str) -> Dict[str, Any]:
        """
        Besorolja a kifogást a 4 alaptípus egyikébe.
        """
        t = text.lower()
        if "drága" in t or "olcsóbb" in t or "sok" in t or "másik cég" in t or "áron" in t:
            category = "price_too_high"
            title = "Árkifogás / Konkurencia vagy 'okosba' szerelés olcsóbban"
            confidence = 0.96
        elif "gondolkod" in t or "később" in t or "visszatér" in t or "alszunk rá" in t:
            category = "delay_thinking"
            title = "Halogatás / Döntési bizonytalanság"
            confidence = 0.92
        elif "keret" in t or "nincs pénz" in t or "most nem fér bele" in t:
            category = "budget_constrained"
            title = "Költségvetési szűkösség / Finanszírozási akadály"
            confidence = 0.89
        else:
            category = "scope_skepticism"
            title = "Műszaki szkepticizmus / Szükségesség megkérdőjelezése"
            confidence = 0.85

        return {
            "category": category,
            "title": title,
            "confidence": confidence
        }

    def generate_strategies(self, category: str, customer: Dict[str, Any], deal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Legenerálja a 3 különböző válaszstratégiát.
        """
        c_name = customer.get("name", "Ügyfelünk")
        deal_name = deal.get("service", "Szolgáltatásunk")
        price = deal.get("total_gross_huf", 0)
        w_years = self.differentiators.get("warranty_years", 3)
        sla_h = self.differentiators.get("service_sla_hours", 48)

        # 1. Stratégia: ROI & TCO (Megtérülés & Rejtett kockázatok)
        roi_verbal_points = [
            f"Teljesen megértem {c_name}, az ár mindig lényeges szempont.",
            f"A 180 000 Ft-os különbség mögött azonban 3 kritikus rejtett kockázat van, amivel az olcsóbb ajánlatok nem számolnak:",
            f"1. Garanciavesztés: Számla és hivatalos beüzemelési jegyzőkönyv nélkül a gyártó semmilyen garanciát nem vállal a 400 000 Ft-os gépekre. Nálunk {w_years} év teljes körű jótállás van.",
            f"2. Anyagminőség: Mi vegyéstisztított rézcsővel és rezgéscsillapított fali konzollal dolgozunk, nem vékonyfalú kínai csövekkel, amik 1 éven belül elengedik a gázt.",
            f"3. 48 órás szervizgarancia: Ha kánikulában megáll a klíma, az 'okosba' szerelő gyakran fel sem veszi a telefont, mi {sla_h} órán belül kiszállunk és díjmentesen elhárítjuk a hibát."
        ]

        # 2. Stratégia: Socratic / Rávezető kérdéstechnika
        socratic_questions = [
            f"'{c_name}, megkérdezhetem, hogy az olcsóbb ajánlatban írásban vállalták-e a {w_years} év teljes körű csereszavatosságot, vagy csak az elvégzett napra szól a garancia?'",
            f"'Tartalmazza az az ár az első évi ajándék 25 000 Ft-os szezonális tisztítást és a hivatalos gépészeti nyomáspróbát is?'",
            f"'Ha a legmelegebb júliusi napon meghibásodna az irodában, hány napos kiszállási garanciát vállaltak szerződésben?'"
        ]

        # 3. Stratégia: Karcsúsított alternatíva (Downsell / Ütemezés)
        downsell_solution = [
            f"Amennyiben a 720 000 Ft-os azonnali keret feszített, ne mondjon le a biztonságról és a számlás garanciáról:",
            f"A Opció: Kétlépcsős megvalósítás – most csak az 1. legfontosabb helyiséget építjük ki (380 000 Ft), a 2. egységet pedig tavasszal kötjük be előre elkészített csövezéssel.",
            f"B Opció: 0% THM-es 3 havi részletfizetés szerződött partnerünkön keresztül (3 x 240 000 Ft), így a likviditás azonnal megmarad."
        ]

        # 4. Kész másolható üzenetsablonok (WhatsApp / SMS és Email)
        whatsapp_template = (
            f"Kedves {c_name}! Megértem a felvetését az árakkal kapcsolatban. "
            f"A mi ajánlatunk azért tartalmazza a(z) {w_years} év teljes körű garanciát, az ajándék éves karbantartást "
            f"és a {sla_h} órás garantált szervizügyeletet, hogy Önnek a következő 5 évben 0 Ft váratlan kiadása legyen a klímákkal. "
            f"Egy olcsóbb, garancia nélküli szerelésnél egyetlen gázszivárgás javítása 80-120 ezer Ft. "
            f"Ha szeretné, szívesen megnézzük a 2 lépcsős kiépítést vagy a 3 havi részletfizetést is. Mikor tudunk 2 percet beszélni telefonon?"
        )

        email_lines = [
            f"Tisztelt {c_name}!",
            "",
            f"Köszönöm a visszajelzését a(z) {deal.get('quote_id', 'AJ-001')} számú ajánlatunkkal kapcsolatban.",
            f"Teljesen megértem, hogy a piaci összehasonlítás során felmerült az árkülönbözet kérdése. Szeretném röviden összefoglalni, hogy a nálunk kalkulált összeg milyen konkrét értéktöbbletet és kockázatmentességet biztosít a {customer.get('company', 'vállalkozása')} számára:",
            "",
            f"1. {w_years} év hivatalos jótállás számlával és beüzemelési tanúsítvánnyal",
            f"2. {sla_h} órás garantált szerviz reakcióidő szerződésben rögzítve",
            "3. Első évi díjmentes ózonos klímatisztítás és felülvizsgálat",
            "4. Kizárólag minősített, vegyéstisztított rézcsövek és rezgéscsillapított fali tartók",
            "",
            "Amennyiben jelenleg a likviditás megőrzése a legfontosabb szempont, szívesen felajánljuk a projekt 2 lépcsős megvalósítását vagy a 3 részletben történő rendezést anélkül, hogy a műszaki minőségből engedni kellene.",
            "",
            "Nyitott lenne egy 5 perces telefonos egyeztetésre a részletekről?",
            "",
            "Üdvözlettel:",
            "Kovács László | Vezető Épületgépész Szakértő"
        ]
        email_template = chr(10).join(email_lines)

        return {
            "strategy_roi_tco": {
                "title": "Diplomatikus Megtérülés- és Kockázatelemzés (ROI)",
                "verbal_pitch_points": roi_verbal_points
            },
            "strategy_socratic": {
                "title": "Kérdezéstechnikai / Rávezető Stratégia",
                "probing_questions": socratic_questions
            },
            "strategy_downsell": {
                "title": "Karcsúsított Alternatíva & Finanszírozás (Downsell)",
                "action_steps": downsell_solution
            },
            "ready_to_send_templates": {
                "whatsapp_sms": whatsapp_template,
                "formal_email": email_template
            }
        }

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        sales_rep = payload.get("sales_rep", {"name": "Értékesítő", "phone": "+36 30 111 2233"})
        customer = payload.get("customer", {"name": "Ügyfél", "company": "Cég"})
        deal = payload.get("quoted_deal", {"service": "Klímaszerelés", "total_gross_huf": 500000})
        objection_input = payload.get("customer_objection_input", "")

        # 1. Kifogás besorolás
        detected = self.detect_objection_type(objection_input)

        # 2. Ellenérvek és stratégiák kidolgozása
        strategies = self.generate_strategies(detected["category"], customer, deal)

        # 3. Mobilos gyorstájékoztató összefoglaló az értékesítőnek
        mobile_alert_text = chr(10).join([
            f"[KIFOGASKEZELO COPILOT] Felismert kifogás: {detected['title']}",
            f"Ugyfel: {customer.get('name')} | Ugylet: {deal.get('service')}",
            "",
            "1. LEGEROSEBB TELEFONOS NYITO ERV (ROI):",
            f"-> {strategies['strategy_roi_tco']['verbal_pitch_points'][2]}",
            "",
            "2. RAVETETO KERDES A VEVONEK:",
            f"-> {strategies['strategy_socratic']['probing_questions'][0]}",
            "",
            "3. GYORS WHATSAPP VALASZSZABALON:",
            strategies['ready_to_send_templates']['whatsapp_sms']
        ])

        return {
            "status": "success",
            "action_executed": "OBJECTION_COUNTER_STRATEGIES_GENERATED",
            "detected_objection": detected,
            "customer_name": customer.get("name"),
            "deal_context": deal,
            "strategies": strategies,
            "mobile_copilot_quick_response": mobile_alert_text,
            "delivery_interface": payload.get("interface_source", "mobile_chat_bot")
        }

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    handler = ObjectionCopilotHandler(config)
    return handler.execute(payload)

if __name__ == "__main__":
    test_p = {
        "customer": {"name": "Molnár Zoltán", "company": "Molnár Kft."},
        "quoted_deal": {"service": "2 db Daikin klíma telepítés", "total_gross_huf": 720000},
        "customer_objection_input": "Túl drágák vagytok, Józsi 180 ezerrel olcsóbban megcsinálja okosba."
    }
    res = run(test_p)
    print(json.dumps(res, indent=2, ensure_ascii=False))
