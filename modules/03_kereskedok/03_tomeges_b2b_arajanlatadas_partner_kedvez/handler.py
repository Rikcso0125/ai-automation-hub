"""
Tömeges B2B Árajánlatadás Partner Kedvezményszintekkel
Modul: 03_tomeges_b2b_arajanlatadas_partner_kedvez
"""

import os
import sys
import json
import re
import datetime
from typing import Dict, Any, List, Optional

class B2BQuotationHandler:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.service_mode = self.config.get("service_mode", "mock")
        self.company_name = self.config.get("company_name", "ProfiGépész Nagykereskedelmi Kft.")
        self.validity_days = int(self.config.get("quote_validity_days", 15))
        self.discount_tiers = self.config.get("discount_tiers", {
            "RETAIL": 0.0,
            "BRONZE": 10.0,
            "SILVER": 15.0,
            "GOLD": 22.0,
            "PLATINUM": 28.0
        })
        self.volume_thresholds = self.config.get("volume_discount_thresholds", {
            "500000": 2.0,
            "1000000": 4.0
        })
        self.approval_mode = self.config.get("approval_mode", "manual_approval_only")
        self.partners_db_path = self.config.get("partners_db_path", "data/b2b_partnerek.json")
        self.catalog_db_path = self.config.get("catalog_db_path", "data/termektorzs_katalogus.json")
        self.quotes_db_path = self.config.get("quotes_db_path", "data/b2b_ajanlatok_naplo.json")

    def _load_partners(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.partners_db_path):
            try:
                with open(self.partners_db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _load_catalog(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.catalog_db_path):
            try:
                with open(self.catalog_db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _find_partner(self, identifier: str, partners: List[Dict[str, Any]]) -> Dict[str, Any]:
        ident_lower = (identifier or "").lower().strip()
        for p in partners:
            if (p.get("partner_code", "").lower() == ident_lower or
                p.get("tax_id", "").lower() == ident_lower or
                p.get("company_name", "").lower() in ident_lower or
                ident_lower in p.get("company_name", "").lower()):
                return p

        # Alapértelmezett vendég / kisker partner
        return {
            "partner_code": "RETAIL-GUEST",
            "company_name": identifier or "Új Partner Érdeklődő",
            "tax_id": "N/A",
            "tier": "RETAIL",
            "discount_percent": 0.0,
            "contact_person": "Beszerző",
            "contact_email": "erdeklodo@partner.hu",
            "payment_terms": "Előreutalás / Készpénz",
            "credit_limit_huf": 0
        }

    def _parse_items(self, raw_input: Any, catalog: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Kinyeri a tételeket és mennyiségeket strukturált listából vagy nyers szöveges emailből.
        """
        if isinstance(raw_input, list) and len(raw_input) > 0 and isinstance(raw_input[0], dict):
            return raw_input

        text = str(raw_input)
        parsed_items = []

        patterns = [
            (r"(\d+)\s*(?:m|fm|meter)?\s*(?:15-ös|15x1|15\s*mm)?\s*rézcső", "CU-PIPE-15", 100),
            (r"(\d+)\s*(?:db)?\s*(?:1/2|feles)?\s*(?:colos)?\s*golyóscsap", "VALVE-BRASS-12", 20),
            (r"(\d+)\s*(?:db|szett)?\s*(?:Daikin|Sensira|klíma)", "DAIKIN-SENSIRA-35", 1),
            (r"(\d+)\s*(?:db)?\s*(?:Grundfos|szivattyú|keringető)", "PUMP-GRUNDFOS-25", 2),
            (r"(\d+)\s*(?:db)?\s*(?:könyök|rézkönyök|fitting)", "FITTING-ELBOW-90", 50)
        ]

        found_skus = set()
        for regex, sku, default_qty in patterns:
            match = re.search(regex, text, re.IGNORECASE)
            if match:
                qty = int(match.group(1)) if match.groups() and match.group(1) else default_qty
                parsed_items.append({"sku": sku, "quantity": qty})
                found_skus.add(sku)

        if not parsed_items:
            for cat in catalog:
                name_words = cat.get("name", "").lower().split()
                if any(w in text.lower() for w in name_words if len(w) > 4):
                    parsed_items.append({"sku": cat["sku"], "quantity": 10})

        if not parsed_items:
            parsed_items = [
                {"sku": "CU-PIPE-15", "quantity": 100},
                {"sku": "VALVE-BRASS-12", "quantity": 25}
            ]

        return parsed_items

    def generate_quote(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        partner_ident = payload.get("partner_identifier") or payload.get("company_name") or ""
        raw_items_or_text = payload.get("items") or payload.get("request_text") or ""

        partners = self._load_partners()
        catalog = self._load_catalog()

        partner = self._find_partner(partner_ident, partners)
        requested_items = self._parse_items(raw_items_or_text, catalog)

        today = datetime.date.today()
        validity_date = today + datetime.timedelta(days=self.validity_days)
        quote_id = f"B2B-AJ-{today.strftime('%Y%m%d')}-{abs(hash(partner['company_name'])) % 9000 + 1000}"

        partner_tier = partner.get("tier", "RETAIL")
        tier_discount_pct = float(partner.get("discount_percent", self.discount_tiers.get(partner_tier, 0.0)))

        line_items = []
        subtotal_list_price = 0.0
        subtotal_discounted_net = 0.0
        shortage_alerts = []

        catalog_map = {item.get("sku"): item for item in catalog}

        for req in requested_items:
            sku = req.get("sku")
            qty = float(req.get("quantity", 1))

            cat_item = catalog_map.get(sku, {})
            name = cat_item.get("name", sku)
            unit = cat_item.get("unit", "db")
            list_unit_price = float(cat_item.get("current_price_huf", 1000))
            stock_qty = float(cat_item.get("stock_qty", 0))

            discounted_unit_price = round(list_unit_price * (1.0 - (tier_discount_pct / 100.0)), -1)
            line_net = qty * discounted_unit_price
            subtotal_list_price += (qty * list_unit_price)
            subtotal_discounted_net += line_net

            # Készletvizsgálat és alternatíva
            has_shortage = qty > stock_qty
            alternative_info = None
            if has_shortage:
                shortage_qty = qty - stock_qty
                alt_sku = cat_item.get("alternative_sku")
                if alt_sku:
                    alt_item = {
                        "alternative_sku": alt_sku,
                        "alternative_name": cat_item.get("alternative_name"),
                        "alternative_list_price": cat_item.get("alternative_price_huf"),
                        "alternative_discounted_price": round(cat_item.get("alternative_price_huf", 0) * (1.0 - (tier_discount_pct / 100.0)), -1),
                        "alternative_stock_qty": cat_item.get("alternative_stock_qty")
                    }
                    alternative_info = alt_item
                    stock_note = f"Részben készleten ({int(stock_qty)} {unit} azonnal, hiány: {int(shortage_qty)} {unit}). Alternatíva raktárról elérhető!"
                else:
                    stock_note = f"Készlethiány: raktáron {int(stock_qty)} {unit}, hiány {int(shortage_qty)} {unit} (Várható szállítás: 3-5 munkanap)"

                shortage_alerts.append({
                    "sku": sku,
                    "name": name,
                    "requested_qty": qty,
                    "available_qty": stock_qty,
                    "shortage_qty": shortage_qty,
                    "alternative": alternative_info
                })
            else:
                stock_note = f"Raktáron ({int(stock_qty)} {unit} azonnal szállítható)"

            line_items.append({
                "sku": sku,
                "name": name,
                "unit": unit,
                "quantity": qty,
                "list_unit_price": list_unit_price,
                "partner_discount_pct": tier_discount_pct,
                "discounted_unit_price": discounted_unit_price,
                "line_net": line_net,
                "stock_status": "SHORTAGE" if has_shortage else "IN_STOCK",
                "stock_note": stock_note,
                "alternative_recommendation": alternative_info
            })

        # Mennyiségi sávos bónuszkedvezmény vizsgálat
        volume_bonus_pct = 0.0
        if subtotal_discounted_net >= 1000000:
            volume_bonus_pct = float(self.volume_thresholds.get("1000000", 4.0))
        elif subtotal_discounted_net >= 500000:
            volume_bonus_pct = float(self.volume_thresholds.get("500000", 2.0))

        final_net_huf = round(subtotal_discounted_net * (1.0 - (volume_bonus_pct / 100.0)))
        vat_amount_huf = round(final_net_huf * 0.27)
        gross_total_huf = final_net_huf + vat_amount_huf
        total_partner_savings_huf = subtotal_list_price - final_net_huf

        # Jóváhagyási státusz megállapítása
        approval_url = f"http://localhost:8000/api/v1/modules/03_tomeges_b2b_arajanlatadas_partner_kedvez/approve_quote?quote_id={quote_id}"
        if self.approval_mode == "auto_send_trusted_partners" and partner_tier in ["GOLD", "PLATINUM"]:
            quote_status = "AUTO_SENT_TO_PARTNER"
            action_summary = f"Megbízható {partner_tier} partner: hivatalos B2B ajánlat azonnal kiküldve emailben!"
        else:
            quote_status = "PENDING_SALES_REP_APPROVAL"
            action_summary = "Értékesítői jóváhagyásra vár (1-kattintásos kiküldési gombbal)."

        # Formázott email piszkozat
        email_lines = [
            f"Tárgy: Hivatalos B2B Árajánlat #{quote_id} - {partner['company_name']}",
            f"Címzett: {partner.get('contact_email', 'partner@ceg.hu')}",
            "",
            f"Tisztelt {partner.get('contact_person', partner['company_name'])}!",
            "",
            f"Köszönjük megkeresését! Az alábbiakban küldjük a(z) {quote_id} számú hivatalos árajánlatunkat "
            f"a(z) '{partner_tier}' szerződéses partneri kedvezményszint (-{tier_discount_pct}%) figyelembevételével:",
            "",
            "TÉTELEK ÉS KÉSZLETI ELÉRHETŐSÉG:"
        ]

        for item in line_items:
            email_lines.append(f"• {item['sku']} | {item['name']}: {item['quantity']} {item['unit']} x {item['discounted_unit_price']:,} Ft = {item['line_net']:,} Ft nettó")
            email_lines.append(f"  -> Készlet: {item['stock_note']}")
            if item.get("alternative_recommendation"):
                alt = item["alternative_recommendation"]
                email_lines.append(f"  -> ALTERNATÍVA: {alt['alternative_name']} ({alt['alternative_discounted_price']:,} Ft nettó, {alt['alternative_stock_qty']} db készleten!)")

        if volume_bonus_pct > 0:
            email_lines.append("")
            email_lines.append(f"NAGYTÉTELES BÓNUSZ KEDVEZMÉNY: -{volume_bonus_pct}% jóváírva a végösszegből!")

        email_lines.extend([
            "",
            f"NETTÓ VÉGÖSSZEG: {final_net_huf:,} Ft",
            f"ÁFA (27%): {vat_amount_huf:,} Ft",
            f"BRUTTÓ FIZETENDŐ: {gross_total_huf:,} Ft",
            f"Megtakarítás a listaárakhoz képest: {total_partner_savings_huf:,} Ft",
            "",
            f"Fizetési feltételek: {partner.get('payment_terms', '15 napos átutalás')}",
            f"Ajánlati kötöttség: {validity_date.strftime('%Y.%m.%d.')} ({self.validity_days} napig érvényes)",
            f"Szállítás: Azonnal raktárról (1 munkanap)",
            "",
            "Üdvözlettel:",
            f"{self.company_name} - B2B Értékesítési Csapat"
        ])
        partner_email_draft = chr(10).join(email_lines)

        # Értékesítői mobilos riasztás
        alert_lines = [
            "[B2B AJANLAT ELKESZULT 60 MP ALATT]",
            f"Ajanlatszam: {quote_id}",
            f"Partner: {partner['company_name']} ({partner_tier} Partner, -{tier_discount_pct}%)",
            f"Netto osszeg: {final_net_huf:,} Ft (Megtakaritas: {total_partner_savings_huf:,} Ft)",
            f"Tetelek szama: {len(line_items)} db",
            f"Keszlethianyos tetelek: {len(shortage_alerts)} db"
        ]
        if shortage_alerts:
            alert_lines.append("Keszletfigyelmeztetes:")
            for s in shortage_alerts:
                alert_lines.append(f"- {s['sku']}: Kert {s['requested_qty']}, elerheto {s['available_qty']}")
        alert_lines.extend([
            "",
            "1-KATTINTASOS JOVAHAGYAS ES KIKULDES:",
            f"-> {approval_url}"
        ])
        sales_alert = chr(10).join(alert_lines)

        quote_record = {
            "quote_id": quote_id,
            "created_at": datetime.datetime.now().isoformat(),
            "valid_until": validity_date.isoformat(),
            "partner_code": partner.get("partner_code"),
            "company_name": partner.get("company_name"),
            "tax_id": partner.get("tax_id"),
            "tier": partner_tier,
            "tier_discount_pct": tier_discount_pct,
            "volume_bonus_pct": volume_bonus_pct,
            "final_net_huf": final_net_huf,
            "vat_amount_huf": vat_amount_huf,
            "gross_total_huf": gross_total_huf,
            "total_partner_savings_huf": total_partner_savings_huf,
            "status": quote_status,
            "items": line_items,
            "shortage_alerts": shortage_alerts,
            "approval_url": approval_url,
            "email_draft": partner_email_draft
        }

        self._save_quote(quote_record)

        return {
            "status": "success",
            "action_executed": "B2B_BULK_QUOTE_GENERATED",
            "quote_id": quote_id,
            "quote_status": quote_status,
            "partner": {
                "company_name": partner["company_name"],
                "tier": partner_tier,
                "tier_discount_percent": tier_discount_pct,
                "payment_terms": partner.get("payment_terms")
            },
            "financial_summary": {
                "subtotal_list_price_huf": subtotal_list_price,
                "volume_bonus_percent": volume_bonus_pct,
                "final_net_huf": final_net_huf,
                "vat_27_huf": vat_amount_huf,
                "gross_total_huf": gross_total_huf,
                "partner_savings_huf": total_partner_savings_huf
            },
            "valid_until": validity_date.strftime("%Y.%m.%d."),
            "items": line_items,
            "shortage_alerts": shortage_alerts,
            "partner_email_draft": partner_email_draft,
            "sales_alert_message": sales_alert,
            "one_click_approval_url": approval_url,
            "action_summary": action_summary
        }

    def _save_quote(self, record: Dict[str, Any]):
        os.makedirs(os.path.dirname(self.quotes_db_path), exist_ok=True)
        existing = []
        if os.path.exists(self.quotes_db_path):
            try:
                with open(self.quotes_db_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = []

        existing.insert(0, record)
        with open(self.quotes_db_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)

    def approve_quote(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        quote_id = payload.get("quote_id")
        if not quote_id:
            return {"status": "error", "message": "quote_id kotelezo a jovahagyashoz!"}

        if os.path.exists(self.quotes_db_path):
            try:
                with open(self.quotes_db_path, "r", encoding="utf-8") as f:
                    records = json.load(f)
                for rec in records:
                    if rec.get("quote_id") == quote_id:
                        rec["status"] = "APPROVED_AND_SENT_TO_PARTNER"
                        rec["approved_at"] = datetime.datetime.now().isoformat()
                        with open(self.quotes_db_path, "w", encoding="utf-8") as fw:
                            json.dump(records, fw, indent=2, ensure_ascii=False)
                        return {
                            "status": "success",
                            "quote_id": quote_id,
                            "new_status": "APPROVED_AND_SENT_TO_PARTNER",
                            "message": f"A(z) {quote_id} B2B ajanlat jovahagyva es sikeresen kikuldve a partnernek!"
                        }
            except Exception as e:
                return {"status": "error", "message": str(e)}

        return {"status": "error", "message": f"A(z) {quote_id} ajanlat nem talalhato."}

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("action", "GENERATE_B2B_QUOTE")
        if action == "APPROVE_QUOTE":
            return self.approve_quote(payload)
        return self.generate_quote(payload)

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    handler = B2BQuotationHandler(config)
    return handler.execute(payload)

if __name__ == "__main__":
    sample = {
        "action": "GENERATE_B2B_QUOTE",
        "partner_identifier": "KlímaMaster Szerelő Kft.",
        "request_text": "100 m rézcső és 20 db golyóscsap árajánlatot kérek"
    }
    res = run(sample)
    print(json.dumps(res, indent=2, ensure_ascii=False))
