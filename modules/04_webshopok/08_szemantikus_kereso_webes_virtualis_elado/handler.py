# -*- coding: utf-8 -*-
"""
Module 4.08: Szemantikus Kereső & Webes Virtuális Eladó Bot
Kötetlen vevői igények megértése, döntéstámogató összehasonlító mátrix,
azonnali raktári alternatíva készlethiánynál és 1-kattintásos kiegészítő csomagajánlás.
"""
import os
import sys
import json
import datetime
from typing import Dict, Any, List, Optional

class SemanticShoppingAdvisorHandler:
    """Szemantikus kereső és virtuális eladó motor"""
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.service_mode = self.config.get("service_mode", "mock")
        self.search_mode = self.config.get("search_mode", "hybrid_full_semantic")
        self.ui_mode = self.config.get("ui_dialogue_mode", "comparative_decision_matrix")
        self.cross_sell_mode = self.config.get("cross_sell_mode", "combined_inventory_and_bundle")
        self.storage_path = self.config.get("storage_path", "data/szemantikus_kereso_naplo.json")
        
        # Belső termékkatalógus szemantikus címkékkel és valós készlettel
        self.products = [
            {
                "sku": "BOSCH-GBH-18V-22",
                "name": "Bosch Professional GBH 18V-22 Akkus Fúrókalapács",
                "brand": "Bosch Professional",
                "category": "furokalapacs",
                "tags": ["beton", "panel", "furas", "veses", "sds_plus", "akkus", "pneumatikus"],
                "price_gross_huf": 74990,
                "stock": 6,
                "power_joules": 1.9,
                "tier": "BESTSELLER",
                "expert_verdict": "Ideális panel betonfalhoz! Pneumatikus ütőműve erőfeszítés nélkül viszi a kemény vasbetont."
            },
            {
                "sku": "MAKITA-DHR-171",
                "name": "Makita DHR171Z Akkus Fúrókalapács",
                "brand": "Makita",
                "category": "furokalapacs",
                "tags": ["beton", "panel", "sds_plus", "akkus", "kompakt"],
                "price_gross_huf": 54990,
                "stock": 0,  # Készlethiány teszthez
                "power_joules": 1.2,
                "tier": "ENTRY_HAMMER",
                "expert_verdict": "Kompakt, könnyű gép, de jelenleg beszállítói készlethiány miatt nem elérhető."
            },
            {
                "sku": "DEWALT-DCH-273",
                "name": "DeWalt DCH273P2T Akkus Fúrókalapács 2x5.0Ah",
                "brand": "DeWalt",
                "category": "furokalapacs",
                "tags": ["beton", "panel", "ipari", "profi", "sds_plus", "akkus"],
                "price_gross_huf": 139990,
                "stock": 4,
                "power_joules": 2.1,
                "tier": "PREMIUM",
                "expert_verdict": "Profi építőipari csúcsmodell 2 db nagy kapacitású 5.0Ah akkuval és kofferrel."
            },
            {
                "sku": "BOSCH-GSR-18V-55",
                "name": "Bosch Professional GSR 18V-55 Fúrócsavarozó",
                "brand": "Bosch Professional",
                "category": "furocsavarozo",
                "tags": ["csavarozas", "fa", "fem", "butor", "akkus"],
                "price_gross_huf": 49990,
                "stock": 9,
                "power_joules": 0.0,
                "tier": "BASIC_DRILL",
                "expert_verdict": "Fa és fém fúrásra, bútorokhoz szuper, de kemény panel betonba önmagában nem ajánlott."
            }
        ]
        
        # Kiegészítők
        self.accessories = {
            "beton": {
                "sku": "BOSCH-SDS-PLUS-SET-5",
                "name": "Bosch 5-részes SDS-Plus Betonfúró Készlet (5, 6, 6, 8, 10 mm)",
                "price_gross_huf": 5490,
                "discount_price_huf": 4490,
                "reason": "Kifejezetten panel falazathoz és dűbelezéshez optimalizált 4-élű keményfém fúrószárak."
            }
        }

    def analyze_user_intent(self, query: str) -> Dict[str, Any]:
        """Kötetlen magyar vásárlói igény elemzése és szándékkivonatolás (1. Kérdés)"""
        q = query.lower()
        intents = []
        requires_pneumatic = False
        power_source = "akkus" if ("akku" in q or "vezeték nélkül" in q or "akkumlator" in q) else "mindegy"
        
        if any(w in q for w in ["beton", "panel", "panelba", "tégla", "falba", "polc"]):
            intents.append("CONCRETE_OR_WALL_DRILLING")
            requires_pneumatic = True
        if any(w in q for w in ["butor", "bútor", "csavar", "fa"]):
            intents.append("WOOD_OR_SCREWDRIVING")
            
        wants_accessories = any(w in q for w in ["szár", "fúrószár", "fej", "készlet", "tartozék"])
        
        expert_advice = ""
        if requires_pneumatic:
            expert_advice = (
                "Panel lakás betonfalához a hagyományos ütvefúrók nem elegek, mert csak hangosak és elkopik a hegyük. " 
                "Ide valódi pneumatikus ütőművel rendelkező SDS-Plus fúrókalapács szükséges, ami erőfeszítés nélkül, másodpercek alatt fúrja ki a tipli helyét!"
            )
        else:
            expert_advice = "Általános otthoni szereléshez és bútorokhoz egy könnyű, nagy nyomatékú fúrócsavarozó a legkényelmesebb választás."
            
        return {
            "raw_query": query,
            "intents": intents,
            "requires_pneumatic_hammer": requires_pneumatic,
            "power_source_preference": power_source,
            "wants_accessories": wants_accessories,
            "expert_advice": expert_advice
        }

    def search_and_rank_products(self, intent_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Termékek rangsorolása szemantikai relevancia alapján"""
        req_pneumatic = intent_data["requires_pneumatic_hammer"]
        ranked = []
        
        for p in self.products:
            score = 50
            if req_pneumatic and p["category"] == "furokalapacs":
                score += 40
            if "beton" in p["tags"]:
                score += 10
            if p["stock"] > 0:
                score += 5
            else:
                score -= 15  # készlethiány levonás
                
            ranked.append({
                "product": p,
                "relevance_score": score,
                "is_in_stock": p["stock"] > 0
            })
            
        ranked.sort(key=lambda x: x["relevance_score"], reverse=True)
        return ranked

    def handle_alternatives_and_cross_sell(self, top_matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Készlethiány pótlás és intelligens kiegészítő csomagajánlás (3. Kérdés)"""
        out_of_stock_item = None
        alternative_proposal = None
        
        for item in self.products:
            if item["stock"] == 0:
                out_of_stock_item = item
                break
                
        # Raktáron lévő helyettesítő kiválasztása
        if out_of_stock_item:
            alt = self.products[0]  # Bosch GBH 18V-22
            alternative_proposal = {
                "original_requested_sku": out_of_stock_item["sku"],
                "original_name": out_of_stock_item["name"],
                "recommended_alternative_sku": alt["sku"],
                "recommended_name": alt["name"],
                "in_stock_units": alt["stock"],
                "explanation": f"A(z) {out_of_stock_item['name']} átmenetileg elfogyott, de a(z) {alt['name']} azonnal raktáron van, ráadásul erősebb (1.9J ütőerő) és azonnal szállítható!"
            }
            
        # Kiegészítő ajánlat
        bundle_offer = None
        if self.cross_sell_mode in ["smart_bundle_accessories", "combined_inventory_and_bundle"]:
            acc = self.accessories["beton"]
            bundle_offer = {
                "accessory_sku": acc["sku"],
                "accessory_name": acc["name"],
                "original_price_huf": acc["price_gross_huf"],
                "bundle_price_huf": acc["discount_price_huf"],
                "savings_huf": acc["price_gross_huf"] - acc["discount_price_huf"],
                "why_needed": acc["reason"],
                "add_bundle_to_cart_url": f"https://profigepesz.hu/cart/add-bundle?primary=BOSCH-GBH-18V-22&acc={acc['sku']}"
            }
            
        return {
            "alternative_proposal": alternative_proposal,
            "bundle_offer": bundle_offer
        }

    def build_comparative_matrix(self, ranked: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Döntéstámogató összehasonlító mátrix felépítése (2. Kérdés)"""
        cards = []
        for entry in ranked[:3]:
            p = entry["product"]
            cards.append({
                "tier": p["tier"],
                "sku": p["sku"],
                "name": p["name"],
                "price_gross_huf": p["price_gross_huf"],
                "in_stock": p["stock"] > 0,
                "stock_count": p["stock"],
                "power_joules": p["power_joules"],
                "expert_verdict": p["expert_verdict"],
                "relevance_score": entry["relevance_score"],
                "add_to_cart_url": f"https://profigepesz.hu/cart/add?sku={p['sku']}&qty=1"
            })
        return cards

    def process_query(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fő lekérdezés-feldolgozás"""
        query_text = payload.get("user_query", "betonfúró") 
        session_id = payload.get("session_id", f"SESS-{datetime.datetime.now().strftime('%H%M%S')}")
        
        intent_data = self.analyze_user_intent(query_text)
        ranked = self.search_and_rank_products(intent_data)
        cards = self.build_comparative_matrix(ranked)
        inventory_actions = self.handle_alternatives_and_cross_sell(ranked)
        
        result = {
            "session_id": session_id,
            "user_query": query_text,
            "intent_analysis": intent_data,
            "search_mode_used": self.search_mode,
            "ui_dialogue_mode": self.ui_mode,
            "comparative_matrix": cards,
            "alternative_replacement": inventory_actions["alternative_proposal"],
            "smart_cross_sell_bundle": inventory_actions["bundle_offer"],
            "handled_at": datetime.datetime.now().isoformat()
        }
        
        self._log_interaction(result)
        return result

    def _log_interaction(self, record: Dict[str, Any]) -> None:
        """Audit napló mentése"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        existing = []
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = []
        existing.append(record)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(existing[-100:], f, indent=2, ensure_ascii=False)

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Hub belépési pont"""
        res = self.process_query(payload)
        return {
            "status": "success",
            "module_id": "08_szemantikus_kereso_webes_virtualis_elado",
            "processed_at": datetime.datetime.now().isoformat(),
            "advisor_result": res
        }

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Szabványos hub belépési pont"""
    effective_config = dict(config or {})
    if "config" in payload and isinstance(payload["config"], dict):
        effective_config.update(payload["config"])
        
    handler = SemanticShoppingAdvisorHandler(effective_config)
    return handler.execute(payload)

if __name__ == "__main__":
    sample = {
        "user_query": "betonba kellene fúrnom a panelban, akkus gép és fúrószár is kell",
        "session_id": "SESS-TEST-001"
    }
    res = run(sample)
    print(json.dumps(res, indent=2, ensure_ascii=False))