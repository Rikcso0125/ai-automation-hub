# -*- coding: utf-8 -*-
import json
from handler import run

import os
payload_path = os.path.join(os.path.dirname(__file__), "test_payload.json")
with open(payload_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

config = {
    "company_name": "ProfiTech Hungary Kft.",
    "stt_engine": "Helyi Faster-Whisper (Privát, ingyenes, gépen fut)",
    "task_management_system": "ClickUp API",
    "require_human_approval": "Igen (Jóváhagyási és szerkesztési fázis a szinkron előtt)",
    "send_summary_to_participants": "Igen (Minden résztvevő megkapja a saját feladatait)"
}

print("=== AUTONÓM ÉRTEKEZLET JEGYZETELÉS & TEENDŐ SZINKRON TESZT ===")
res = run(payload, config)
print(json.dumps(res, indent=2, ensure_ascii=False))
