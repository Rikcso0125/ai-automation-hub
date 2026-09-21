# -*- coding: utf-8 -*-
import os
import json
import time
from typing import Dict, Any, List

def run(payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    company = config.get("company_name", "DentArt Prémium Fogászat & Implantológia")
    event_type = payload.get("event_type", "APPOINTMENT_CANCELLATION")
    
    blast_size = int(config.get("waitlist_blast_size", 3))
    deposit_amount = int(config.get("deposit_amount_huf", 10000))
    require_deposit = config.get("require_deposit_on_repeat_noshow", True)
    admin_alert_active = config.get("admin_dashboard_alert_enabled", True)

    # 1. ESET: Lemondás és Várólista Villám-újratöltés
    if event_type == "APPOINTMENT_CANCELLATION":
        slot = payload.get("canceled_slot", {})
        slot_time = slot.get("datetime", "2026-09-22 14:00")
        service = slot.get("service", "Szolgáltatás")
        waitlist = payload.get("waitlist", [])

        # Első N fő kiválasztása
        notified_candidates = waitlist[:blast_size]
        dispatched_blasts = []

        for idx, c in enumerate(notified_candidates, 1):
            claim_token = f"CLAIM-{slot.get('booking_id', '8812')}-{idx}"
            claim_link = f"http://localhost:8000/claim/{claim_token}"
            msg = (
                f"Kedves {c['name']}! Felszabadult egy azonnali prémium időpont a(z) {company} rendelőjében: "
                f"{slot_time} ({service})! "
                f"Azonnali lefoglaláshoz kattintson ide: {claim_link}"
            )
            dispatched_blasts.append({
                "candidate_name": c["name"],
                "phone": c["phone"],
                "claim_token": claim_token,
                "claim_link": claim_link,
                "message_sent": msg,
                "channel": "WhatsApp First (Fallback: Telnyx SMS)"
            })

        # Szimuláljuk az első beérkező villám-elfogadást (Flash Claim)
        first_claimer = notified_candidates[0] if notified_candidates else {"name": "Várólistás Érdeklődő"}
        claimed_booking_id = f"REBOOK-{slot.get('booking_id', '8812')}"

        return {
            "status": "success",
            "event_handled": "APPOINTMENT_CANCELLATION",
            "empty_slot_details": {
                "original_booking_id": slot.get("booking_id"),
                "canceled_by": slot.get("client_name"),
                "slot_datetime": slot_time,
                "service": service
            },
            "waitlist_automation": {
                "candidates_notified_count": len(dispatched_blasts),
                "dispatched_blasts": dispatched_blasts,
                "flash_claim_result": {
                    "claimed_by": first_claimer["name"],
                    "phone": first_claimer.get("phone"),
                    "new_booking_id": claimed_booking_id,
                    "calendar_repopulated_status": "AUTO_BOOKED_IN_CALENDAR",
                    "time_to_fill_seconds": 240,
                    "revenue_saved_huf": 28500
                }
            },
            "admin_panel_notice": {
                "status": "SLOT_REFILLED_SUCCESS",
                "badge": "[SIKERES UJRATOLTES] URES IDOPONT MENTVE",
                "message": f"A(z) {slot_time} időpontot {first_claimer['name']} lefoglalta a várólistáról."
            }
        }

    # 2. ESET: No-Show Esemény (Meg nem jelenés kezelése)
    else:
        client_data = payload.get("no_show_client", {})
        client_name = client_data.get("client_name", "Ismeretlen Ügyfél")
        phone = client_data.get("phone", "+36306667788")
        prev_no_shows = int(client_data.get("previous_no_shows", 0)) + 1

        # CRM és előleg zárolási szabály
        deposit_required = require_deposit and (prev_no_shows >= 1)
        deposit_link = f"https://pay.stripe.com/dentart/deposit_{phone[-4:]}" if deposit_required else None

        admin_badge = "[KRITIKUS] NO-SHOW ESZLELVE"
        admin_alert_message = (
            f"FIGYELEM! {client_name} ({phone}) nem jelent meg a megbeszélt időponton. "
            f"No-Show számlálója frissítve: {prev_no_shows}. "
            f"A profil megjelölve a CRM-ben: következő foglaláshoz {deposit_amount:,} Ft kártyás előleg kötelező!"
        )

        return {
            "status": "success",
            "event_handled": "NO_SHOW_OCCURRED",
            "client_profile_updated": {
                "name": client_name,
                "phone": phone,
                "total_no_shows": prev_no_shows,
                "crm_tag": "NO_SHOW_FLAGGED_HIGH_RISK",
                "deposit_required_for_future": deposit_required,
                "deposit_amount_huf": deposit_amount if deposit_required else 0,
                "stripe_deposit_link": deposit_link
            },
            "admin_dashboard_alert": {
                "enabled": admin_alert_active,
                "badge": admin_badge,
                "alert_text": admin_alert_message,
                "action_url": f"http://localhost:8000/#crm_client_{phone[-4:]}"
            }
        }
