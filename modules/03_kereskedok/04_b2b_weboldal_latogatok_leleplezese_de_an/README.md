# 🕵️ B2B Weboldal Látogatók Leleplezése (De-Anonymization)

**Modul azonosító:** `04_b2b_weboldal_latogatok_leleplezese_de_an`  
**Kategória:** Kereskedő Cégek Automatizációi (3. Kategória / 04. Modul)

---

## 🎯 Cél és Működési Áttekintés

A B2B weboldalakra érkező látogatók 95–97%-a soha nem tölt ki ajánlatkérő űrlapot: megnézik a termékeket, a nagykereskedelmi árlistát, majd távoznak.
Ez a modul leleplezi ezeket a rejtett forró érdeklődőket:
1. **Reverse IP & Network Intelligence:** Felismeri a látogató mögött álló vállalkozást vállalati IP és domain adatok alapján.
2. **Lakossági Spamszűrő:** Kiszűri a Telekom, Vodafone, Digi, Yettel lakossági dinamikus hálózatokat, így a sales csapat csak valódi B2B cégekre fókuszál.
3. **Intent Scoring (Vásárlási szándék pontozás):** 0–100-as skálán méri a látogatás sürgősségét (árlista megtekintése, termékkatalógus böngészése, időtartam, visszatérő látogató).
4. **Döntéshozó-kutatás:** Megkeresi a cég kulcs vezetőit (Ügyvezető, Beszerzési vezető, Főmérnök) LinkedIn profillal és email címmel.
5. **Személyre szabott hideg megkeresési forgatókönyv:** Kész telefonos nyitószöveget és email vázlatot ír az értékesítőnek az adott cég profiljára szabva.
6. **Azonnali Forró Riasztás & CRM Szinkron:** 70 pont felett azonnali Telegram/WhatsApp riasztást küld 1-kattintásos CRM felvételi gombbal.
7. **Perzisztens napló:** `data/b2b_weboldal_latogatok.json`.

---

## ⚙️ Főbb Konfigurációs Beállítások

| Mező | Típus | Alapérték | Leírás |
|------|-------|-----------|--------|
| `min_hot_intent_score` | `integer` | `70` | Forró lead riasztási küszöb (0-100) |
| `excluded_isps` | `array` | `["Magyar Telekom", "Vodafone", ...]` | Kizárt lakossági szolgáltatók |
| `target_industries` | `array` | `["Épületgépészet", "Klíma", ...]` | Kiemelt céliparágak |
| `alert_channels` | `array` | `["telegram", "whatsapp", "dashboard"]` | Riasztási csatornák |
| `visitors_db_path` | `string` | `"data/b2b_weboldal_latogatok.json"` | Látogatói adatbázis útvonala |

---

## 📡 API és Webhook Végpontok

- **Látogatási esemény kiértékelése:** `POST /api/v1/modules/04_b2b_weboldal_latogatok_leleplezese_de_an/test`
- **Külső Webhook fogadás:** `POST /api/v1/webhook/04_b2b_weboldal_latogatok_leleplezese_de_an`
- **1-Kattintásos CRM átvétel:** `POST /api/v1/modules/04_b2b_weboldal_latogatok_leleplezese_de_an/test` (`{"action": "CLAIM_LEAD", "lead_id": "..."}`)
