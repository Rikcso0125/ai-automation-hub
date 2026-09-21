# -*- coding: utf-8 -*-
import json
import re
from typing import Dict, Any

def run(payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    sender_name = payload.get("sender_name", "Ismeretlen feladó")
    sender_email = payload.get("sender_email", "")
    sender_company = payload.get("sender_company", "")
    sender_phone = payload.get("sender_phone", "")
    subject = payload.get("subject", "")
    body = payload.get("body", "")

    # Telefonszám automatikus kinyerése a levéltörzsből ha nincs külön mezőben
    if not sender_phone:
        phone_match = re.search(r"(\+?[0-9\s\-\/]{9,15})", body)
        if phone_match:
            sender_phone = phone_match.group(1).strip()

    company_name = config.get("company_name", "Cégünk")
    detection_mode = config.get("vip_detection_mode", "Mindkettő (VIP Partner Lista + AI Hangulatelemzés)")
    vip_list_raw = config.get("vip_domains_and_emails", "mol.hu, otp.hu, audi.hu")
    urgent_kw_raw = config.get("urgent_keywords", "azonnal, sürgős, leállás, kötbér, panasz, hiba")
    channels = config.get("alert_channels", "Mindhárom (Telegram + Telnyx SMS + Email)")
    auto_reply = config.get("auto_reply_to_vip", "Igen (Bekapcsolva)")
    reply_template = config.get("auto_reply_message", "")

    exec_phone = config.get("executive_phone", "+36301234567")
    exec_email = config.get("executive_email", "vezeto@ceg.hu")

    # 1. VIP lista ellenőrzése
    vip_items = [v.strip().lower() for v in vip_list_raw.split(",") if v.strip()]
    sender_domain = sender_email.split("@")[-1].lower() if "@" in sender_email else ""
    is_vip_match = False
    vip_reason = None

    for item in vip_items:
        if item in sender_email.lower() or item == sender_domain:
            is_vip_match = True
            vip_reason = f"Kiemelt VIP partner domain/email egyezés: [{item}]"
            break

    # 2. Sürgősségi kulcsszó és hangulatelemzés
    urgent_keywords = [k.strip().lower() for k in urgent_kw_raw.split(",") if k.strip()]
    found_keywords = []
    full_text_lower = f"{subject} {body}".lower()
    for kw in urgent_keywords:
        if kw in full_text_lower:
            found_keywords.append(kw)

    # Frusztráció és sürgősségi pontszámítás
    urgency_score = 1
    frustration_level = "Normál / Nyugodt"
    
    if found_keywords:
        urgency_score = min(5, 2 + len(found_keywords))
        frustration_level = "Magas / Káresemény vagy kötbér veszély"

    if any(w in full_text_lower for w in ["kötbér", "kártérítés", "leállás", "ügyvéd", "felmondás"]):
        urgency_score = 5
        frustration_level = "KRITIKUS / Dühös & Jogi fenyegetés"

    # 3. Döntési mechanizmus
    should_escalate = False
    escalation_reasons = []

    if "Lista" in detection_mode and is_vip_match:
        should_escalate = True
        escalation_reasons.append(vip_reason)

    if "AI" in detection_mode or "Mindkettő" in detection_mode:
        if urgency_score >= 4:
            should_escalate = True
            escalation_reasons.append(f"Kritikus sürgősség és kockázat (Pontszám: {urgency_score}/5, Hangulat: {frustration_level})")
        if found_keywords:
            escalation_reasons.append(f"Sürgősségi kulcsszavak észlelve: {', '.join(found_keywords)}")

    # 4. Értesítések előkészítése a vezetőnek
    alert_title = "[SURGOS VEZETOI EMAIL ESZKALACIO]"
    alert_summary = f"""{alert_title}
• Feladó: {sender_name} ({sender_company or sender_email})
• Telefonszám: {sender_phone or 'Nincs megadva'}
• Tárgy: {subject}
• Eszkaláció oka: {' | '.join(escalation_reasons)}
• Hangulat: {frustration_level}
• Javasolt azonnali teendő: Közvetlen visszahívás 15 percen belül!"""

    sms_alert = f"FIGYELEM VEZETO! Surgos VIP email: {sender_name} ({sender_domain}). Targy: {subject[:40]}... Visszahivas: {sender_phone}"

    # 5. Eredmény csomag összeállítása
    return {
        "status": "success",
        "is_escalated": should_escalate,
        "classification": {
            "is_vip": is_vip_match,
            "vip_details": vip_reason if is_vip_match else "Nem szerepel a fix VIP listán",
            "urgency_score": urgency_score,
            "frustration_level": frustration_level,
            "detected_keywords": found_keywords,
            "escalation_reasons": escalation_reasons
        },
        "executive_notifications": {
            "channels_configured": channels,
            "telegram_alert": {
                "sent": ("Telegram" in channels or "Mindhárom" in channels) and should_escalate,
                "message": alert_summary
            },
            "telnyx_sms_alert": {
                "sent": ("Telnyx SMS" in channels or "Mindhárom" in channels) and should_escalate,
                "target_phone": exec_phone,
                "sms_body": sms_alert
            },
            "email_alert": {
                "sent": ("Email" in channels or "Mindhárom" in channels) and should_escalate,
                "target_email": exec_email,
                "subject": f"[ESZKALACIO] {subject}",
                "body": alert_summary
            }
        },
        "client_auto_reply": {
            "enabled": (auto_reply == "Igen (Bekapcsolva)"),
            "sent_to": sender_email,
            "subject": f"Re: {subject} - Kiemelt ügyfélszolgálati tájékoztatás",
            "reply_text": reply_template
        }
    }

async def run_async(payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    return run(payload, config)
