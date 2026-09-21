"""
Kereskedelmi Anomália Detektálás (Árrészuhanás Figyelő & Circuit Breaker)
Modul: 10_kereskedelmi_anomalia_detektalas_arreszu
"""

import os
import sys
import json
import datetime
from typing import Dict, Any, List, Optional

class CommercialAnomalyCircuitBreakerHandler:
    """
    Valós idejű kereskedelmi árrésvédelmi védőpajzs (Circuit Breaker).
    Kiszűri a ráfizetéses tételeket, minimális haszonkulcs alatti eladásokat,
    a kedvezményhalmozást és a gépelési hibákat, intelligensen zárolja a folyamatot,
    és 1-kattintásos / PIN-kódos vezetői feloldást biztosít.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.service_mode = self.config.get("service_mode", "mock")
        self.min_margin_percent = float(self.config.get("minimum_margin_percent", 8.0))
        self.max_cumulative_discount = float(self.config.get("max_cumulative_discount_percent", 35.0))
        self.circuit_breaker_policy = self.config.get("circuit_breaker_policy", "loss_threshold_adaptive")
        self.hard_block_loss_threshold = float(self.config.get("hard_block_loss_threshold_huf", 50000.0))
        self.fat_finger_multiplier = float(self.config.get("fat_finger_quantity_multiplier", 10.0))
        self.catalog_db_path = self.config.get("catalog_db_path", "data/termektorzs_katalogus.json")
        self.anomaly_log_path = self.config.get("anomaly_log_path", "data/arresvedelem_naplo.json")

    def _audit_item(self, item: Dict[str, Any], order: Dict[str, Any]) -> Dict[str, Any]:
        """Egyetlen megrendelt tétel árrés és anomália vizsgálata"""
        sku = item.get("sku", "UNKNOWN-SKU")
        name = item.get("product_name", sku)
        qty = int(item.get("quantity", 1))
        unit_cost = float(item.get("unit_cost_huf", 0))
        offered_price = float(item.get("offered_price_huf", 0))
        list_price = float(item.get("list_price_huf", offered_price))
        discounts = item.get("applied_discounts", [])
        
        # Pénzügyi kalkulációk
        unit_profit = offered_price - unit_cost
        total_profit = unit_profit * qty
        margin_pct = round((unit_profit / max(1.0, offered_price)) * 100.0, 2) if offered_price > 0 else -100.0
        cumulative_discount = round(((list_price - offered_price) / max(1.0, list_price)) * 100.0, 1) if list_price > 0 else 0.0
        
        item_anomalies = []
        
        # 1. Anomália: Ráfizetéses eladás (Negatív árrés)
        if offered_price < unit_cost:
            loss_per_unit = abs(unit_profit)
            total_loss = loss_per_unit * qty
            item_anomalies.append({
                "code": "CRITICAL_NEGATIVE_MARGIN",
                "severity": "CRITICAL",
                "title": "Ráfizetéses Eladás (Beszerzési Ár Alatti Értékesítés)",
                "calculated_loss_huf": total_loss,
                "description": f"Az eladási ár ({offered_price:,.0f} Ft) alacsonyabb a beszerzési önköltségnél ({unit_cost:,.0f} Ft). Tételenkénti veszteség: {loss_per_unit:,.0f} Ft, összesen: {total_loss:,.0f} Ft!".replace(",.0f", ":,.0f")
            })
            
        # 2. Anomália: Minimális elvárt haszonkulcs alatti tétel
        elif margin_pct < self.min_margin_percent:
            margin_shortfall_huf = round(((self.min_margin_percent / 100.0) * offered_price - unit_profit) * qty)
            item_anomalies.append({
                "code": "SUB_MINIMUM_MARGIN_FLOOR",
                "severity": "HIGH" if margin_shortfall_huf >= 20000 else "MEDIUM",
                "title": "Minimális Árréshatár Megsértése",
                "calculated_loss_huf": max(0, margin_shortfall_huf),
                "description": f"A realizált árrés ({margin_pct}%) elmarad a céges minimumtól ({self.min_margin_percent}%). Elmaradt minimális haszon: {margin_shortfall_huf:,.0f} Ft.".replace(",.0f", ":,.0f")
            })
            
        # 3. Anomália: Kirívó Kedvezményhalmozás
        if cumulative_discount > self.max_cumulative_discount:
            item_anomalies.append({
                "code": "EXCESSIVE_DISCOUNT_STACKING",
                "severity": "HIGH",
                "title": "Veszélyes Kedvezményhalmozás",
                "calculated_loss_huf": round(((cumulative_discount - self.max_cumulative_discount) / 100.0) * list_price * qty),
                "description": f"A kumulált engedmény ({cumulative_discount}%) meghaladja a maximális korlátot ({self.max_cumulative_discount}%). Levont tételek: {discounts}."
            })
            
        # 4. Anomália: 0 Ft-os tétel vagy extrém mennyiség
        if offered_price <= 0:
            item_anomalies.append({
                "code": "ZERO_PRICE_FAT_FINGER",
                "severity": "CRITICAL",
                "title": "Nulla Forintos Eladási Ár (Gépelési Hiba)",
                "calculated_loss_huf": unit_cost * qty,
                "description": "Az eladási ár 0 Ft! Azonnali adatbázis vagy gépelési hiba kizárása szükséges."
            })
            
        return {
            "sku": sku,
            "product_name": name,
            "quantity": qty,
            "unit_cost_huf": unit_cost,
            "offered_price_huf": offered_price,
            "list_price_huf": list_price,
            "unit_profit_huf": unit_profit,
            "total_profit_huf": total_profit,
            "margin_percent": margin_pct,
            "cumulative_discount_percent": cumulative_discount,
            "discounts_applied": discounts,
            "has_anomaly": len(item_anomalies) > 0,
            "anomalies": item_anomalies
        }

    def _determine_circuit_breaker(
        self,
        order: Dict[str, Any],
        audited_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Zárolási és beavatkozási döntéshozatal (Circuit Breaker Policy)"""
        all_anomalies = []
        total_calculated_loss = 0.0
        has_critical = False
        
        for it in audited_items:
            for anom in it.get("anomalies", []):
                all_anomalies.append(anom)
                total_calculated_loss += anom.get("calculated_loss_huf", 0)
                if anom.get("severity") == "CRITICAL":
                    has_critical = True
                    
        if len(all_anomalies) == 0:
            status = "CLEAR_PROCEED"
            status_label = "Minden tétel szabályos – Jóváhagyva"
            dispatch_blocked = False
            action_required = "Automatikus raktári kiadás és számlázás engedélyezve."
        else:
            if self.circuit_breaker_policy == "always_hard_block":
                status = "HARD_CIRCUIT_BREAKER_ACTIVE"
                status_label = "KEMÉNY ZÁRLAT – Folyamat Leállítva"
                dispatch_blocked = True
                action_required = "Rendelés zárolva! Vezetői jóváhagyás szükséges a folytatáshoz."
            elif self.circuit_breaker_policy == "warning_only":
                status = "WARNING_PROCEED_WITH_FLAG"
                status_label = "Figyelmeztető Zászló – Folyamat Nem Áll Le"
                dispatch_blocked = False
                action_required = "Figyelmeztetés a bizonylaton rögzítve, szállítás engedélyezve."
            else:  # loss_threshold_adaptive
                if has_critical or total_calculated_loss >= self.hard_block_loss_threshold:
                    status = "HARD_CIRCUIT_BREAKER_ACTIVE"
                    status_label = f"KEMÉNY ZÁRLAT! Veszteség ({total_calculated_loss:,.0f} Ft) meghaladja a küszöböt ({self.hard_block_loss_threshold:,.0f} Ft)".replace(",.0f", ":,.0f")
                    dispatch_blocked = True
                    action_required = "SZÁLLÍTÁS ÉS SZÁMLÁZÁS LEÁLLÍTVA! Pénzügyi igazgatói jóváhagyás kötelező."
                else:
                    status = "WARNING_PROCEED_WITH_FLAG"
                    status_label = f"Alacsony kockázatú anomália ({total_calculated_loss:,.0f} Ft veszteség) – Folytatás engedélyezve".replace(",.0f", ":,.0f")
                    dispatch_blocked = False
                    action_required = "Audit figyelmeztetés rögzítve a számlán, szállítás engedélyezve."
                    
        return {
            "circuit_breaker_status": status,
            "status_label": status_label,
            "dispatch_blocked": dispatch_blocked,
            "total_anomalies_count": len(all_anomalies),
            "total_calculated_loss_huf": round(total_calculated_loss),
            "action_required": action_required,
            "anomalies_summary": all_anomalies
        }

    def _generate_manager_override(self, order: Dict[str, Any], breaker: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """1-kattintásos és PIN kódos vezetői feloldási csomag generálása"""
        if not breaker["dispatch_blocked"]:
            return None
            
        order_id = order.get("order_id", "ORD-UNKNOWN")
        cust = order.get("customer_name", "Megrendelő")
        loss = breaker["total_calculated_loss_huf"]
        
        approve_token = f"AUTH-APPROVE-{order_id}-2026"
        reject_token = f"AUTH-REJECT-{order_id}-2026"
        
        return {
            "override_available": True,
            "urgency": "IMMEDIATE_CFO_DECISION",
            "approver_role": "Pénzügyi Igazgató (CFO) / Ügyvezető",
            "approval_tokens": {
                "approve_token": approve_token,
                "reject_token": reject_token,
                "web_pin_code": "8842"
            },
            "one_click_actions": {
                "one_click_approve_url": f"https://hub.profigepesz.hu/api/v1/override?token={approve_token}&action=APPROVE",
                "one_click_reject_url": f"https://hub.profigepesz.hu/api/v1/override?token={reject_token}&action=REJECT"
            },
            "alert_broadcast": {
                "telegram_alert": f"ÁRRÉSVÉDELMI VÉSZJELZÉS: {cust} ({order_id}) zárolva! Várható árrésveszteség: {loss:,.0f} Ft! Feloldás: https://hub.profigepesz.hu/api/v1/override?token={approve_token}".replace(",.0f", ":,.0f"),
                "dashboard_banner": f"CIRCUIT BREAKER AKTÍV: {order_id} szállítás zárolva!"
            }
        }

    def audit_single_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Egyetlen rendelés komplett vizsgálata"""
        items = order.get("items", [])
        audited_items = []
        for it in items:
            audited_items.append(self._audit_item(it, order))
            
        tot_rev = sum(it["offered_price_huf"] * it["quantity"] for it in audited_items)
        tot_cost = sum(it["unit_cost_huf"] * it["quantity"] for it in audited_items)
        tot_prof = sum(it["total_profit_huf"] for it in audited_items)
        avg_margin = round((tot_prof / max(1.0, tot_rev)) * 100.0, 2) if tot_rev > 0 else 0.0
        
        breaker = self._determine_circuit_breaker(order, audited_items)
        override_pkg = self._generate_manager_override(order, breaker)
        
        return {
            "order_id": order.get("order_id"),
            "customer_name": order.get("customer_name"),
            "customer_tier": order.get("customer_tier", "BRONZE"),
            "order_date": order.get("order_date"),
            "audited_at": datetime.datetime.now().isoformat(),
            "totals": {
                "total_revenue_huf": tot_rev,
                "total_cost_huf": tot_cost,
                "total_profit_huf": tot_prof,
                "overall_margin_percent": avg_margin
            },
            "circuit_breaker": breaker,
            "manager_override": override_pkg,
            "audited_items": audited_items
        }

    def _persist_audit_log(self, audited_orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Audit eredmények tartós mentése"""
        os.makedirs(os.path.dirname(self.anomaly_log_path), exist_ok=True)
        existing = []
        if os.path.exists(self.anomaly_log_path):
            try:
                with open(self.anomaly_log_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        existing = data
                    elif isinstance(data, dict) and "orders" in data:
                        existing = data.get("orders", [])
            except Exception:
                existing = []
                
        idx_map = {o.get("order_id"): i for i, o in enumerate(existing)}
        for ao in audited_orders:
            oid = ao.get("order_id")
            if oid in idx_map:
                existing[idx_map[oid]] = ao
            else:
                existing.append(ao)
                idx_map[oid] = len(existing) - 1
                
        blocked_count = sum(1 for o in existing if o.get("circuit_breaker", {}).get("dispatch_blocked"))
        saved_margin = sum(o.get("circuit_breaker", {}).get("total_calculated_loss_huf", 0) for o in existing if o.get("circuit_breaker", {}).get("dispatch_blocked"))
        
        db_payload = {
            "last_updated": datetime.datetime.now().isoformat(),
            "total_orders_audited": len(existing),
            "protection_summary": {
                "blocked_orders_count": blocked_count,
                "total_margin_loss_prevented_huf": round(saved_margin),
                "circuit_breaker_active": blocked_count > 0
            },
            "orders": existing
        }
        
        with open(self.anomaly_log_path, "w", encoding="utf-8") as f:
            json.dump(db_payload, f, indent=2, ensure_ascii=False)
            
        return db_payload["protection_summary"]

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fő belépési pont"""
        action = payload.get("action", "AUDIT_TRANSACTIONS")
        
        # Vezetői feloldási token kezelése
        if action == "OVERRIDE_TRANSACTION":
            token = payload.get("token", "")
            pin = payload.get("pin_code", "")
            order_id = payload.get("order_id", "")
            if token.startswith("AUTH-APPROVE") or pin == "8842":
                return {
                    "status": "success",
                    "order_id": order_id,
                    "override_status": "APPROVED_BY_EXECUTIVE",
                    "dispatch_unblocked": True,
                    "message": f"A(z) {order_id} megrendelés feloldva! Számlázás és árukiadás engedélyezve cégvezetői jóváhagyással."
                }
            else:
                return {
                    "status": "error",
                    "order_id": order_id,
                    "message": "Érvénytelen token vagy PIN kód! A zárolás érvényben marad."
                }
                
        orders_input = []
        if "orders" in payload and isinstance(payload["orders"], list):
            orders_input = payload["orders"]
        elif "order" in payload and isinstance(payload["order"], dict):
            orders_input = [payload["order"]]
        elif "sample_data" in payload and isinstance(payload["sample_data"], dict):
            orders_input = [payload["sample_data"]]
        else:
            orders_input = [payload]
            
        results = []
        for o in orders_input:
            results.append(self.audit_single_order(o))
            
        summary = self._persist_audit_log(results)
        blocked_orders = [r for r in results if r["circuit_breaker"]["dispatch_blocked"]]
        
        return {
            "status": "success",
            "module_id": "10_kereskedelmi_anomalia_detektalas_arreszu",
            "processed_at": datetime.datetime.now().isoformat(),
            "orders_audited_count": len(results),
            "protection_summary": summary,
            "blocked_orders_count": len(blocked_orders),
            "immediate_actions": [
                {
                    "order_id": r["order_id"],
                    "customer_name": r["customer_name"],
                    "status": r["circuit_breaker"]["circuit_breaker_status"],
                    "calculated_loss_huf": r["circuit_breaker"]["total_calculated_loss_huf"],
                    "dispatch_blocked": r["circuit_breaker"]["dispatch_blocked"],
                    "override_tokens": r["manager_override"]["approval_tokens"] if r["manager_override"] else None,
                    "one_click_url": r["manager_override"]["one_click_actions"]["one_click_approve_url"] if r["manager_override"] else None
                }
                for r in blocked_orders
            ],
            "audited_orders": results
        }

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Szabványos hub belépési pont"""
    handler = CommercialAnomalyCircuitBreakerHandler(config)
    return handler.execute(payload)

if __name__ == "__main__":
    sample = {
        "orders": [
            {
                "order_id": "ORD-SAMPLE",
                "customer_name": "Minta Cég",
                "items": [
                    {"sku": "PUMP-01", "quantity": 1, "unit_cost_huf": 100000, "offered_price_huf": 80000}
                ]
            }
        ]
    }
    res = run(sample)
    print(json.dumps(res, indent=2, ensure_ascii=False))