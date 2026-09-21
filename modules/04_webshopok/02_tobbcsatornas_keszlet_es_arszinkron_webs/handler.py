# -*- coding: utf-8 -*-
"""
Module 4.02: Többcsatornás Készlet- és Árszinkron (Webshop + eMAG + Alza + POS)
Valós idejű készlet- és árszinkronizáció piacterek és bolti kasszák között.
Támogatja a választható készletpuffer stratégiákat (A-B-C),
a dinamikus árrésvédett árazást (A-B-C) és a POS szinkronizációt (A-B-C).
"""
import os
import sys
import json
import time
import datetime
from typing import Dict, Any, List, Optional

class MultiChannelSyncHandler:
    """Többcsatornás készlet- és árszinkron motor"""
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.service_mode = self.config.get("service_mode", "mock")
        self.buffer_mode = self.config.get("buffer_stock_mode", "fixed_buffer")  # fixed_buffer, dynamic_quota, realtime_lock
        self.buffer_threshold = int(self.config.get("buffer_threshold", 2))
        self.reservation_ttl = int(self.config.get("reservation_ttl_minutes", 15))
        self.pricing_mode = self.config.get("pricing_mode", "margin_protected")  # uniform, margin_protected, channel_rules
        self.min_floor_margin_pct = float(self.config.get("min_floor_margin_pct", 12.0))
        self.pos_sync_mode = self.config.get("pos_sync_mode", "hybrid")  # realtime_push, batch_periodic, hybrid
        self.low_stock_threshold = int(self.config.get("low_stock_threshold", 5))
        self.storage_path = self.config.get("storage_path", "data/tobbcsatornas_szinkron_naplo.json")
        
        # Belső központi termék- és készlettörzs (szimuláció)
        self.catalog = {
            "BOSCH-GSR-18V-55": {
                "sku": "BOSCH-GSR-18V-55",
                "name": "Bosch Professional GSR 18V-55 Akkus Fúrócsavarozó",
                "master_stock": 7,
                "reserved_stock": 0,
                "cost_net": 34000,
                "base_price_gross": 49990,
                "vat_rate": 0.27
            },
            "MAKITA-DHP-484": {
                "sku": "MAKITA-DHP-484",
                "name": "Makita DHP484Z Akkus Ütvefúró-csavarbehajtó",
                "master_stock": 2,
                "reserved_stock": 0,
                "cost_net": 45000,
                "base_price_gross": 64990,
                "vat_rate": 0.27
            },
            "DEWALT-DCD-796": {
                "sku": "DEWALT-DCD-796",
                "name": "DeWalt DCD796P2 Akkus Kefe Nélküli Fúrócsavarozó",
                "master_stock": 14,
                "reserved_stock": 1,
                "cost_net": 62000,
                "base_price_gross": 89990,
                "vat_rate": 0.27
            }
        }

    def calculate_stock_allocation(self, sku: str, total_available: int) -> Dict[str, Any]:
        """Készletelosztás kalkuláció a választott buffer stratégia szerint"""
        channels_stock = {}
        flags = []
        
        # 1. FIX PUFFER STRATÉGIA (A opció)
        if self.buffer_mode == "fixed_buffer":
            if total_available <= self.buffer_threshold:
                # Piactereken nullázás a túladás és a kötbér kivédésére
                channels_stock["webshop"] = max(0, total_available)
                channels_stock["pos"] = max(0, total_available)
                channels_stock["emag"] = 0
                channels_stock["alza"] = 0
                flags.append("BUFFER_ZEROED_ON_MARKETPLACES_OVERSOLD_PROTECTION")
            else:
                channels_stock["webshop"] = total_available
                channels_stock["pos"] = total_available
                channels_stock["emag"] = total_available
                channels_stock["alza"] = total_available
                
        # 2. DINAMIKUS KVÓTA STRATÉGIA (B opció)
        elif self.buffer_mode == "dynamic_quota":
            if total_available <= 1:
                channels_stock["webshop"] = total_available
                channels_stock["pos"] = total_available
                channels_stock["emag"] = 0
                channels_stock["alza"] = 0
            else:
                # 60% Webshop, 20% eMAG, 20% Alza, POS látja a teljes bolti készletet
                webshop_q = max(1, int(round(total_available * 0.6)))
                emag_q = max(0, int(round(total_available * 0.2)))
                alza_q = max(0, total_available - webshop_q - emag_q)
                channels_stock["webshop"] = webshop_q
                channels_stock["emag"] = emag_q
                channels_stock["alza"] = alza_q
                channels_stock["pos"] = total_available
            flags.append("DYNAMIC_QUOTA_DISTRIBUTION_APPLIED")
            
        # 3. VALÓS IDEJŰ ZÁROLÁS (C opció)
        elif self.buffer_mode == "realtime_lock":
            channels_stock["webshop"] = max(0, total_available)
            channels_stock["pos"] = max(0, total_available)
            channels_stock["emag"] = max(0, total_available)
            channels_stock["alza"] = max(0, total_available)
            flags.append(f"REALTIME_SUB_SECOND_LOCK_ACTIVE_{self.reservation_ttl}MIN_RESERVATION")
            
        return {
            "strategy": self.buffer_mode,
            "channels_stock": channels_stock,
            "flags": flags,
            "buffer_threshold": self.buffer_threshold
        }

    def calculate_channel_prices(self, sku: str, base_price_gross: float, cost_net: float) -> Dict[str, Any]:
        """Árképzés kalkuláció csatornánként a választott árazási mód szerint"""
        prices = {}
        margins = {}
        flags = []
        
        # 1. EGYSÉGES ÁR (A opció)
        if self.pricing_mode == "uniform":
            p = int(round(base_price_gross))
            prices = {"webshop": p, "pos": p, "emag": p, "alza": p}
            flags.append("UNIFORM_PRICE_ALL_CHANNELS")
            
        # 2. JUTALÉKKAL NÖVELT ÁRRÉSVÉDEDT ÁR (B opció)
        elif self.pricing_mode == "margin_protected":
            # eMAG átlagos jutalék: +16%, Alza: +14%
            p_web = int(round(base_price_gross))
            p_emag = int(round(base_price_gross * 1.16, -1))
            p_alza = int(round(base_price_gross * 1.14, -1))
            prices = {"webshop": p_web, "pos": p_web, "emag": p_emag, "alza": p_alza}
            flags.append("COMMISSION_ABSORBING_PRICE_PROTECTION_APPLIED")
            
        # 3. EGYEDI CSATORNA SZABÁLYZAT (C opció)
        elif self.pricing_mode == "channel_rules":
            # Pszichológiai 990 kerekítés + egyedi szorzók
            p_web = int(round(base_price_gross / 1000) * 1000 - 10)
            p_pos = p_web
            p_emag = int(round((base_price_gross * 1.15) / 1000) * 1000 - 10)
            p_alza = int(round((base_price_gross * 1.12) / 1000) * 1000 - 10)
            prices = {"webshop": p_web, "pos": p_pos, "emag": p_emag, "alza": p_alza}
            flags.append("CUSTOM_CHANNEL_RULES_WITH_PSYCHOLOGICAL_ROUNDING")
            
        # Árrés-ellenőrzés a nettó beszerzési árhoz képest
        for ch, p_gross in prices.items():
            p_net = p_gross / 1.27
            margin_pct = ((p_net - cost_net) / p_net * 100) if p_net > 0 else 0
            margins[ch] = round(margin_pct, 1)
            if margin_pct < self.min_floor_margin_pct:
                flags.append(f"WARNING_LOW_MARGIN_ON_{ch.upper()}_{margin_pct}%")
                
        return {
            "pricing_mode": self.pricing_mode,
            "prices_gross_huf": prices,
            "estimated_margins_pct": margins,
            "flags": flags
        }

    def process_sync_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Egy készlet- vagy ármódosító esemény szinkronizálása az összes csatornára"""
        start_time = time.time()
        event_type = payload.get("event_type", "ORDER_PLACED")
        source_channel = payload.get("source_channel", "webshop").lower()
        event_data = payload.get("event_data", {})
        
        sku = event_data.get("sku", "BOSCH-GSR-18V-55")
        qty = int(event_data.get("quantity", 1))
        
        # Termék keresése a törzsben
        item = self.catalog.get(sku, {
            "sku": sku,
            "name": event_data.get("product_name", f"Termék {sku}"),
            "master_stock": 10,
            "reserved_stock": 0,
            "cost_net": 30000,
            "base_price_gross": float(event_data.get("sale_price_gross", 49990)),
            "vat_rate": 0.27
        })
        
        # 1. Készlet módosítása az esemény szerint
        if event_type in ["ORDER_PLACED", "RECEIPT_CLOSED", "POS_SALE"]:
            item["master_stock"] = max(0, item["master_stock"] - qty)
        elif event_type in ["CHECKOUT_STARTED", "CART_RESERVE"]:
            item["reserved_stock"] = item["reserved_stock"] + qty
        elif event_type in ["STOCK_RECEIPT", "RESTOCK"]:
            item["master_stock"] = item["master_stock"] + qty
            
        available_stock = max(0, item["master_stock"] - item["reserved_stock"])
        
        # 2. Elosztás és árazás számítása
        stock_alloc = self.calculate_stock_allocation(sku, available_stock)
        price_alloc = self.calculate_channel_prices(sku, item["base_price_gross"], item["cost_net"])
        
        # 3. POS Szinkron mód kiértékelése
        pos_action = {}
        if source_channel == "pos" or event_type in ["RECEIPT_CLOSED", "POS_SALE"]:
            if self.pos_sync_mode == "realtime_push":
                pos_action = {
                    "mode": "realtime_push",
                    "status": "IMMEDIATE_BROADCAST_COMPLETED",
                    "broadcast_sla_ms": 115,
                    "message": "Fizikai kassza zárás után azonnali 3mp-en belüli leküldés lezárult."
                }
            elif self.pos_sync_mode == "batch_periodic":
                pos_action = {
                    "mode": "batch_periodic",
                    "status": "QUEUED_FOR_5MIN_BATCH",
                    "batch_scheduled_in_sec": 180,
                    "message": "POS eladás kötegelt sorba állítva, nap végi zárási jelentéssel egyeztetve."
                }
            elif self.pos_sync_mode == "hybrid":
                if available_stock <= self.low_stock_threshold:
                    pos_action = {
                        "mode": "hybrid_instant_escalation",
                        "status": "TRIGGERED_INSTANT_PUSH_DUE_TO_LOW_STOCK",
                        "broadcast_sla_ms": 140,
                        "message": f"Alacsony készlet ({available_stock} db <= {self.low_stock_threshold} db) miatt azonnali szinkron lefutott!"
                    }
                else:
                    pos_action = {
                        "mode": "hybrid_background",
                        "status": "QUEUED_FOR_ROUTINE_CYCLE",
                        "message": "Készletszint biztonságos, 5 perces ciklusban frissül."
                    }
                    
        # 4. Külső API csatornák szimulált válaszideje (<3 másodperc SLA)
        sync_channels = ["webshop", "emag", "alza", "pos"]
        target_channels = [ch for ch in sync_channels if ch != source_channel]
        
        dispatch_results = {}
        for ch in target_channels:
            dispatch_results[ch] = {
                "target": ch,
                "stock_pushed": stock_alloc["channels_stock"].get(ch, available_stock),
                "price_pushed_gross": price_alloc["prices_gross_huf"].get(ch, item["base_price_gross"]),
                "api_status": "200_OK",
                "latency_ms": 85 if ch == "webshop" else (145 if ch == "emag" else 130)
            }
            
        elapsed_ms = round((time.time() - start_time) * 1000 + 45, 1)
        is_sla_met = elapsed_ms < 3000
        
        result = {
            "sync_event_id": f"SYNC-{int(time.time()*1000)}",
            "timestamp": datetime.datetime.now().isoformat(),
            "event_type": event_type,
            "source_channel": source_channel,
            "sku": sku,
            "product_name": item["name"],
            "quantity_affected": qty,
            "inventory_state": {
                "master_stock": item["master_stock"],
                "reserved_stock": item["reserved_stock"],
                "available_stock": available_stock,
                "channel_visibility": stock_alloc["channels_stock"]
            },
            "pricing_state": {
                "pricing_mode": self.pricing_mode,
                "channel_prices_gross": price_alloc["prices_gross_huf"],
                "channel_margins_pct": price_alloc["estimated_margins_pct"]
            },
            "buffer_strategy_applied": stock_alloc["strategy"],
            "pos_sync_status": pos_action,
            "dispatch_results": dispatch_results,
            "execution_sla": {
                "elapsed_ms": elapsed_ms,
                "target_sla_ms": 3000,
                "sla_met": is_sla_met
            },
            "system_flags": stock_alloc["flags"] + price_alloc["flags"]
        }
        
        self._log_sync_event(result)
        return result

    def _log_sync_event(self, entry: Dict[str, Any]) -> None:
        """Audit napló perzisztálása"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        existing = []
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = []
        existing.append(entry)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(existing[-100:], f, indent=2, ensure_ascii=False)

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fő végrehajtó metódus"""
        sync_result = self.process_sync_event(payload)
        return {
            "status": "success",
            "module_id": "02_tobbcsatornas_keszlet_es_arszinkron_webs",
            "processed_at": datetime.datetime.now().isoformat(),
            "sync_result": sync_result
        }

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Szabványos hub belépési pont"""
    effective_config = dict(config or {})
    if "config" in payload and isinstance(payload["config"], dict):
        effective_config.update(payload["config"])
        
    handler = MultiChannelSyncHandler(effective_config)
    return handler.execute(payload)

if __name__ == "__main__":
    sample = {
        "event_type": "ORDER_PLACED",
        "source_channel": "emag",
        "event_data": {
            "sku": "BOSCH-GSR-18V-55",
            "quantity": 1,
            "sale_price_gross": 54990
        }
    }
    res = run(sample)
    print(json.dumps(res, indent=2, ensure_ascii=False))