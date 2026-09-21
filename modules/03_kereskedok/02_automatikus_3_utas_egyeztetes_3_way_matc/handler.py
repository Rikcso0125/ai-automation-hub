"""
Automatikus 3-Utas Egyeztetés (3-Way Matching: Számla vs PO vs Szállítólevél & Csalásszűrés)
Modul: 02_automatikus_3_utas_egyeztetes_3_way_matc
"""

import os
import sys
import json
import datetime
from typing import Dict, Any, List, Optional

class ThreeWayMatchingHandler:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.service_mode = self.config.get("service_mode", "mock")
        self.iban_guard_mode = self.config.get("iban_fraud_guard_mode", "STRICT_FREEZE")
        self.price_tolerance_pct = float(self.config.get("price_tolerance_percent", 0.0))
        self.rounding_tolerance_huf = float(self.config.get("rounding_tolerance_huf", 5.0))
        self.auto_approve_perfect = self.config.get("auto_approve_perfect_match", True)
        self.generate_dispute = self.config.get("generate_dispute_letter", True)
        self.audit_db_path = self.config.get("audit_db_path", "data/3way_matching_naplo.json")

    def _normalize_iban(self, iban_str: str) -> str:
        return "".join(c for c in (iban_str or "") if c.isalnum()).upper()

    def _generate_dispute_letter(
        self,
        invoice_no: str,
        po_no: str,
        delivery_note_no: str,
        supplier_name: str,
        discrepancies: List[Dict[str, Any]],
        total_overbilled_huf: float
    ) -> str:
        today_str = datetime.date.today().strftime("%Y.%m.%d.")
        lines = [
            f"HIVATALOS KIFOGÁSOLÁSI JEGYZŐKÖNYV ÉS JÓVÁÍRÓ SZÁMLA IGÉNY",
            f"Dátum: {today_str}",
            f"Címzett: {supplier_name} - Pénzügyi és Értékesítési Osztály",
            "",
            f"Tisztelt Partnerünk!",
            "",
            f"Értesítjük Önöket, hogy a(z) {invoice_no} sorszámú számlájuk 3-utas pénzügyi ellenőrzése során "
            f"(Összevetve a jóváhagyott {po_no} sz. megrendeléssel és a {delivery_note_no} sz. raktári bevételezéssel) "
            f"az alábbi jogosulatlan eltéréseket azonosítottuk:",
            ""
        ]

        for d in discrepancies:
            lines.append(f"• Cikkszám: {d['sku']} - {d['name']}")
            if d.get("quantity_discrepancy"):
                lines.append(f"  - Mennyiségi hiány: Számlázva {d['invoiced_qty']} db, Raktárba beérkezett: {d['received_qty']} db (Hiány: {d['qty_diff']} db)")
            if d.get("price_discrepancy"):
                lines.append(f"  - Áreltérés: Számlázott egységár: {d['invoiced_unit_price']:,} Ft, PO jóváhagyott ár: {d['po_approved_unit_price']:,} Ft (+{d['price_diff_pct']}% túlszámlázás)")
            lines.append(f"  - Jogosulatlan túlszámlázási összeg: {d['item_overbilled_huf']:,} Ft nettó")
            lines.append("")

        lines.extend([
            f"ÖSSZESÍTETT TÚLSZÁMLÁZÁS / KIFOGÁSOLT ÖSSZEG: {total_overbilled_huf:,} Ft + ÁFA",
            "",
            "A fentiek alapján a számla kifizetését belső pénzügyi szabályzatunk szerint zároltuk.",
            f"Kérjük, szíveskedjenek a vitatott tételre vonatkozóan {total_overbilled_huf:,} Ft értékben helyesbítő / jóváíró számlát (Credit Note) kiállítani,",
            "vagy a hiányzó mennyiséget haladéktalanul pótolni.",
            "",
            "Megértésüket és gyors együttműködésüket köszönjük!",
            "Üdvözlettel: Pénzügyi és Beszerzési Igazgatóság"
        ])

        return chr(10).join(lines)

    def reconcile(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        invoice = payload.get("invoice", {})
        po = payload.get("purchase_order", {})
        gr = payload.get("goods_receipt", {})

        invoice_no = invoice.get("invoice_number", "ISMERETLEN_SZAMLA")
        po_no = po.get("po_number", "ISMERETLEN_PO")
        dn_no = gr.get("delivery_note_number") or gr.get("receipt_number", "ISMERETLEN_SZALLITO")
        supplier_name = invoice.get("supplier_name", "Beszállító")

        reconciliation_id = f"3WAY-{datetime.date.today().strftime('%Y%m%d')}-{invoice_no.replace('/', '_')}"

        # 1. LÉPÉS: IBAN CSALÁSSZŰRÉS (FRAUD GUARD)
        inv_iban_clean = self._normalize_iban(invoice.get("supplier_iban", ""))
        reg_iban_clean = self._normalize_iban(po.get("registered_iban", ""))
        fraud_risk = False
        fraud_message = None

        if inv_iban_clean and reg_iban_clean and inv_iban_clean != reg_iban_clean:
            fraud_risk = True
            fraud_message = (
                f"VIGYÁZAT! A számlán szereplő IBAN ({invoice.get('supplier_iban')}) eltér a céges törzsben "
                f"regisztrált hivatalos bankszámlaszámtól ({po.get('registered_iban')})! Lehetséges számlacsalás."
            )

        # 2. LÉPÉS: TÉTELES 3-UTAS EGYEZTETÉS
        po_items_by_sku = {item.get("sku"): item for item in po.get("items", [])}
        gr_items_by_sku = {item.get("sku"): item for item in gr.get("items", [])}

        reconciled_lines = []
        discrepancies = []
        total_overbilled_huf = 0.0
        total_invoiced_net = float(invoice.get("total_net", 0.0))
        total_approved_net = 0.0

        for inv_item in invoice.get("items", []):
            sku = inv_item.get("sku")
            name = inv_item.get("name")
            inv_qty = float(inv_item.get("quantity", 0))
            inv_price = float(inv_item.get("unit_price", 0))
            inv_line_net = float(inv_item.get("line_net", inv_qty * inv_price))

            po_item = po_items_by_sku.get(sku, {})
            po_qty = float(po_item.get("quantity", 0))
            po_price = float(po_item.get("approved_unit_price", inv_price))

            gr_item = gr_items_by_sku.get(sku, {})
            gr_qty = float(gr_item.get("accepted_qty", gr_item.get("received_qty", 0)))

            # Mennyiségi vizsgálat (Számla vs Raktári átvétel)
            qty_diff = inv_qty - gr_qty
            has_qty_discrepancy = qty_diff > 0

            # Árvizsgálat (Számla ár vs PO jóváhagyott ár)
            price_diff = inv_price - po_price
            price_diff_pct = round((price_diff / po_price) * 100, 2) if po_price > 0 else 0.0
            has_price_discrepancy = price_diff_pct > self.price_tolerance_pct

            item_overbilled = 0.0
            if has_qty_discrepancy:
                # Kiszámlázva olyan darabokért, amit át sem vettünk
                item_overbilled += (qty_diff * inv_price)
            if has_price_discrepancy:
                # A ténylegesen átvett darabokra rászámolt felár
                item_overbilled += (gr_qty * price_diff)

            line_status = "MATCH_PERFECT"
            if has_qty_discrepancy or has_price_discrepancy:
                line_status = "DISCREPANCY_DETECTED"
                total_overbilled_huf += item_overbilled
                discrepancies.append({
                    "sku": sku,
                    "name": name,
                    "invoiced_qty": inv_qty,
                    "received_qty": gr_qty,
                    "po_qty": po_qty,
                    "qty_diff": qty_diff,
                    "quantity_discrepancy": has_qty_discrepancy,
                    "invoiced_unit_price": inv_price,
                    "po_approved_unit_price": po_price,
                    "price_diff_pct": price_diff_pct,
                    "price_discrepancy": has_price_discrepancy,
                    "item_overbilled_huf": item_overbilled
                })

            # A jóváhagyható összeg az átvett mennyiség * po_ár
            approved_line_net = gr_qty * po_price
            total_approved_net += approved_line_net

            reconciled_lines.append({
                "sku": sku,
                "name": name,
                "invoiced_qty": inv_qty,
                "received_qty": gr_qty,
                "po_qty": po_qty,
                "invoiced_price": inv_price,
                "po_price": po_price,
                "line_status": line_status,
                "item_overbilled_huf": item_overbilled,
                "approved_line_net": approved_line_net
            })

        # Végösszeg kerekítési ellenőrzés
        rounding_diff = abs(total_invoiced_net - (total_approved_net + total_overbilled_huf))
        has_rounding_issue = rounding_diff > self.rounding_tolerance_huf

        # 3. LÉPÉS: VÉGSŐ JÓVÁHAGYÁSI DÖNTÉS
        if fraud_risk and self.iban_guard_mode == "STRICT_FREEZE":
            reconciliation_status = "SUSPECTED_FRAUD_PAYMENT_FROZEN"
            payment_authorized = False
            action_summary = "Pénzügyi zárolás aktiválva: IBAN számlacsalási gyanú!"
        elif total_overbilled_huf > 0 or len(discrepancies) > 0:
            reconciliation_status = "DISCREPANCY_PAYMENT_HOLD"
            payment_authorized = False
            action_summary = f"Kifizetés felfüggesztve: {total_overbilled_huf:,} Ft jogosulatlan túlszámlázás / hiány azonosítva."
        else:
            reconciliation_status = "PERFECT_MATCH_APPROVED_FOR_PAYMENT"
            payment_authorized = True
            action_summary = "100%-os 3-utas egyezés! A számla kifizetésre jóváhagyva."

        dispute_letter = ""
        if discrepancies and self.generate_dispute:
            dispute_letter = self._generate_dispute_letter(
                invoice_no=invoice_no,
                po_no=po_no,
                delivery_note_no=dn_no,
                supplier_name=supplier_name,
                discrepancies=discrepancies,
                total_overbilled_huf=total_overbilled_huf
            )

        override_url = f"http://localhost:8000/api/v1/modules/02_automatikus_3_utas_egyeztetes_3_way_matc/override?rec_id={reconciliation_id}"

        # Értesítési üzenet a gazdasági vezetőnek
        alert_lines = [
            "[3-WAY MATCHING AUDIT EREDMÉNY]",
            f"Szamlaszam: {invoice_no}",
            f"Beszallito: {supplier_name}",
            f"Megrendeles (PO): {po_no} | Szallitolevel: {dn_no}",
            f"Statusz: {reconciliation_status}",
            f"Szamlazott osszeg: {total_invoiced_net:,} Ft nettó",
            f"Jovahagytato osszeg: {total_approved_net:,} Ft nettó",
            f"Tulszamlazas / Hiany: {total_overbilled_huf:,} Ft nettó",
            f"Fizetes engedelyezve: {'IGEN' if payment_authorized else 'NEM (ZÁROLVA)'}",
            ""
        ]
        if fraud_risk:
            alert_lines.append(f"RIASZTÁS: {fraud_message}")
            alert_lines.append("")
        if discrepancies:
            alert_lines.append("Azonositott elteresek:")
            for d in discrepancies:
                alert_lines.append(f"- {d['sku']}: Tulszamlazas = {d['item_overbilled_huf']:,} Ft")
            alert_lines.append("")
            alert_lines.append("Gazdasagi vezeto felulbiralati link:")
            alert_lines.append(f"-> {override_url}")

        executive_alert = chr(10).join(alert_lines)

        audit_record = {
            "reconciliation_id": reconciliation_id,
            "created_at": datetime.datetime.now().isoformat(),
            "invoice_number": invoice_no,
            "po_number": po_no,
            "delivery_note_number": dn_no,
            "supplier_name": supplier_name,
            "fraud_risk": fraud_risk,
            "fraud_message": fraud_message,
            "status": reconciliation_status,
            "payment_authorized": payment_authorized,
            "total_invoiced_net": total_invoiced_net,
            "total_approved_net": total_approved_net,
            "total_overbilled_huf": total_overbilled_huf,
            "discrepancies_count": len(discrepancies),
            "lines": reconciled_lines,
            "discrepancies": discrepancies,
            "dispute_letter": dispute_letter,
            "override_url": override_url
        }

        self._save_audit_log(audit_record)

        return {
            "status": "success",
            "action_executed": "3WAY_MATCHING_RECONCILED",
            "reconciliation_id": reconciliation_id,
            "reconciliation_status": reconciliation_status,
            "payment_authorized": payment_authorized,
            "fraud_risk_detected": fraud_risk,
            "fraud_message": fraud_message,
            "summary": {
                "invoiced_net_huf": total_invoiced_net,
                "approved_net_huf": total_approved_net,
                "overbilled_huf": total_overbilled_huf,
                "discrepancies_count": len(discrepancies),
                "action_summary": action_summary
            },
            "discrepancies": discrepancies,
            "dispute_letter_for_supplier": dispute_letter,
            "one_click_override_url": override_url,
            "executive_alert_message": executive_alert
        }

    def _save_audit_log(self, record: Dict[str, Any]):
        os.makedirs(os.path.dirname(self.audit_db_path), exist_ok=True)
        existing = []
        if os.path.exists(self.audit_db_path):
            try:
                with open(self.audit_db_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = []

        existing.insert(0, record)
        with open(self.audit_db_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)

    def override_approval(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        rec_id = payload.get("reconciliation_id")
        reason = payload.get("reason", "Gazdasági vezetői felülbírálat jóváírószámla beérkezése után")
        if not rec_id:
            return {"status": "error", "message": "reconciliation_id kötelező a felülbírálathoz!"}

        if os.path.exists(self.audit_db_path):
            try:
                with open(self.audit_db_path, "r", encoding="utf-8") as f:
                    records = json.load(f)
                for rec in records:
                    if rec.get("reconciliation_id") == rec_id:
                        rec["status"] = "MANUALLY_OVERRIDDEN_APPROVED"
                        rec["payment_authorized"] = True
                        rec["override_reason"] = reason
                        rec["overridden_at"] = datetime.datetime.now().isoformat()
                        with open(self.audit_db_path, "w", encoding="utf-8") as fw:
                            json.dump(records, fw, indent=2, ensure_ascii=False)
                        return {
                            "status": "success",
                            "reconciliation_id": rec_id,
                            "new_status": "MANUALLY_OVERRIDDEN_APPROVED",
                            "payment_authorized": True,
                            "message": f"A(z) {rec_id} számla kézi felülbírálattal kifizetésre engedélyezve."
                        }
            except Exception as e:
                return {"status": "error", "message": str(e)}

        return {"status": "error", "message": f"A(z) {rec_id} egyeztetési azonosító nem található."}

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = payload.get("action", "RECONCILE_3WAY")
        if action == "OVERRIDE_APPROVAL":
            return self.override_approval(payload)
        return self.reconcile(payload)

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    handler = ThreeWayMatchingHandler(config)
    return handler.execute(payload)

if __name__ == "__main__":
    test_p = {
        "action": "RECONCILE_3WAY",
        "invoice": {"invoice_number": "TEST-1", "supplier_iban": "HU111", "items": []},
        "purchase_order": {"po_number": "PO-1", "registered_iban": "HU111", "items": []},
        "goods_receipt": {"receipt_number": "GR-1", "items": []}
    }
    res = run(test_p)
    print(json.dumps(res, indent=2, ensure_ascii=False))
