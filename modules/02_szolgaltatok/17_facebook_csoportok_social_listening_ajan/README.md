# 📢 Facebook Csoportok Social Listening (Ajánláskérések Figyelése)

**Modul azonosító:** `17_facebook_csoportok_social_listening_ajan`  
**Kategória:** Szolgáltató Cégek Automatizációi (2. Kategória / 17. Modul)

---

## 🎯 Cél és Működési Áttekintés

A lakossági és szakmai szolgáltatók legforróbb organikus leadjei a Facebook csoportokban születnek: naponta jelennek meg bejegyzések, mint például:  
*„Tudtok jó klímást / villanyszerelőt a XI. kerületben?”*,  
*„Megbízható szakembert keresek azonnal garanciával!”*.

A probléma: a cégek órákkal vagy napokkal később veszik észre ezeket a posztokat, amikor a konkurencia már elvitte a munkát, vagy kéretlen spamszerű reklámokat szórnak a kommentmezőbe, amit a csoportadminok azonnal törölnek.

Ez a modul autonóm figyelőként (Social Listening) működik:
1. **Kulcsszavas és geolokációs szűrés:** Figyeli a megadott csoportokat, azonnal felismeri az ajánláskérő szándékot és összeveti a kiszállási zónákkal.
2. **Negatív kulcsszószűrő:** Kiszűri a spameket, álláshirdetéseket, panaszokat és nem releváns posztokat (0 fals riasztás).
3. **Segítőkész szakértői komment generálás:** Nem tolakodó direkt reklám, hanem valódi értéket adó szakmai tanáccsal mutatja be a vállalkozást, naptárfoglalási linkkel és telefonszámmal.
4. **Privát Messenger DM vázlat:** Előkészít egy közvetlen, udvarias privát üzenetet is a posztíró megkereséséhez.
5. **1-Kattintásos értékesítői kapu & riasztás:** Azonnal riasztja a sales csapatot (Telegram / WhatsApp / Dashboard) a bejegyzés linkjével és 1-kattintásos jóváhagyó gombbal (5 perces reakcióidő cél).
6. **Perzisztens lead-követés:** Minden beérkező leadet elment a `data/facebook_leads_naplo.json` fájlba statisztikákhoz és konverzióméréshez.

---

## ⚙️ Főbb Konfigurációs Beállítások

| Mező | Típus | Alapérték | Leírás |
|------|-------|-----------|--------|
| `company_name` | `string` | `"ProfiKlíma & Épületgépészet Kft."` | Vállalkozás neve |
| `company_specialty` | `string` | `"Lakossági és ipari klíma..."` | Kiemelt szakterület és referenciák |
| `company_phone` | `string` | `"+36 30 123 4567"` | Telefonszám |
| `booking_url` | `string` | `"https://profiklima.hu/idopontfoglalas"` | Naptárfoglaló link |
| `monitored_groups` | `array` | `["Újbuda - XI. kerületiek", ...]` | Megfigyelt csoportok listája |
| `target_locations` | `array` | `["Budapest", "XI. kerület", ...]` | Kiszállási célterületek |
| `trigger_keywords` | `array` | `["klímás", "ajánljatok", ...]` | Ajánláskérő kulcsszavak |
| `negative_exclusion_keywords` | `array` | `["állás", "felvétel", ...]` | Kizáró spamszavak |
| `min_relevance_score` | `integer` | `70` | Riasztási küszöb (0-100) |
| `response_tone` | `string` | `"tegezo_baratsagos"` | Tegező barátságos vagy magázó hivatalos |
| `approval_mode` | `string` | `"manual_approval_only"` | Manuális jóváhagyás vagy auto-poszt |
| `alert_channels` | `array` | `["telegram", "whatsapp", "dashboard"]` | Riasztási csatornák |
| `leads_db_path` | `string` | `"data/facebook_leads_naplo.json"` | Perzisztens lead napló |

---

## 📡 API és Webhook Végpontok

- **Teszt és kiértékelés:** `POST /api/v1/modules/17_facebook_csoportok_social_listening_ajan/test`
- **Külső Webhook fogadás:** `POST /api/v1/webhook/17_facebook_csoportok_social_listening_ajan`
- **1-Kattintásos jóváhagyás:** `POST /api/v1/modules/17_facebook_csoportok_social_listening_ajan/test` (`{"action": "APPROVE_LEAD", "lead_id": "..."}`)
