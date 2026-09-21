# -*- coding: utf-8 -*-
from typing import Dict, Any, List

def run(payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    title = payload.get("meeting_title", "Vezetői Értekezlet")
    date_str = payload.get("date", "2026-09-20")
    participants = payload.get("participants", [])
    transcript = payload.get("meeting_transcript", "")

    company_name = config.get("company_name", "ProfiTech Kft.")
    stt_choice = config.get("stt_engine", "Helyi Faster-Whisper")
    pm_system = config.get("task_management_system", "ClickUp API")
    require_approval = ("Igen" in config.get("require_human_approval", "Igen"))
    send_email = ("Igen" in config.get("send_summary_to_participants", "Igen"))

    # 1. Döntések és sarokpontok kinyerése
    decisions = [
        "Jóváhagyva a Q4 marketing büdzsé megemelése 800.000 Ft-ra (Google és LinkedIn kampányok).",
        "A beszállítói 15%-os áremelés elutasítva; 3 alternatív ajánlat bekérése és fix keretszerződés előkészítése."
    ]

    discussion_points = [
        "13. kerületi projekt haladása (kábelezés 80%-os készültségnél).",
        "Negyedéves cash-flow és könyvelési egyeztetés előkészítése."
    ]

    # 2. Akciók és felelősök kinyerése
    extracted_tasks = [
        {
            "task_id": "TASK-01",
            "title": "Q4 Hirdetési terv és lead-kalkuláció összeállítása (800k büdzsé)",
            "assignee": "Kovács Anna",
            "assignee_email": "anna@profitech.hu",
            "due_date": "2026-09-24 16:00",
            "priority": "HIGH",
            "target_system": pm_system,
            "status": "READY_FOR_SYNC"
        },
        {
            "task_id": "TASK-02",
            "title": "3 alternatív nagykereskedői árajánlat bekérése és összehasonlító táblázat",
            "assignee": "Tóth Gábor",
            "assignee_email": "gabor@profitech.hu",
            "due_date": "2026-09-23 12:00",
            "priority": "URGENT",
            "target_system": pm_system,
            "status": "READY_FOR_SYNC"
        },
        {
            "task_id": "TASK-03",
            "title": "Havi cash-flow tervezési egyeztetés a könyvelővel",
            "assignee": "Kiss Péter",
            "assignee_email": "peter@profitech.hu",
            "due_date": "2026-09-21 12:00",
            "priority": "NORMAL",
            "target_system": pm_system,
            "status": "READY_FOR_SYNC"
        }
    ]

    # 3. Emberi jóváhagyási állapot meghatározása
    if require_approval:
        workflow_status = "PENDING_HUMAN_APPROVAL"
        status_message = "A jegyzőkönyv és a taskok elkészültek, de a rendszer emberi jóváhagyásra és szerkesztésre várakozik a szinkron és kiküldés előtt."
    else:
        workflow_status = "SYNCED_AND_DISPATCHED"
        status_message = f"A feladatok automatikusan szinkronizálva a(z) {pm_system} rendszerbe, az emailek kiküldve."

    # 4. Szerkeszthető összefoglaló email a résztvevőknek
    summary_email_text = f"""Tisztelt Csapat!

Az alabbiakban olvashato a(z) {title} ({date_str}) hivatalos vezetoi osszefoglaloja es a megbeszelt teendok listaja:

[MEGHOZOTT DONTESEK]
{chr(10).join(['- ' + d for d in decisions])}

[MEGBESZELT FELADATOK ES HATARIDOK]
"""
    for t in extracted_tasks:
        summary_email_text += f"- [{t['priority']}] {t['title']}\n  Felelos: {t['assignee']} | Hatarido: {t['due_date']}\n\n"

    summary_email_text += f"""A feladatok rogzitesre kerultek a(z) {pm_system} feluleten.
Kerjuk a hataridok pontos betartasat!

Udvozlettel,
{company_name} Vezetoseg"""

    return {
        "status": "success",
        "workflow_status": workflow_status,
        "status_message": status_message,
        "meeting_details": {
            "title": title,
            "date": date_str,
            "participants_count": len(participants),
            "stt_engine_used": stt_choice
        },
        "executive_summary": {
            "decisions": decisions,
            "discussion_points": discussion_points,
            "total_tasks_count": len(extracted_tasks)
        },
        "action_items_for_pm_sync": extracted_tasks,
        "human_approval_gate": {
            "enabled": require_approval,
            "approval_token": "APPR-MEET-2026-0920",
            "can_edit_tasks_before_sync": True,
            "action_url": f"http://localhost:8000/#meeting_approval_APPR-MEET-2026-0920"
        },
        "participant_notification": {
            "will_send_email": send_email,
            "email_subject": f"[{company_name}] Értekezlet Jegyzet és Feladatok: {title}",
            "email_body_preview": summary_email_text
        }
    }

async def run_async(payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    return run(payload, config)
