# 🎙️ Voice-to-Action Napi Munkalapok és Építési Napló Hangjegyzetből (Module 5.01)

A helyszínen lévő szakember vagy művezető mobiltelefonon egy 30-60 másodperces kötetlen hangüzenetben mondja el a napi elvégzett munkát, felhasznált anyagokat és akadályoztató tényezőket. A modul OpenAI Whisper AI motorral átírja, NLP entitáskinyeréssel strukturálja, és automatikusan elkészíti a **191/2009. (IX. 15.) Korm. rendelet** szerinti hivatalos e-Építési Napló bejegyzést, valamint a belső rezsióradíjas elszámoló munkalapot.

---

## 🎯 Üzleti Érték és Funkciók

1. **🎙️ Whisper AI Hangjegyzet & Entitáskinyerés (Opció C):**
   * Támogatja a közvetlen hangfájl feltöltést (Telegram/WhatsApp OGG/MP3 hangüzenet) és a kész szöveges átiratot is.
   * Automatikusan kinyeri a létszámot, neveket, munkaórákat (fő x óra), beépített anyagokat cikkszámmal/mennyiséggel, és az időjárási körülményeket.

2. **🏛️ 191/2009. Korm. Rendelet Kompatibilis e-Napló (Opció C):**
   * Hivatalos e-Építési Napló formátum: Létszám-összesítő, elvégzett technológiai munkafázisok MSZ szabvány hivatkozással.
   * Szállítói megfelelőségi nyilatkozatok (DoP / CE jelölés) nyilvántartása.
   * Hivatalos akadályoztatási jegyzőkönyv bejegyzés a határidő-hosszabbítási és kötbérmentességi jogalap biztosítására.

3. **📊 Projektkontrolling & Főmérnöki Jóváhagyási Kapu (Opció C):**
   * Belső rezsióradíj alapú munkadíj és tételes anyagköltség kalkuláció.
   * Profit Margin és költségkeret figyelés.
   * 1-kattintásos vezetői / műszaki ellenőri jóváhagyási kapu (`status: pending_review` -> `approved`), PDF és JSON export.

---

## ⚙️ Konfigurációs Paraméterek (`config.schema.json`)

| Mező | Típus | Alapérték | Leírás |
|------|-------|-----------|--------|
| `hourly_rate_huf` | integer | `7500` | Belső elszámoló rezsióradíj (Ft/óra) |
| `auto_approve_threshold_hours` | integer | `40` | Automatikus jóváhagyási küszöb (óra) |
| `weather_station_id` | string | `"OMSZ-BUD-01"` | OMSZ időjárás-állomás kódja |
| `require_manager_approval` | boolean | `true` | Kötelező vezetői / műszaki ellenőri jóváhagyási kapu |
| `notify_email` | string | `"epitesvezeto@vallalkozas.hu"` | Műszaki vezető értesítési e-mail címe |

---

## 📡 Webhook Végpont

* **URL:** `POST http://<szerver-ip>:8000/api/v1/modules/01_voice_to_action_napi_munkalapok_es_epite/test`
* **Naplófájl:** `data/epitesi_naplo_hangjegyzet_naplo.json`
