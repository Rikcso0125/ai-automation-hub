# -*- coding: utf-8 -*-
import json
from datetime import datetime
from typing import Dict, Any

async def run_async(payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    return run(payload, config)

def run(payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    invoice_no = payload.get("invoice_number", "SZAMLA-0001")
    customer_name = payload.get("customer_name", "Kedves Partnerünk")
    customer_email = payload.get("customer_email", "")
    customer_phone = payload.get("customer_phone", "")
    days_overdue = int(payload.get("days_overdue", 0))
    orig_amount = float(payload.get("original_amount_huf", 100000))
    currency = payload.get("currency", "HUF")

    company_name = config.get("company_name", "Cégünk Kft.")
    bank_account = config.get("company_bank_account", "11705008-20495812-00000000")
    grace_period = int(config.get("grace_period_days", 15))
    eur_rate = float(config.get("eur_huf_rate", 400))
    gateway = config.get("payment_gateway", "billingo")
    email_prov = config.get("email_provider", "mock")
    sms_prov = config.get("sms_provider", "mock")

    # 1. Fizetési link generálás
    if gateway == "stripe":
        pay_url = f"https://buy.stripe.com/test_pay_{invoice_no.replace('-', '')}"
    elif gateway == "billingo":
        pay_url = f"https://app.billingo.hu/pay/{invoice_no}"
    elif gateway == "szamlazz_hu":
        pay_url = f"https://www.szamlazz.hu/fizetes/{invoice_no}"
    else:
        pay_url = f"Banki átutalás: {bank_account} (Közlemény: {invoice_no})"

    # 2. Lépcsőzetes logika kiértékelése a késedelem napjai alapján
    fee_40eur_huf = 0
    interest_huf = 0
    stage = ""
    send_sms = False
    action_title = ""

    if days_overdue < 0:
        stage = "PRE_DUE"
        action_title = "Lejárat előtti udvarias emlékeztető (-2 nap)"
        email_subject = f"Emlékeztető: Közelgő számlafizetés ({invoice_no}) - {company_name}"
        email_body = f"""Kedves {customer_name}!

Szeretnénk figyelmébe ajánlani, hogy a(z) {invoice_no} számú, {orig_amount:,.0f} {currency} összegű számlánk hamarosan esedékessé válik.

A számla kényelmesen rendezhető online bankkártyával az alábbi linken:
{pay_url}

Vagy banki átutalással:
Bankszámlaszám: {bank_account}
Közlemény: {invoice_no}

Köszönjük együttműködését!

Üdvözlettel,
{company_name} Pénzügy"""
        sms_text = ""

    elif days_overdue == 0:
        stage = "DUE_TODAY"
        action_title = "Ma esedékes fizetési értesítő"
        email_subject = f"Értesítés: Ma esedékes számla ({invoice_no}) - {company_name}"
        email_body = f"""Kedves {customer_name}!

Értesítjük, hogy a(z) {invoice_no} számú számlánk a mai napon esedékes ({orig_amount:,.0f} {currency}).

Kérjük, intézkedjen a számla kiegyenlítéséről:
Online azonnali fizetés: {pay_url}

Köszönjük pontosságát!
{company_name}"""
        sms_text = ""

    elif 1 <= days_overdue < grace_period:
        stage = "FIRST_WARNING"
        send_sms = True
        action_title = f"1. Fizetési figyelmeztetés ({days_overdue} nap késés) + Telnyx SMS"
        email_subject = f"Fizetési figyelmeztetés: Lejárt számla ({invoice_no}) - {company_name}"
        email_body = f"""Tisztelt {customer_name}!

Nyilvántartásunk szerint a(z) {invoice_no} számú számla fizetési határideje {days_overdue} napja lejárt.
Fizetendő összeg: {orig_amount:,.0f} {currency}.

Kérjük, szíveskedjen ellenőrizni és mihamarabb rendezni:
Azonnali bankkártyás fizetés: {pay_url}

Amennyiben az átutalás már megtörtént, kérjük tekintse levelünket tárgytalannak.

Üdvözlettel,
{company_name}"""
        sms_text = f"Tisztelt Partnerunk! A(z) {invoice_no} szamla {days_overdue} napja lejart ({orig_amount:,.0f} Ft). Kerjuk rendezze online: {pay_url} - {company_name}"

    else:
        # >= grace_period (pl. 15 nap után: 40 EUR behajtási költségátalány + késedelmi kamat)
        stage = "LEGAL_DEMAND_40EUR"
        send_sms = True
        action_title = f"Hivatalos Ügyvédi/Pénzügyi Felszólítás & 40 EUR Költségátalány ({days_overdue} nap késés)"

        fee_40eur_huf = int(40 * eur_rate)
        annual_rate = 0.145  # 14.5% jegybanki kamat
        interest_huf = int(orig_amount * annual_rate * (days_overdue / 365.0))
        total_payable = int(orig_amount + fee_40eur_huf + interest_huf)

        email_subject = f"HIVATALOS FIZETÉSI FELSZÓLÍTÁS & 40 EUR Költségátalány: {invoice_no} - {company_name}"
        email_body = f"""TISZTELT {customer_name.upper()}!

Hivatalosan felszólítjuk, hogy a(z) {invoice_no} számú, {days_overdue} napja lejárt tartozását haladéktalanul rendezze!

A behajtási költségátalányról szóló 2016. évi IX. törvény 3. § (1) bekezdése alapján a vállalkozások közötti kereskedelmi ügyletek késedelmes fizetése esetén a jogosult a késedelem napjától kezdve legalább 40 EUR összegű behajtási költségátalányra, valamint a Ptk. szerinti késedelmi kamatra jogosult.

TARTOZÁS ÖSSZESÍTŐ:
• Alaptartozás (Számla összege): {orig_amount:,.0f} {currency}
• Törvényi behajtási költségátalány (40 EUR): {fee_40eur_huf:,.0f} {currency}
• Számított késedelmi kamat: {interest_huf:,.0f} {currency}
------------------------------------------------------------
MINDÖSSZESEN FIZETENDŐ: {total_payable:,.0f} {currency}

Kérjük a tartozás 3 munkanapon belüli teljesítését az alábbi linken keresztül:
{pay_url}

Bankszámlaszám: {bank_account}
Közlemény: {invoice_no}

Felhívjuk figyelmét, hogy a határidő eredménytelen eltelte esetén az ügyet átadjuk követeléskezelő és jogi partnerünknek, mely esetben a fizetési meghagyás és végrehajtás teljes költsége Önöket terheli.

{company_name} Pénzügyi és Jogi Osztály"""

        sms_text = f"FIGYELEM! A(z) {invoice_no} szamla {days_overdue} napja lejart. A 40 EUR koltsegatalany felszamitasra kerult. Fizetendo: {total_payable:,.0f} Ft. Fizetes: {pay_url}"

    total_due = orig_amount + fee_40eur_huf + interest_huf

    return {
        "status": "success",
        "stage": stage,
        "action_taken": action_title,
        "invoice_number": invoice_no,
        "customer": {
            "name": customer_name,
            "email": customer_email,
            "phone": customer_phone
        },
        "days_overdue": days_overdue,
        "financial_breakdown": {
            "original_invoice_amount": orig_amount,
            "statutory_40eur_fee_huf": fee_40eur_huf,
            "statutory_interest_huf": interest_huf,
            "total_amount_due": total_due,
            "currency": currency
        },
        "payment_link_generated": pay_url,
        "delivery": {
            "email_provider": f"{email_prov.upper()} (Tárgy: {email_subject})",
            "email_queued": True,
            "email_content": email_body,
            "sms_provider": f"{sms_prov.upper()} (Telnyx API)",
            "sms_sent": send_sms,
            "sms_text": sms_text if send_sms else "SMS küldés ezen a szinten még nem szükséges"
        },
        "legal_reference": "2016. évi IX. törvény a behajtási költségátalányról" if fee_40eur_huf > 0 else "Nincs jogi szankció"
    }
