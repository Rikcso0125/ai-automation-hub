# 🧠 Telefonos Hang-Biometria és Frusztráció-Detektálás Hívásokban (Module 5.06)

Ügyfélszolgálati és diszpécseri telefonos hibabejelentő hívásoknál a modul valós időben elemzi a beszélő pszichoakusztikai hanghullámait (hangerő decibel kiugrások, megemelkedett hangmagasság, beszédsebesség, közbevágások) és a szemantikai szándékot (termeléskiesés, azonnali kártérítés és kötbér emlegetése). Hang-biometrikus ujjlenyomat alapján azonosítja a hívó gyárigazgatót / üzemvezetőt és az érintett ipari gépparkot, valamint kritikus stressz index esetén (>75%) azonnali Warm Transferrel és fülbe-súgott Whisper Coach felkészítéssel átadja a hívást a felelős műszaki igazgatónak.

---

## 🎯 Üzleti Érték és Funkciók

1. **📊 Hibrid Pszichoakusztikai & Szemantikai Feszültségmérés (Opció C):**
   * Párhuzamosan méri az akusztikai stresszt (89 dB hangerőcsúcs, 215 szó/perc beszédsebesség, +65 Hz pitch tremor, 4 közbevágás) és a szemantikai fenyegetettséget.
   * Valós idejű **0-100%-os Frusztrációs Index** generálása másodpercenként.

2. **👤 Biometrikus Hang-Ujjlenyomat & VIP SLA Géppark Kontextus (Opció C):**
   * A bejövő hanghullám alapján (Voiceprint hash) 99.1%-os biztonsággal azonosítja a hívót, rejtett vagy új számról hívva is.
   * Betölti a céges szerződéses feltételeket (Tier-1 VIP, 2 órás kritikus hibaelhárítási SLA) és az érintett gyártósort (Sacmi PH 6500 hidraulikus kerámia sajtológép).

3. **🎧 Valós Idejű „Warm Transfer” & Whisper Coach + Push Riasztás (Opció C):**
   * Azonnali Telegram / SMS push vészriasztás a felelős műszaki vezetőnek (`Kovács István`).
   * Élő hívásátkapcsolás közben 4 másodperces szóbeli fülbe-súgás a fogadó mérnöknek a kicsöngés alatt ("Whisper Coach"), miközben képernyőjére vetíti a javasolt megnyugtató nyitómondatot és a legközelebbi szervizautó pozícióját (40 perc kiszállási SLA).

---

## ⚙️ Konfigurációs Paraméterek (`config.schema.json`)

| Mező | Típus | Alapérték | Leírás |
|------|-------|-----------|--------|
| `frustration_detection_mode` | string | `"hybrid_psychoacoustic_semantic"` | Feszültség-detektálási mód |
| `caller_identification_mode` | string | `"biometric_voiceprint_vip_sla"` | Hívóazonosítási mód |
| `escalation_workflow` | string | `"warm_transfer_whisper_coach_push"` | Eszkalációs és hívásátadási mód |
| `frustration_threshold_pct` | integer | `75` | Kritikus frusztrációs küszöb (%) |
| `sla_critical_response_hours` | integer | `2` | Kritikus VIP SLA kiszállási idő (óra) |
| `notification_channel` | string | `"telegram"` | Riasztási csatorna (telegram, sms, email) |

---

## 📡 Webhook Végpont

* **URL:** `POST http://<szerver-ip>:8000/api/v1/modules/06_telefonos_hang_biometria_es_frusztracio_/test`
* **Naplófájl:** `data/telefonos_hang_biometria_naplo.json`
