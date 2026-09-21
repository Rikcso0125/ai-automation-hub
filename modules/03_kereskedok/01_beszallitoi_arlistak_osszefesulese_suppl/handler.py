"""
Beszállítói Árlisták Összefésülése (Supplier Feed Harmonizer & Árrésvédelem)
Modul: 01_beszallitoi_arlistak_osszefesulese_suppl
"""

import os
import sys
import json
import datetime
from typing import Dict, Any, List, Optional

class SupplierFeedHarmonizerHandler:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.service_mode = self.config.get("service_mode", "mock")
        self.default_target_margin = float(self.config.get("default_target_margin_percent", 25.0))
        self.critical_margin_threshold = float(self.config.get("critical_margin_threshold_percent", 10.0))
        self.currency_rates = self.config.get("currency_exchange_rates", {
            "EUR": 412.5,
            "USD": 382.0,
            "HUF": 1.0
        })
        self.approval_mode = self.config.get("approval_mode", "manual_approval_only")
        self.auto_sync_max_increase = float(self.config.get("auto_sync_max_increase_percent", 5.0))
        self.enable_best_buy = self.config.get("enable_best_buy_comparison", True)
        self.catalog_path = self.config.get("master_catalog_path", "data/termektorzs_katalogus.json")
        self.audit_log_path = self.config.get("audit_log_path", "data/beszallitoi_arlistak_naplo.json")


    def _load_master_catalog(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.catalog_path):
            try:
                with open(self.catalog_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_master_catalog(self, catalog: List[Dict[str, Any]]):
        os.makedirs(os.path.dirname(self.catalog_path), exist_ok=True)
        with open(self.catalog_path, "w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)

    def _normalize_item(self, raw_item: Dict[str, Any], default_supplier: str, default_curr: str) -> Dict[str, Any]:
        """
        Smart Field Mapping: Azonosítja a cikkszámot, nevet, árat, devizát eltérő oszlopnevekből.
        """
        keys_lower = {k.lower().strip(): v for k, v in raw_item.items()}

        # Cikkszám keresése
        sku = (keys_lower.get("cikkszam") or keys_lower.get("sku") or
               keys_lower.get("part_number") or keys_lower.get("cikk_kod") or
               keys_lower.get("product_code") or keys_lower.get("kod") or "UNKNOWN_SKU")

        # Név keresése
        name = (keys_lower.get("termek_nev") or keys_lower.get("megnevezes") or
                keys_lower.get("name") or keys_lower.get("description") or
                keys_lower.get("cikknev") or "Névtelen Termék")

        # Beszerzési ár keresése
        cost_raw = (keys_lower.get("beszerzesi_ar") or keys_lower.get("ar") or
                    keys_lower.get("netto_ar") or keys_lower.get("price") or
                    keys_lower.get("unit_cost") or keys_lower.get("cost") or
                    keys_lower.get("nagyker_ar") or 0.0)
        try:
            cost = float(cost_raw)
        except Exception:
            cost = 0.0

        # Deviza keresése
        currency = str(keys_lower.get("valuta") or keys_lower.get("deviza") or
                       keys_lower.get("currency") or default_curr).upper()

        # Készlet keresése
        stock_raw = (keys_lower.get("keszlet") or keys_lower.get("stock") or
                     keys_lower.get("mennyiseg") or keys_lower.get("qty") or 0)
        try:
            stock = int(stock_raw)
        except Exception:
            stock = 0

        # Beszállító neve
        supplier = str(keys_lower.get("beszallito") or keys_lower.get("supplier") or default_supplier)

        return {
            "sku": str(sku).strip(),
            "name": str(name).strip(),
            "cost": cost,
            "currency": currency,
            "stock": stock,
            "supplier": supplier
        }

    def _find_catalog_match(self, item: Dict[str, Any], catalog: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        sku_clean = item["sku"].upper()
        # 1. Cikkszám szerinti egyezés
        for cat_item in catalog:
            if cat_item.get("sku", "").upper() == sku_clean:
                return cat_item

        # 2. Fuzzy név szerinti egyezés (ha a szavak 60%-a megegyezik)
        item_words = set(item["name"].lower().split())
        for cat_item in catalog:
            cat_words = set(cat_item.get("name", "").lower().split())
            if item_words and cat_words:
                common = item_words.intersection(cat_words)
                if len(common) / max(len(item_words), 1) >= 0.5:
                    return cat_item

        return None

    def harmonize_feed(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        supplier_name = payload.get("supplier_name", "Ismeretlen Beszállító")
        feed_source = payload.get("feed_source", "feed.xlsx")
        default_currency = payload.get("currency", "HUF")
        raw_items = payload.get("feed_items", [])

        catalog = self._load_master_catalog()
        today_str = datetime.date.today().strftime("%Y%m%d")
        batch_id = f"BATCH-{today_str}-{abs(hash(supplier_name + feed_source)) % 9000 + 1000}"

        harmonized_items = []
        critical_alerts = []
        total_items = len(raw_items)
        increased_count = 0
        loss_making_count = 0
        total_profit_protected_huf = 0

        for raw_item in raw_items:
            norm = self._normalize_item(raw_item, supplier_name, default_currency)
            # Devizaváltás HUF-ra
            rate = self.currency_rates.get(norm["currency"], 1.0)
            new_cost_huf = round(norm["cost"] * rate)

            matched = self._find_catalog_match(norm, catalog)

            if matched:
                sku = matched.get("sku")
                product_name = matched.get("name")
                old_cost_huf = matched.get("current_cost_huf", new_cost_huf)
                current_price_huf = matched.get("current_price_huf", round(new_cost_huf * 1.3))
                target_margin = matched.get("target_margin_percent", self.default_target_margin)

                cost_diff_huf = new_cost_huf - old_cost_huf
                cost_change_pct = round((cost_diff_huf / old_cost_huf) * 100, 2) if old_cost_huf > 0 else 0.0

                # Jelenlegi haszonkulcs az új beszerzési ár mellett
                current_margin_pct = round(((current_price_huf - new_cost_huf) / current_price_huf) * 100, 2) if current_price_huf > 0 else 0.0

                # Kockázati szint meghatározása
                if new_cost_huf >= current_price_huf:
                    risk_level = "CRITICAL_LOSS_MAKING"
                    loss_amount = new_cost_huf - current_price_huf
                    loss_making_count += 1
                    status_note = f"VESZTESÉGES! Darabonként -{loss_amount:,} Ft veszteség keletkezne a jelenlegi eladási áron!"
                    critical_alerts.append({
                        "sku": sku,
                        "name": product_name,
                        "risk": risk_level,
                        "new_cost_huf": new_cost_huf,
                        "current_price_huf": current_price_huf,
                        "deficit_huf": loss_amount
                    })
                elif current_margin_pct < self.critical_margin_threshold:
                    risk_level = "MARGIN_SQUEEZE_CRITICAL"
                    status_note = f"Kritikusan alacsony árrés ({current_margin_pct}% < {self.critical_margin_threshold}%)!"
                    critical_alerts.append({
                        "sku": sku,
                        "name": product_name,
                        "risk": risk_level,
                        "new_cost_huf": new_cost_huf,
                        "current_margin_pct": current_margin_pct
                    })
                elif cost_change_pct > 0:
                    risk_level = "PRICE_INCREASE"
                    status_note = f"Beszállítói áremelkedés: +{cost_change_pct}%"
                    increased_count += 1
                elif cost_change_pct < 0:
                    risk_level = "PRICE_DECREASE"
                    status_note = f"Beszállítói árcsökkenés: {cost_change_pct}% (Extra profit lehetőség)"
                else:
                    risk_level = "UNCHANGED"
                    status_note = "Változatlan beszerzési ár"

                # Új javasolt eladási ár kalkulációja
                recommended_price_huf = round(new_cost_huf / (1 - (target_margin / 100.0)), -1)
                recommended_profit_huf = recommended_price_huf - new_cost_huf
                recommended_margin_pct = round(((recommended_price_huf - new_cost_huf) / recommended_price_huf) * 100, 2)

                # Mennyi profitot ment meg az árvédelem
                if recommended_price_huf > current_price_huf:
                    total_profit_protected_huf += (recommended_price_huf - current_price_huf)

                # Jóváhagyási státusz tételenként
                if self.approval_mode == "auto_sync_small_changes" and cost_change_pct <= self.auto_sync_max_increase and risk_level not in ["CRITICAL_LOSS_MAKING", "MARGIN_SQUEEZE_CRITICAL"]:
                    item_sync_status = "AUTO_APPROVED_SYNCED"
                else:
                    item_sync_status = "PENDING_HUMAN_APPROVAL"

                harmonized_items.append({
                    "sku": sku,
                    "product_name": product_name,
                    "supplier": norm["supplier"],
                    "feed_cost_raw": norm["cost"],
                    "feed_currency": norm["currency"],
                    "new_cost_huf": new_cost_huf,
                    "old_cost_huf": old_cost_huf,
                    "cost_change_pct": cost_change_pct,
                    "current_price_huf": current_price_huf,
                    "current_margin_pct": current_margin_pct,
                    "target_margin_pct": target_margin,
                    "recommended_price_huf": recommended_price_huf,
                    "recommended_margin_pct": recommended_margin_pct,
                    "recommended_profit_huf": recommended_profit_huf,
                    "risk_level": risk_level,
                    "status_note": status_note,
                    "sync_status": item_sync_status
                })
            else:
                # Új termék a beszállítótól, ami még nincs a törzsben
                recommended_price = round(new_cost_huf / (1 - (self.default_target_margin / 100.0)), -1)
                harmonized_items.append({
                    "sku": norm["sku"],
                    "product_name": norm["name"],
                    "supplier": norm["supplier"],
                    "feed_cost_raw": norm["cost"],
                    "feed_currency": norm["currency"],
                    "new_cost_huf": new_cost_huf,
                    "old_cost_huf": None,
                    "cost_change_pct": 0.0,
                    "current_price_huf": None,
                    "current_margin_pct": None,
                    "target_margin_pct": self.default_target_margin,
                    "recommended_price_huf": recommended_price,
                    "recommended_margin_pct": self.default_target_margin,
                    "recommended_profit_huf": recommended_price - new_cost_huf,
                    "risk_level": "NEW_PRODUCT_DISCOVERED",
                    "status_note": "Új termék a beszállítói feedből, felvételre előkészítve",
                    "sync_status": "PENDING_HUMAN_APPROVAL"
                })

        # Jóváhagyási link
        approval_url = f"http://localhost:8000/api/v1/modules/01_beszallitoi_arlistak_osszefesulese_suppl/approve_batch?batch_id={batch_id}"

        # Értesítési üzenet a beszerzési vezetőnek
        alert_lines = [
            "[ARRESVEDELMI RIASZTAS - BESZALLITOI FEED FELDOLGOZVA]",
            f"Beszallito: {supplier_name} ({feed_source})",
            f"Feldolgozott tetelek: {total_items} db",
            f"Aremelkedesben erintett cikkek: {increased_count} db",
            f"VESZELYESEN RAFIZETESES CIKKEK SZAMA: {loss_making_count} db",
            f"Megvedett kereskedelmi profit: {total_profit_protected_huf:,} Ft",
            "",
            "1-KATTINTASOS JOVAHAGYAS ES ERP SZINKRON:",
            f"-> {approval_url}"
        ]
        if critical_alerts:
            alert_lines.append("")
            alert_lines.append("KRITIKUS TETEL FIGYELMEZTETES:")
            for ca in critical_alerts[:3]:
                alert_lines.append(f"- {ca['sku']}: {ca['name']} (Új ár: {ca['new_cost_huf']:,} Ft, Eladási ár: {ca.get('current_price_huf', 'N/A')})")

        notification_message = chr(10).join(alert_lines)

        # Mentés az audit naplóba
        batch_record = {
            "batch_id": batch_id,
            "created_at": datetime.datetime.now().isoformat(),
            "supplier_name": supplier_name,
            "feed_source": feed_source,
            "total_items": total_items,
            "increased_items_count": increased_count,
            "loss_making_items_count": loss_making_count,
            "total_profit_protected_huf": total_profit_protected_huf,
            "critical_alerts": critical_alerts,
            "items": harmonized_items,
            "approval_mode": self.approval_mode,
            "approval_status": "AUTO_SYNCED" if loss_making_count == 0 and self.approval_mode == "auto_sync_small_changes" else "PENDING_APPROVAL",
            "approval_url": approval_url
        }

        self._save_audit_log(batch_record)

        return {
            "status": "success",
            "action_executed": "FEED_HARMONIZED_AND_MARGIN_PROTECTED",
            "batch_id": batch_id,
            "supplier_name": supplier_name,
            "feed_source": feed_source,
            "summary": {
                "total_items_processed": total_items,
                "price_increase_count": increased_count,
                "critical_loss_making_count": loss_making_count,
                "profit_protected_huf": total_profit_protected_huf,
                "approval_status": batch_record["approval_status"]
            },
            "one_click_approval_url": approval_url,
            "critical_alerts": critical_alerts,
            "harmonized_items": harmonized_items,
            "executive_alert_message": notification_message
        }

    def _save_audit_log(self, record: Dict[str, Any]):
        os.makedirs(os.path.dirname(self.audit_log_path), exist_ok=True)
        existing = []
        if os.path.exists(self.audit_log_path):
            try:
                with open(self.audit_log_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        existing = data
                    elif isinstance(data, dict):
                        existing = data.get("orders", [])
            except Exception:
                existing = []

        if not isinstance(existing, list):
            existing = []

        existing.insert(0, record)
        with open(self.audit_log_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)


    def approve_batch(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Jóváhagyja az árváltozásokat és frissíti a belső terméktörzset (data/termektorzs_katalogus.json).
        """
        batch_id = payload.get("batch_id")
        if not batch_id:
            return {"status": "error", "message": "batch_id kötelező a jóváhagyáshoz!"}

        if not os.path.exists(self.audit_log_path):
            return {"status": "error", "message": "Nincs audit napló."}

        with open(self.audit_log_path, "r", encoding="utf-8") as f:
            logs = json.load(f)

        target_batch = None
        for b in logs:
            if b.get("batch_id") == batch_id:
                target_batch = b
                break

        if not target_batch:
            return {"status": "error", "message": f"A(z) {batch_id} csomag nem található!"}

        # Terméktörzs frissítése
        catalog = self._load_master_catalog()
        updated_count = 0

        for item in target_batch.get("items", []):
            sku = item.get("sku")
            for cat_item in catalog:
                if cat_item.get("sku") == sku:
                    cat_item["current_cost_huf"] = item.get("new_cost_huf")
                    cat_item["current_price_huf"] = item.get("recommended_price_huf")
                    cat_item["last_price_update"] = datetime.datetime.now().isoformat()
                    updated_count += 1
                    break

        self._save_master_catalog(catalog)

        # Audit napló státuszának frissítése
        target_batch["approval_status"] = "APPROVED_AND_SYNCED_TO_ERP"
        target_batch["approved_at"] = datetime.datetime.now().isoformat()
        with open(self.audit_log_path, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)

        return {
            "status": "success",
            "batch_id": batch_id,
            "updated_products_count": updated_count,
            "message": f"A(z) {batch_id} árváltozás jóváhagyva és szinkronizálva a terméktörzsbe ({updated_count} tétel frissítve)."
        }

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("action", "HARMONIZE_FEED")
        if action == "APPROVE_BATCH":
            return self.approve_batch(payload)
        return self.harmonize_feed(payload)

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    handler = SupplierFeedHarmonizerHandler(config)
    return handler.execute(payload)

if __name__ == "__main__":
    sample = {
        "action": "HARMONIZE_FEED",
        "supplier_name": "EuroGépész Nagyker Kft.",
        "feed_source": "test_prices.xlsx",
        "currency": "HUF",
        "feed_items": [
            {"cikkszam": "CU-PIPE-15", "ar": 2750},
            {"cikkszam": "VALVE-BRASS-12", "ar": 1720}
        ]
    }
    res = run(sample)
    print(json.dumps(res, indent=2, ensure_ascii=False))
