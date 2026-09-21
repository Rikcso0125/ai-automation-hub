"""
Raktári Kétkezes Hangvezérlés (Hands-Free Voice Picking)
Modul: 08_raktari_ketkezes_hangvezerles_hands_free
"""

import os
import sys
import json
import re
import datetime
from typing import Dict, Any, List, Optional, Tuple

class WarehouseVoicePickingHandler:
    """
    Kétkezes raktári hangvezérelt szedési motor Bluetooth fülhallgatókhoz.
    Navigálja a raktárost, hangosan beolvassa a polcokat és tételeket,
    felismeri az ellenőrző kódokat és darabszámokat, valamint kezeli a hiányokat.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.service_mode = self.config.get("service_mode", "mock")
        self.verification_method = self.config.get("verification_method", "check_digit")
        self.shortage_strategy = self.config.get("shortage_strategy", "smart_adaptive")
        self.picking_mode = self.config.get("picking_mode", "single_order")
        self.catalog_db_path = self.config.get("catalog_db_path", "data/termektorzs_katalogus.json")
        self.warehouse_log_path = self.config.get("warehouse_log_path", "data/raktar_hangvezerles_naplo.json")

    def _parse_hungarian_quantity(self, text: str) -> Optional[int]:
        """Magyar szöveges és numerikus darabszám felismerés"""
        t = text.lower().strip()
        num_map = {
            "egy": 1, "kettő": 2, "ketto": 2, "két": 2, "ket": 2,
            "három": 3, "harom": 3, "négy": 4, "negy": 4,
            "öt": 5, "ot": 5, "hat": 6, "hét": 7, "het": 7,
            "nyolc": 8, "kilenc": 9, "tíz": 10, "tiz": 10,
            "tizenegy": 11, "tizenkettő": 12, "tizenhárom": 13,
            "tizenöt": 15, "húsz": 20, "harminc": 30, "negyven": 40, "ötven": 50
        }
        for word, val in num_map.items():
            if word in t:
                return val
        digits = re.findall(r"\d+", t)
        if digits:
            return int(digits[0])
        return None

    def _optimize_route(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Polchelyek szerinti logikai sorrendezés a minimális gyalogláshoz (pl. A -> B -> C)"""
        return sorted(items, key=lambda x: str(x.get("shelf_location", "Z-99-99")))

    def _process_dialogue_step(
        self,
        current_item: Dict[str, Any],
        step_type: str,
        operator_speech: str,
        verif_method: str,
        shortage_strat: str
    ) -> Tuple[bool, Dict[str, Any], str]:
        """Egyetlen hangos dialógus lépés kiértékelése"""
        speech_clean = operator_speech.strip().lower()
        expected_check = str(current_item.get("check_digit", "")).strip().lower()
        sku = str(current_item.get("sku", ""))
        expected_qty = int(current_item.get("quantity_ordered", 1))
        
        # 1. Lépés: Polc ellenőrzése
        if step_type == "CONFIRM_LOCATION":
            verified = False
            if verif_method == "check_digit":
                if expected_check in speech_clean or speech_clean in expected_check:
                    verified = True
            elif verif_method == "sku_last_digits":
                last_digits = sku[-3:].lower()
                if last_digits in speech_clean:
                    verified = True
            else:  # hybrid_dual_check
                if expected_check in speech_clean:
                    verified = True
                    
            if verified:
                tts_response = f"Rendben! Polc igazolva. Szedj ki {expected_qty} darabot ebből: {current_item.get('name')}!"
                return True, {"event": "LOCATION_VERIFIED", "shelf": current_item.get("shelf_location")}, tts_response
            else:
                tts_response = f"Téves ellenőrző kód! A várt kód a(z) {current_item.get('shelf_location')} polcon: {expected_check}. Mondd újra!"
                return False, {"event": "LOCATION_MISMATCH", "expected": expected_check, "heard": operator_speech}, tts_response
                
        # 2. Lépés: Darabszám és készlet nyugtázása
        elif step_type == "CONFIRM_QUANTITY":
            # Hiány vagy sérülés detektálása
            if any(w in speech_clean for w in ["hiány", "hiany", "csak", "sérült", "serult", "nincs"]):
                picked_qty = self._parse_hungarian_quantity(speech_clean) or 0
                shortage_qty = max(0, expected_qty - picked_qty)
                
                backup_shelf = current_item.get("backup_shelf")
                if backup_shelf and shortage_strat in ["smart_adaptive", "redirect_to_backup_shelf"]:
                    tts_response = f"Hiány rögzítve ({picked_qty} db kiszedve). Menj a tartalék polchoz: {backup_shelf} a maradék {shortage_qty} darabért!"
                    event_data = {
                        "event": "SHORTAGE_REDIRECTED_TO_BACKUP",
                        "picked_qty": picked_qty,
                        "shortage_qty": shortage_qty,
                        "backup_shelf": backup_shelf
                    }
                else:
                    tts_response = f"Részmennyiség ({picked_qty} db) rögzítve. {shortage_qty} db hiány feljegyezve a beszerzésnek. Haladj a következő tételhez!"
                    event_data = {
                        "event": "SHORTAGE_LOGGED_AND_CONTINUED",
                        "picked_qty": picked_qty,
                        "shortage_qty": shortage_qty,
                        "procurement_alert": True
                    }
                return True, event_data, tts_response
                
            # Normál sikeres darabszám bemondás
            parsed_qty = self._parse_hungarian_quantity(speech_clean)
            if parsed_qty == expected_qty or "kész" in speech_clean or "kesz" in speech_clean or "rendben" in speech_clean:
                tts_response = f"Rendben, {expected_qty} darab behelyezve a gyűjtődobozba."
                return True, {"event": "QUANTITY_VERIFIED", "quantity_picked": expected_qty}, tts_response
            else:
                tts_response = f"Eltérő mennyiség hallatszik. {expected_qty} darabot kértünk. Kérlek erősítsd meg a szedett mennyiséget!"
                return False, {"event": "QUANTITY_MISMATCH", "expected": expected_qty, "heard": operator_speech}, tts_response
                
        return False, {"event": "UNKNOWN_STEP"}, "Ismételd meg az utasítást!"

    def execute_tour(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Egy komplett szedési túra végrehajtása és naplózása"""
        order = payload.get("order", {})
        order_id = order.get("order_id", f"ORD-{datetime.datetime.now().strftime('%Y%m%d%H%M')}")
        customer = order.get("customer_name", "B2B Partner")
        operator_name = payload.get("operator_name", "Kovács István (Raktáros)")
        picking_mode = payload.get("picking_mode", self.picking_mode)
        verif_method = payload.get("verification_method", self.verification_method)
        shortage_strat = payload.get("shortage_strategy", self.shortage_strategy)
        
        raw_items = order.get("items", [])
        optimized_items = self._optimize_route(raw_items)
        simulated_dialogue = payload.get("simulated_voice_dialogue", [])
        
        tour_steps_log = []
        dialogue_idx = 0
        total_items_picked = 0
        total_items_shortage = 0
        item_results = []
        
        for item_idx, item in enumerate(optimized_items):
            shelf = item.get("shelf_location", "A-01-01")
            name = item.get("name", "Cikk")
            qty_ordered = int(item.get("quantity_ordered", 1))
            
            prompt_nav = f"Tétel {item_idx + 1}/{len(optimized_items)}: Menj a(z) {shelf} polchoz! Mondd az ellenőrző kódot!"
            
            # Polc azonosítás szimuláció
            loc_heard = "42"
            if dialogue_idx < len(simulated_dialogue):
                loc_heard = simulated_dialogue[dialogue_idx].get("operator_speech", "42")
                dialogue_idx += 1
            else:
                loc_heard = str(item.get("check_digit", "42"))
                
            ok_loc, loc_data, tts_qty = self._process_dialogue_step(item, "CONFIRM_LOCATION", loc_heard, verif_method, shortage_strat)
            
            # Darabszám nyugtázás szimuláció
            qty_heard = "kész"
            if dialogue_idx < len(simulated_dialogue):
                qty_heard = simulated_dialogue[dialogue_idx].get("operator_speech", f"{qty_ordered} kész")
                dialogue_idx += 1
            else:
                qty_heard = f"{qty_ordered} kész"
                
            ok_qty, qty_data, tts_next = self._process_dialogue_step(item, "CONFIRM_QUANTITY", qty_heard, verif_method, shortage_strat)
            
            picked = qty_ordered
            shortage = 0
            if "shortage_qty" in qty_data:
                picked = qty_data.get("picked_qty", 0)
                shortage = qty_data.get("shortage_qty", 0)
                
            total_items_picked += picked
            total_items_shortage += shortage
            
            item_results.append({
                "sku": item.get("sku"),
                "name": name,
                "shelf_location": shelf,
                "quantity_ordered": qty_ordered,
                "quantity_picked": picked,
                "shortage": shortage,
                "status": "COMPLETED" if shortage == 0 else "PARTIAL_SHORTAGE",
                "dialogue_history": [
                    {"system_prompt": prompt_nav, "operator_heard": loc_heard, "result": loc_data},
                    {"system_prompt": tts_qty, "operator_heard": qty_heard, "result": qty_data}
                ]
            })
            
        # Csomagolólevél és dobozcímke generálás
        box_barcode = f"BOX-{order_id[-4:]}-01"
        packing_slip = {
            "slip_number": f"SLIP-{order_id}",
            "order_id": order_id,
            "customer_name": customer,
            "delivery_address": order.get("delivery_address", "Kiszállítási cím"),
            "picking_mode": picking_mode,
            "packed_by": operator_name,
            "packed_at": datetime.datetime.now().isoformat(),
            "box_label": {
                "barcode": box_barcode,
                "carrier": "Trans-Sped Logisztika",
                "total_items": total_items_picked,
                "handling": "Törékeny épületgépészeti szerelvények"
            },
            "items": item_results
        }
        
        # Tartós adatbázis naplózás
        summary = self._persist_tour_log(order_id, operator_name, packing_slip, total_items_picked, total_items_shortage)
        
        final_audio_prompt = f"Gratulálok! A(z) {order_id} szedési túra befejeződött. {total_items_picked} tétel kiszedve. A(z) {box_barcode} számú dobozcímke kinyomtatva a csomagolóasztalon!"
        
        return {
            "status": "success",
            "module_id": "08_raktari_ketkezes_hangvezerles_hands_free",
            "processed_at": datetime.datetime.now().isoformat(),
            "order_id": order_id,
            "operator": operator_name,
            "picking_mode": picking_mode,
            "verification_method": verif_method,
            "shortage_strategy": shortage_strat,
            "tour_status": "COMPLETED",
            "metrics": {
                "total_lines": len(optimized_items),
                "total_items_picked": total_items_picked,
                "total_shortage_items": total_items_shortage,
                "accuracy_percent": 100.0 if total_items_shortage == 0 else round((total_items_picked / max(1, total_items_picked + total_items_shortage)) * 100, 1),
                "estimated_time_seconds": len(optimized_items) * 45
            },
            "final_voice_prompt": final_audio_prompt,
            "packing_slip": packing_slip,
            "warehouse_summary": summary
        }

    def _persist_tour_log(self, order_id: str, operator: str, slip: Dict[str, Any], picked: int, shortage: int) -> Dict[str, Any]:
        """Szedési túra elmentése a raktári naplóba"""
        os.makedirs(os.path.dirname(self.warehouse_log_path), exist_ok=True)
        records = []
        if os.path.exists(self.warehouse_log_path):
            try:
                with open(self.warehouse_log_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        records = data
                    elif isinstance(data, dict) and "tours" in data:
                        records = data.get("tours", [])
            except Exception:
                records = []
                
        new_tour = {
            "tour_id": f"TOUR-{order_id}",
            "order_id": order_id,
            "operator": operator,
            "completed_at": datetime.datetime.now().isoformat(),
            "items_picked": picked,
            "items_shortage": shortage,
            "slip_number": slip.get("slip_number")
        }
        records.append(new_tour)
        
        tot_picked = sum(r.get("items_picked", 0) for r in records)
        tot_short = sum(r.get("items_shortage", 0) for r in records)
        
        db_payload = {
            "last_updated": datetime.datetime.now().isoformat(),
            "total_completed_tours": len(records),
            "warehouse_kpi": {
                "total_items_picked_hands_free": tot_picked,
                "total_shortages_detected": tot_short,
                "average_speed_lines_per_hour": 58
            },
            "tours": records
        }
        
        with open(self.warehouse_log_path, "w", encoding="utf-8") as f:
            json.dump(db_payload, f, indent=2, ensure_ascii=False)
            
        return db_payload["warehouse_kpi"]

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fő belépési pont"""
        return self.execute_tour(payload)

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Szabványos hub belépési pont"""
    handler = WarehouseVoicePickingHandler(config)
    return handler.execute(payload)

if __name__ == "__main__":
    test_sample = {
        "order": {
            "order_id": "ORD-TEST-01",
            "customer_name": "Teszt Vevő",
            "items": [
                {"sku": "PUMP-01", "name": "Keringető szivattyú", "quantity_ordered": 2, "shelf_location": "B-02", "check_digit": "42"}
            ]
        }
    }
    res = run(test_sample)
    print(json.dumps(res, indent=2, ensure_ascii=False))