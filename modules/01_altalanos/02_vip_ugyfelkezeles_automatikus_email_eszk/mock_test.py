# -*- coding: utf-8 -*-
import json
from handler import run

with open("test_payload.json", "r", encoding="utf-8") as f:
    payload = json.load(f)

config = {
    "company_name": "ProfiTech Hungary Kft.",
    "vip_detection_mode": "Mindkettő (VIP Partner Lista + AI Hangulatelemzés)",
    "vip_domains_and_emails": "mol.hu, otp.hu, audi.hu",
    "urgent_keywords": "azonnal, sürgős, leállás, kötbér, kár, per, hiba",
    "alert_channels": "Mindhárom (Telegram + Telnyx SMS + Email)",
    "executive_phone": "+36301234567",
    "executive_email": "vezeto@profitech.hu",
    "auto_reply_to_vip": "Igen (Bekapcsolva)",
    "auto_reply_message": "Tisztelt Dr. Varga Zoltán!\n\nKiemelt partnerként jelzését közvetlenül a cégvezetéshez továbbítottuk. Ügyvezetőnk 15 percen belül visszahívja Önt a megadott számon a helyzet azonnali elhárítására.\n\nÜdvözlettel,\nÜgyvezetés"
}

print("=== VIP ÜGYFÉLKEZELÉS & ESZKALÁCIÓ TESZT ===")
res = run(payload, config)
print(json.dumps(res, indent=2, ensure_ascii=False))
