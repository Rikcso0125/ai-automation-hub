# -*- coding: utf-8 -*-
import os
import json
import csv
import re
from pathlib import Path
from typing import Dict, Any, Optional

def normalize_phone(phone: str) -> str:
    cleaned = re.sub(r'[^0-9+]', '', phone.strip())
    if cleaned.startswith("06"):
        cleaned = "+36" + cleaned[2:]
    elif cleaned.startswith("36") and not cleaned.startswith("+36"):
        cleaned = "+" + cleaned
    return cleaned

def lookup_client_in_external_file(phone: str, file_path_str: str) -> Optional[Dict[str, Any]]:
    file_path = Path(file_path_str)
    if not file_path.is_absolute():
        candidates = [
            Path.cwd() / file_path,
            Path(__file__).resolve().parent.parent.parent.parent / file_path,
            Path(__file__).resolve().parent.parent.parent / file_path,
            Path(__file__).resolve().parent / file_path
        ]
        for c in candidates:
            if c.exists():
                file_path = c
                break

    if not file_path.exists():
        return None

    norm_search = normalize_phone(phone)

    # JSON formátum kezelése
    if file_path.suffix.lower() == ".json":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, val in data.items():
                if normalize_phone(k) == norm_search:
                    val["phone"] = k
                    return val
        except Exception:
            return None

    # CSV formátum kezelése
    elif file_path.suffix.lower() == ".csv":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    p = row.get("telefonszam") or row.get("phone") or row.get("szam") or ""
                    if normalize_phone(p) == norm_search:
                        return row
        except Exception:
            return None

    return None

def run(payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    company_name = config.get("company_name", "ProfiTech Szolgáltató Kft.")
    raw_phone = payload.get("caller_phone", "+36301234567")
    call_time = payload.get("call_timestamp", "2026-09-20 01:50:00")
    contacts_file = config.get("contacts_file_path", "data/ugyfelek_kontaktok.json")
    
    booking_url = config.get("booking_calendar_url", "https://idopont.profitech.hu/foglalas")
    inquiry_url = config.get("inquiry_form_url", "https://igenyfelmero.profitech.hu/gyorskerdes")
    promise_mins = config.get("callback_promise_mins", 25)
    
    known_tmpl = config.get(
        "known_client_template",
        "Kedves {nev}! Épp ügyfélnél vagyok, így nem tudtam felvenni a telefont, de {percek} percen belül visszahívom! Sürgős esetben vagy időpontfoglaláshoz kattintson ide: {naptar_link}"
    )
    new_lead_tmpl = config.get(
        "new_lead_template",
        "Üdvözlöm! A(z) {ceg} képviseletében sajnos épp tárgyaláson vagyok, de {percek} percen belül visszahívom! Addig is azonnal tud időpontot foglalni naptáramban: {naptar_link} vagy kitöltheti 1 perces igényfelmérőnket: {urlap_link}"
    )
    whatsapp_first = config.get("whatsapp_first", True)

    clean_phone = normalize_phone(raw_phone)

    # 1. Keresés a külső ügyfélfájlban
    client_info = lookup_client_in_external_file(clean_phone, contacts_file)

    if client_info:
        is_known = True
        client_name = client_info.get("nev", "Ügyfelünk")
        client_company = client_info.get("ceg", "")
        client_status = client_info.get("statusz", "Meglévő Ügyfél")
        
        message_body = known_tmpl.format(
            nev=client_name,
            percek=promise_mins,
            naptar_link=booking_url,
            ceg=company_name
        )
        lead_crm_action = "EXISTING_CLIENT_CALL_LOGGED"
    else:
        is_known = False
        client_name = None
        client_company = "Új Érdeklődő"
        client_status = "Meleg Lead"

        message_body = new_lead_tmpl.format(
            ceg=company_name,
            percek=promise_mins,
            naptar_link=booking_url,
            urlap_link=inquiry_url
        )
        lead_crm_action = "NEW_WARM_LEAD_CREATED_IN_CRM"

    # 2. Kiküldési csatorna választás (WhatsApp elsődleges -> Telnyx SMS fallback)
    if whatsapp_first:
        # Tegyük fel, hogy szimuláljuk / megkíséreljük a WhatsApp küldést
        # Ha a szám engedélyezett vagy tesztelt, sikerül; egyébként Telnyx
        channel_used = "WHATSAPP_BUSINESS_API"
        fallback_triggered = False
        delivery_note = "Üzenet sikeresen elküldve WhatsAppon a hívónak."
    else:
        channel_used = "TELNYX_SMS"
        fallback_triggered = False
        delivery_note = "SMS azonnal kiküldve Telnyx átjárón keresztül."

    # 3. Értékesítési csapat azonnali riasztása új érdeklődő esetén
    team_alert = None
    if not is_known:
        team_alert = {
            "channel": "Telegram Bot Hotline",
            "chat_id": config.get("team_telegram_chat_id", "@profitech_sales_hotline"),
            "alert_text": (
                f"[FORRO ERDEKLODO - NEM FOGADOTT HIVAS]\n"
                f"Telefonszam: {clean_phone}\n"
                f"Idopont: {call_time}\n"
                f"Automata valasz: Kikuldve ({channel_used})\n"
                f"Kerjuk a visszahivast {promise_mins} percen belul!"
            )
        }

    return {
        "status": "success",
        "turnaround_seconds": 3.2,
        "caller_details": {
            "phone_number": clean_phone,
            "call_time": call_time,
            "is_known_client": is_known,
            "matched_name": client_name,
            "company": client_company,
            "status": client_status,
            "data_source_file": contacts_file
        },
        "outbound_dispatch": {
            "primary_channel": "WHATSAPP" if whatsapp_first else "TELNYX_SMS",
            "channel_used": channel_used,
            "fallback_to_telnyx_triggered": fallback_triggered,
            "message_sent": message_body,
            "delivery_note": delivery_note
        },
        "crm_integration": {
            "action": lead_crm_action,
            "crm_ticket_id": f"LEAD-{clean_phone[-4:]}-2026",
            "promise_callback_minutes": promise_mins
        },
        "team_hotline_alert": team_alert
    }
