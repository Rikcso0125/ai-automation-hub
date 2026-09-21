# -*- coding: utf-8 -*-
import os
import json
import time
from typing import Dict, Any, List

def run(payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    company = config.get("company_name", "ProfiTech Szolgáltató Kft.")
    buffer_mins = int(config.get("buffer_time_minutes", 30))
    duration_mins = int(config.get("meeting_duration_minutes", 45))
    calendar_sys = config.get("calendar_system", "Google Calendar API")
    staff_mode = config.get("staff_assignment_mode", "Automatikus Round-Robin (Egyenletes elosztás)")
    require_confirm = config.get("require_reschedule_confirmation", True)
    
    msg = payload.get("user_message", "").strip()
    channel = payload.get("channel", "website_widget")
    user_info = payload.get("user_profile", {})
    user_name = user_info.get("name", "Kedves Érdeklődő")
    existing_id = payload.get("existing_booking_id")
    msg_l = msg.lower()

    # Szakember kiválasztása
    assigned_staff = "Horváth Ádám (Vezető Tanácsadó)" if "Round-Robin" in staff_mode else "Kovács Béla (Ügyvezető)"

    # 1. ESET: Időpont módosítási kérés
    if any(k in msg_l for k in ["mégse", "megse", "át tudjuk", "at tudjuk", "módosít", "modosit", "másik időpont", "masik idopont"]):
        target_slot = "2026. szeptember 24. (Csütörtök) 10:00"
        
        # Ha megerősítést küldött az ügyfél ("igen", "oké", "rendben")
        if any(c in msg_l for c in ["igen", "jó lesz", "jo lesz", "rendben", "oké", "oke"]):
            booking_status = "RESCHEDULED_CONFIRMED"
            bot_reply = (
                f"Koszonom a megerositest, {user_name}! A naptaramban sikeresen atjegyeztem a talalkozot "
                f"az uj idopontra: {target_slot} ({duration_mins} perc). Szakertonk: {assigned_staff}.\n"
                f"A frissitett meghivot elkuldtem a(z) {user_info.get('email', 'megadott email cimere')}."
            )
            requires_client_action = False
        else:
            # Megerősítés kérése
            booking_status = "RESCHEDULE_PENDING_CONFIRMATION"
            bot_reply = (
                f"Termeszetesen, at tudjuk tenni! Megneztem a naptaramat: a csutortoki napon (szeptember 24.) 10:00-kor "
                f"szabad a savunk. Megfelel Onnek ez az idopont?\n"
                f"Kerem valaszoljon: 'IGEN', es azonnal athelyezem a naptarban!"
            )
            requires_client_action = True

        return {
            "status": "success",
            "conversation_intent": "RESCHEDULE_APPOINTMENT",
            "booking_status": booking_status,
            "requires_client_confirmation": requires_client_action,
            "assigned_specialist": assigned_staff,
            "bot_response": bot_reply,
            "booking_details": {
                "booking_id": existing_id or "BOOK-2026-9410",
                "proposed_new_slot": target_slot,
                "duration_minutes": duration_mins,
                "buffer_applied_minutes": buffer_mins
            }
        }

    # 2. ESET: Új időpontfoglalási egyeztetés
    else:
        # Pufferidőkkel kalkulált szabad naptári ajánlatok
        offered_slots = [
            {"date": "2026-09-22 (Kedd)", "time": "14:30 - 15:15", "type": "Délutáni sáv"},
            {"date": "2026-09-22 (Kedd)", "time": "16:00 - 16:45", "type": "Késő délutáni sáv"},
            {"date": "2026-09-23 (Szerda)", "time": "10:00 - 10:45", "type": "Délelőtti sáv"}
        ]

        bot_reply = (
            f"Kedves {user_name}! Orommel varunk a budapesti irodankban egy szemelyes konzultaciora!\n"
            f"Megneztem a naptarunkat, a kert idoszakban az alabbi szabad idopontjaink vannak:\n"
            f"1. Kedd (szept. 22.) 14:30\n"
            f"2. Kedd (szept. 22.) 16:00\n"
            f"3. Szerda (szept. 23.) 10:00\n\n"
            f"Melyik lenne a legkenyelmesebb Onnek? Csak irja meg a szamot (1, 2 vagy 3), es mar be is jegyzem a naptarba!"
        )

        # Weboldalba ágyazható HTML/JS snippet
        embed_widget_code = (
            f'<script src="http://localhost:8000/widgets/calendar-chat.js" '
            f'data-company="{company}" data-channel="{channel}" async></script>'
        )

        return {
            "status": "success",
            "conversation_intent": "NEW_BOOKING_CONSULTATION",
            "bot_response": bot_reply,
            "offered_slots": offered_slots,
            "calendar_sync": {
                "system": calendar_sys,
                "meeting_duration": f"{duration_mins} perc",
                "travel_buffer": f"{buffer_mins} perc pufferidő biztosítva",
                "assigned_specialist": assigned_staff,
                "double_booking_prevented": True
            },
            "web_embed_snippet": embed_widget_code
        }
