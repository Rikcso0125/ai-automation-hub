# -*- coding: utf-8 -*-
import re
from typing import Dict, Any, List

def clean_text(text: str) -> str:
    """Ékezetmentesítés és tisztítás az összehasonlításhoz."""
    t = str(text or "").lower()
    rep = {"á": "a", "é": "e", "í": "i", "ó": "o", "ö": "o", "ő": "o", "ú": "u", "ü": "u", "ű": "u"}
    for k, v in rep.items():
        t = t.replace(k, v)
    return re.sub(r"[^a-z0-9]", "", t)

def calculate_similarity_score(tx: Dict[str, Any], inv: Dict[str, Any]) -> (int, List[str]):
    score = 0
    reasons = []

    # 1. Összeg egyezés (Max 35 pont)
    tx_amount = float(tx.get("amount_huf", 0))
    inv_amount = float(inv.get("gross_amount", 0))

    if tx_amount == inv_amount:
        score += 35
        reasons.append(f"Pontos összeg-egyezés: {tx_amount:,.0f} Ft")
    elif 0 < tx_amount < inv_amount:
        score += 20
        reasons.append(f"Részfizetés észlelve: {tx_amount:,.0f} Ft / {inv_amount:,.0f} Ft")

    # 2. Számlaszám egyezés a közleményben (Max 40 pont)
    clean_remittance = clean_text(tx.get("remittance_info", ""))
    clean_inv_no = clean_text(inv.get("invoice_number", ""))
    # Kinyerjük a számlaszám numerikus részeit is (pl. 2026 0842)
    inv_digits = re.sub(r"[^0-9]", "", inv.get("invoice_number", ""))

    if clean_inv_no in clean_remittance:
        score += 40
        reasons.append(f"Közleményben pontos számlaszám: [{inv.get('invoice_number')}]")
    elif inv_digits and inv_digits in clean_remittance:
        score += 35
        reasons.append(f"Közleményben számlaszám számjegy egyezés: [{inv_digits}]")

    # 3. Név egyezés (Max 25 pont)
    def to_words(s):
        t = str(s or "").lower()
        rep = {"á": "a", "é": "e", "í": "i", "ó": "o", "ö": "o", "ő": "o", "ú": "u", "ü": "u", "ű": "u"}
        for k, v in rep.items():
            t = t.replace(k, v)
        return set(w for w in re.findall(r"[a-z0-9]+", t) if len(w) >= 2)

    words_sender = to_words(tx.get("sender_name", ""))
    words_cust = to_words(inv.get("customer_name", ""))
    common_words = words_sender.intersection(words_cust)

    clean_sender = clean_text(tx.get("sender_name", ""))
    clean_customer = clean_text(inv.get("customer_name", ""))

    if clean_sender == clean_customer:
        score += 25
        reasons.append("Pontos partnernév egyezés")
    elif len(common_words) >= 2:
        score += 25
        reasons.append(f"Erős partnernév egyezés: {', '.join(common_words)}")
    elif len(common_words) == 1:
        score += 15
        reasons.append(f"Közös névelem: {', '.join(common_words)}")

    return min(100, score), reasons

def run(payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    tx = payload.get("incoming_transaction", {})
    open_invoices = payload.get("open_invoices_in_system", [])
    threshold = float(config.get("confidence_threshold_percent", 85))
    source_type = config.get("bank_source_type", "Billingo Bankszinkron API")
    bank_name = config.get("bank_name", "OTP Bank")
    partial_rule = config.get("partial_payment_handling", "Részfizetés rögzítése")
    stop_dunning = config.get("stop_dunning_on_match", "Igen")

    best_match = None
    highest_score = 0
    match_reasons = []

    for inv in open_invoices:
        score, reasons = calculate_similarity_score(tx, inv)
        if score > highest_score:
            highest_score = score
            best_match = inv
            match_reasons = reasons

    tx_amount = float(tx.get("amount_huf", 0))

    if best_match and highest_score >= threshold:
        inv_gross = float(best_match.get("gross_amount", 0))
        is_partial = (tx_amount < inv_gross)

        if is_partial:
            match_status = "PARTIAL_PAYMENT_RECORDED"
            remaining = inv_gross - tx_amount
            action_desc = f"Részfizetés rögzítve ({tx_amount:,.0f} Ft). Fennmaradó tartozás: {remaining:,.0f} Ft."
            thank_you_note = f"Köszönjük a(z) {tx_amount:,.0f} Ft összegű részfizetést a {best_match['invoice_number']} számlára! Fennmaradó egyenleg: {remaining:,.0f} Ft, határidő: {best_match.get('due_date')}."
        else:
            match_status = "FULLY_PAID_AND_CLOSED"
            remaining = 0
            action_desc = f"A számla ({best_match['invoice_number']}) 100%-ban kiegyenlítve és lezárva a rendszerben."
            thank_you_note = f"Köszönjük a számla ({best_match['invoice_number']}) hiánytalan kiegyenlítését!"

        dunning_status = "STOPPED_SUCCESSFULLY" if "Igen" in stop_dunning else "UNCHANGED"

        return {
            "status": "success",
            "match_status": match_status,
            "bank_source": f"{source_type} ({bank_name})",
            "confidence_score": f"{highest_score}%",
            "matched_invoice": {
                "invoice_number": best_match["invoice_number"],
                "customer_name": best_match["customer_name"],
                "gross_amount": inv_gross,
                "amount_paid_now": tx_amount,
                "remaining_balance": remaining,
                "new_invoice_status": "FIZETVE" if not is_partial else "RÉSZBEN FIZETVE"
            },
            "similarity_breakdown": match_reasons,
            "dunning_robot_control": {
                "dunning_stopped": (dunning_status == "STOPPED_SUCCESSFULLY"),
                "message": "A kintlévőség-kezelő és behajtási folyamat azonnal leállítva a számlára."
            },
            "customer_communication": {
                "thank_you_message_prepared": thank_you_note,
                "send_to_email": best_match.get("customer_email", "vevo@partner.hu")
            },
            "accounting_sync": {
                "action": "SET_PAID_IN_BILLING_SYSTEM",
                "payment_method": "Átutalás",
                "transaction_id": tx.get("transaction_id")
            }
        }
    else:
        return {
            "status": "manual_review_required",
            "match_status": "LOW_CONFIDENCE_MATCH",
            "bank_source": f"{source_type} ({bank_name})",
            "confidence_score": f"{highest_score}% (Küszöb: {threshold}%)",
            "best_candidate": best_match["invoice_number"] if best_match else "Nincs releváns számla",
            "candidate_reasons": match_reasons,
            "action_required": "A pénzügyi vezető jóváhagyása szükséges a lekönyveléshez.",
            "alert_dispatched": True,
            "target_alert_email": config.get("alert_email", "penzugy@cegem.hu")
        }

async def run_async(payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    return run(payload, config)
