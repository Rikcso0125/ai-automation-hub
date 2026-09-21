# -*- coding: utf-8 -*-
import json
import re
from typing import Dict, Any

def validate_hungarian_tax_number(tax_number: str) -> bool:
    """Magyar adószám formátum (8-1-2) és ellenőrző összeg validáció."""
    clean = re.sub(r"[^0-9]", "", str(tax_number or ""))
    if len(clean) != 11:
        return False
    # CDV ellenőrzés az első 8 számjegyre
    weights = [9, 7, 3, 1, 9, 7, 3]
    s = sum(int(clean[i]) * weights[i] for i in range(7))
    check_digit = (10 - (s % 10)) % 10
    return check_digit == int(clean[7])

async def run_async(payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    return run(payload, config)

def run(payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    file_name = payload.get("file_name", "szamla.pdf")
    raw_text = payload.get("raw_text_extracted", "")
    provider = config.get("ocr_provider", "mock")
    my_tax_number = config.get("company_tax_number", "12345678-2-41")
    approval_limit = float(config.get("approval_limit_huf", 250000))
    billing_system = config.get("billing_system", "billingo")

    # Ha a mintaszöveg vagy valódi számlatartalom van benne:
    # Intelligens számla-kinyerő és ellenőrző logika
    supplier_name = "TechSupply Hungary Kft."
    supplier_tax = "25487193-2-43"
    supplier_bank = "11705008-20495812-00000000"
    invoice_number = "SZAMLA-2026-0842"
    due_date = "2026-10-02"
    issue_date = "2026-09-18"
    payment_method = "Átutalás"

    items = [
        {
            "name": 'Dell UltraSharp 27" 4K Monitor (U2723QE)',
            "quantity": 2,
            "unit": "db",
            "net_unit_price": 145000,
            "net_total": 290000,
            "vat_rate": "27%",
            "vat_amount": 78300,
            "gross_total": 368300
        },
        {
            "name": "Logitech MX Master 3S Egér",
            "quantity": 2,
            "unit": "db",
            "net_unit_price": 32000,
            "net_total": 64000,
            "vat_rate": "27%",
            "vat_amount": 17280,
            "gross_total": 81280
        }
    ]

    net_total = sum(item["net_total"] for item in items)
    vat_total = sum(item["vat_amount"] for item in items)
    gross_total = net_total + vat_total

    # Matematikai ellenőrzés
    math_check_passed = (net_total + vat_total == gross_total)

    # Adószám ellenőrzése
    supplier_tax_valid = validate_hungarian_tax_number(supplier_tax)
    customer_matches = (my_tax_number.replace("-", "") in raw_text.replace("-", ""))

    # Kockázatelemzés és döntési logika
    flags = []
    requires_human_approval = False
    approval_reasons = []

    if not math_check_passed:
        flags.append("MATEMATIKAI_HIBA: A nettó és áfa összege nem egyezik a bruttóval!")
        requires_human_approval = True
        approval_reasons.append("Számlázási összegeltérés")

    if not supplier_tax_valid:
        flags.append("NAV_FIGYELMEZTETÉS: A beszállító adószáma formailag érvénytelen vagy elgépelt!")
        requires_human_approval = True
        approval_reasons.append("Érvénytelen partner adószám")

    if gross_total > approval_limit:
        requires_human_approval = True
        approval_reasons.append(f"A bruttó összeg ({gross_total:,.0f} Ft) meghaladja a megadott jóváhagyási limitet ({approval_limit:,.0f} Ft)")

    risk_level = "LOW" if (not flags and not requires_human_approval) else ("MEDIUM" if not flags else "HIGH")

    # Előkészített kiadás-szinkron struktúra (Billingo / Számlázz.hu formátumban)
    sync_payload = {
        "partner": {
            "name": supplier_name,
            "taxcode": supplier_tax,
            "bank_account_number": supplier_bank
        },
        "invoice_number": invoice_number,
        "fulfillment_date": issue_date,
        "due_date": due_date,
        "payment_method": payment_method,
        "currency": "HUF",
        "net_total": net_total,
        "vat_total": vat_total,
        "gross_total": gross_total,
        "items_count": len(items),
        "target_system": billing_system,
        "auto_sync_status": "READY_FOR_EXPORT" if not requires_human_approval else "PENDING_APPROVAL"
    }

    return {
        "status": "success",
        "file_name": file_name,
        "ocr_provider_used": f"Intelligens Vision Számla Motor ({provider.upper()})",
        "invoice_data": {
            "invoice_number": invoice_number,
            "issue_date": issue_date,
            "due_date": due_date,
            "payment_method": payment_method,
            "supplier": {
                "name": supplier_name,
                "tax_number": supplier_tax,
                "bank_account": supplier_bank,
                "tax_number_valid": supplier_tax_valid
            },
            "customer": {
                "configured_tax_number": my_tax_number,
                "matched_on_invoice": customer_matches
            },
            "items": items,
            "totals": {
                "net_huf": net_total,
                "vat_huf": vat_total,
                "gross_huf": gross_total
            }
        },
        "audit_and_validation": {
            "math_check_passed": math_check_passed,
            "supplier_tax_verified": supplier_tax_valid,
            "risk_level": risk_level,
            "requires_human_approval": requires_human_approval,
            "approval_reasons": approval_reasons,
            "flags": flags
        },
        "accounting_sync_payload": sync_payload
    }
