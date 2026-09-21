# 🎫 Készpénzes és Tankolási Blokkok 3 Másodperces Fotós Elszámolása (Module 5.04)

A terepen dolgozó szerelők, építésvezetők és technikusok a pénztárnál mobiltelefonnal lefotózzák a barkácsáruházi (Bauhaus, Obi, Praktiker, Würth) vagy benzinkúti (MOL, OMV, Shell) blokkot. A modul Vision AI technológiával 3 másodperc alatt kinyeri a tételes adatokat, elvégzi az ÁFA-bontást, összekapcsolja a céges gépjármű digitális menetlevelével, és GPS-pozíció alapján automatikusan a megfelelő kivitelezési projektre terheli a költséget.

---

## 🎯 Üzleti Érték és Funkciók

1. **⚡ Vision AI Blokkfelismerés & Menetlevél Szinkron (Opció C):**
   * Tételes anyagkinyerés (pl. csavarok, ragasztók, tiplik) 27%-os és 5%-os ÁFA-bontással, könyvelési kategóriákba sorolva.
   * Üzemanyag tankolási blokkoknál liter, egységár, üzemanyagtípus, rendszám (`ABC-890`) és km-óra állás automatikus kinyerése és rögzítése a céges digitális flottanyilvántartásban.

2. **📍 Hibrid Geolokáció & Keretösszeg-Védelem (Opció C):**
   * A mobilfotó GPS koordinátái és a dolgozó aktív digitális jelenléte alapján automatikusan párosítja a kivitelezési projekttel (pl. `PRJ-2026-AUDI-G3`).
   * Valós idejű költségkeret-ellenőrzés: vizsgálja a projekt megmaradt anyagkeretét, túllépés esetén azonnali vezetői vészjelzést ad.

3. **💳 Céges Kártya Párosítás & Vezetői Jóváhagyási Kapu (Opció C):**
   * 100%-os egyezés vizsgálata a céges bankkártya tranzakcióval (összeg, időpont).
   * 30 000 Ft feletti vásárlásoknál 1-kattintásos vezetői felülvizsgálati kapu (`status: PENDING_PROJECT_DIRECTOR_APPROVAL`).
   * Azonnali megnyugtató mobil visszajelzés a terepi dolgozónak mobilon / Telegramon.

---

## ⚙️ Konfigurációs Paraméterek (`config.schema.json`)

| Mező | Típus | Alapérték | Leírás |
|------|-------|-----------|--------|
| `receipt_recognition_mode` | string | `"vision_hardware_mileage_sync"` | Blokkfelismerési és menetlevél szinkron mód |
| `project_allocation_mode` | string | `"hybrid_geo_work_order_budget"` | Projektszám és keretösszeg-vizsgálati mód |
| `accounting_workflow` | string | `"realtime_erp_card_match_gate"` | Számviteli és bankkártya-párosítási mód |
| `manager_approval_threshold_huf` | integer | `30000` | Vezetői jóváhagyási értékhatár (Ft) |
| `notification_channel` | string | `"telegram"` | Riasztási csatorna (telegram, sms, email) |

---

## 📡 Webhook Végpont

* **URL:** `POST http://<szerver-ip>:8000/api/v1/modules/04_keszpenzes_es_tankolasi_blokkok_3_masodp/test`
* **Naplófájl:** `data/keszpenzes_tankolasi_blokk_naplo.json`
