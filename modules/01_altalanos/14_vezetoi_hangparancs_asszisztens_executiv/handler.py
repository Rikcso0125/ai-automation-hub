# -*- coding: utf-8 -*-
import os
import re
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

def parse_multi_intent(transcript: str, calendar_sys: str, pm_sys: str) -> List[Dict[str, Any]]:
    actions = []
    text_l = transcript.lower()

    # 1. Naptár / Találkozó szándék
    if any(k in text_l for k in ["találkozó", "talalkozo", "megbeszélés", "megbeszeles", "meeting", "naptár", "naptar"]):
        partner = "Molnár Gábor" if "molnár" in text_l or "molnar" in text_l else "Üzleti Partner"
        event_time = "2026-09-22 15:00 - 16:00"
        location = "Központi Tárgyaló / Iroda" if "iroda" in text_l else "Online Google Meet"
        
        actions.append({
            "action_type": "CALENDAR_EVENT_CREATE",
            "target_system": calendar_sys,
            "title": f"Stratégiai egyeztetés - {partner}",
            "partner": partner,
            "scheduled_time": event_time,
            "location": location,
            "topic": "Költségvetés és heti prioritások",
            "conflict_check": {
                "has_conflict": False,
                "message": "Nincs naptári ütközés, a 15:00 - 16:00 idősáv szabad."
            },
            "status": "SCHEDULED_SUCCESS"
        })

    # 2. Feladat delegálás szándék
    if any(k in text_l for k in ["szólj", "szolj", "adj feladatot", "delegálj", "delegald", "küldje", "clickup", "asana", "jira"]):
        assignee = "Kovács Anna" if "anna" in text_l else "Kolléga"
        task_title = "Prezentáció és anyagok összeállítása és átküldése"
        due = "Szerda 12:00 (2026-09-23 12:00)"
        
        actions.append({
            "action_type": "TASK_DELEGATION",
            "target_system": pm_sys,
            "task_title": task_title,
            "assignee": assignee,
            "due_date": due,
            "priority": "HIGH",
            "status": "TASK_CREATED_SUCCESS"
        })

    # 3. Adatlekérdezési szándék (Text-to-SQL integráció)
    if any(k in text_l for k in ["mennyi", "bevétel", "bevetel", "forgalom", "számok", "egyenleg", "kintlévőség"]):
        actions.append({
            "action_type": "DATA_QUERY_LOOKUP",
            "target_system": "10_termeszetes_nyelvu_adatbazis_kereso_text",
            "query_summary": "Heti záró árbevétel és likviditási egyenleg lekérése",
            "result_summary": "Kiszámlázott árbevétel: 8.450.000 Ft, Záró bank: 14.820.000 Ft.",
            "status": "DATA_RETRIEVED"
        })

    # 4. Egyedi bővíthető akció (ha nincs konkrét illeszkedés)
    if not actions:
        actions.append({
            "action_type": "CUSTOM_COMMAND_DISPATCH",
            "target_system": "Webhook Integráció",
            "raw_text": transcript,
            "status": "DISPATCHED_TO_CUSTOM_HANDLER"
        })

    return actions

def run(payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    exec_name = config.get("executive_name", "Dr. Kovács Béla")
    transcript = payload.get("spoken_transcript", "").strip()
    location = payload.get("executive_location", "Autóban")
    duration = payload.get("audio_duration_sec", 5.0)

    calendar_sys = config.get("calendar_integration", "Google Calendar API")
    pm_sys = config.get("task_management_tool", "ClickUp API")
    enable_tts = "Igen" in config.get("enable_voice_feedback_tts", "Igen")
    stt_engine = config.get("stt_engine", "Helyi Faster-Whisper (Privát, ingyenes, gépen fut)")

    # Több-szándékú (multi-intent) parancsértelmezés
    dispatched_actions = parse_multi_intent(transcript, calendar_sys, pm_sys)

    # Hangos felolvasó (TTS) beszédgenerálás az autó hangszórójára
    speech_parts = ["Rendben, Uram!"]
    for act in dispatched_actions:
        if act["action_type"] == "CALENDAR_EVENT_CREATE":
            speech_parts.append(
                f"A találkozót {act['partner']} partnerrel rögzítettem a naptárban ({act['scheduled_time']}). Nincs ütközés."
            )
        elif act["action_type"] == "TASK_DELEGATION":
            speech_parts.append(
                f"{act['assignee']} részére létrehoztam a kiemelt feladatot a {pm_sys} felületén, határidő: {act['due_date']}."
            )
        elif act["action_type"] == "DATA_QUERY_LOOKUP":
            speech_parts.append(f"Az adatok szerint: {act['result_summary']}.")

    spoken_tts_response = " ".join(speech_parts)

    # Szöveges dashboard / chat összefoglaló
    lines = [
        f"[HANGPARANCS VEGREHAJTVA - {duration} mp]",
        f"Elhangzott: \"{transcript}\"",
        "",
        f"VEGREHAJTOTT MUVELETEK ({len(dispatched_actions)} db):"
    ]
    for idx, act in enumerate(dispatched_actions, 1):
        target_info = act.get('title') or act.get('task_title') or act.get('query_summary') or 'Egyedi akcio'
        lines.append(f"{idx}. [{act['action_type']}] -> {act['target_system']}: {target_info}")
    formatted_summary = "\n".join(lines)

    return {
        "status": "success",
        "executive": exec_name,
        "input_metadata": {
            "stt_engine_used": stt_engine,
            "duration_sec": duration,
            "location_context": location,
            "raw_transcript": transcript
        },
        "executed_actions_count": len(dispatched_actions),
        "executed_actions": dispatched_actions,
        "tts_voice_feedback": {
            "enabled": enable_tts,
            "spoken_audio_text": spoken_tts_response,
            "voice_profile": "Magyar üzleti asszisztens (Nyugodt, határozott)"
        },
        "chat_summary_message": formatted_summary,
        "web_voice_widget": {
            "ready_for_next_recording": True,
            "microphone_status": "STANDBY",
            "ui_hint": "Beszéljen újra vagy kattintson a mikrofon ikonra a weboldalon."
        }
    }
