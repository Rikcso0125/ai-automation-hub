# ✅ Minőségbiztosítási & Munkavédelmi Ellenőrző Robot (Checklist Audit - Module 5.03)

Műszaki tervek, kivitelezési helyszínek és részátadási jegyzőkönyvek fotóinak és leírásainak Vision AI auditja a kötelező jogszabályi szabványok (1993. évi XCIII. Munkavédelmi törvény és OTSZ 54/2014. BM rendelet) szerint, azonnali Stop-Work határozattal, hatósági bírságkockázat-becsléssel és fotós Before/After igazolási kapuval.

---

## 🎯 Üzleti Érték és Funkciók

1. **👷 Hibrid Munkavédelmi & Műszaki Átadási Kombinált Audit (Opció C):**
   * Párhuzamosan ellenőrzi a munkavédelmi egyéni védőfelszereléseket (PPE: zuhanásgátló hevederzet, rögzített életvonal, védősisak állszíj) és a műszaki minőséget (OTSZ tűzgátló lezárások, MSZ HD 60364 érintésvédelem).
   * Tételes nem-megfelelőségi jelentés (NCR lista) szabványhivatkozásokkal.

2. **⚖️ Jogszabályi & Hatósági Kockázati Motor (Opció C):**
   * Mvt. és OTSZ szerinti bírságsáv kalkuláció (pl. 500 000 - 3 000 000 Ft munkaügyi bírságkockázat közvetlen súlyos veszélyeztetés esetén).
   * Automata **Stop-Work Order** munkabeszüntetési határozat közvetlen élet- és zuhanásveszély esetén az érintett munkafázisra.

3. **📱 Valós Idejű Terepi Riasztás & Fotós Igazolási Kapu (Opció C):**
   * Azonnali Telegram / SMS értesítés a helyszíni felelős műszaki vezetőnek és az alvállalkozónak.
   * Kijelölt határidők (2 óra azonnali életveszély esetén, 24 óra műszaki hiányosságnál).
   * Digitális Before/After igazolási kapu: a javítás elvégzése után a szerelő fotót tölt fel, amit az AI ellenőriz és automatikusan rögzít az e-Építési Naplóban.

---

## ⚙️ Konfigurációs Paraméterek (`config.schema.json`)

| Mező | Típus | Alapérték | Leírás |
|------|-------|-----------|--------|
| `audit_scope` | string | `"hybrid_safety_and_technical_audit"` | Ellenőrzési hatókör és terület |
| `severity_rule_engine` | string | `"regulatory_legal_penalty_engine"` | Kockázati és jogszabályi bírságmotor |
| `remediation_workflow` | string | `"realtime_push_photo_gate"` | Javítási munkafolyamat és igazoló kapu |
| `stop_work_on_critical_danger` | boolean | `true` | Azonnali munkabeszüntetés életveszély esetén |
| `legal_framework` | string | `"1993. évi XCIII. Mvt. & OTSZ"` | Alkalmazott jogszabályi keret |
| `notification_channel` | string | `"telegram"` | Riasztási csatorna (telegram, email, sms, slack) |

---

## 📡 Webhook Végpont

* **URL:** `POST http://<szerver-ip>:8000/api/v1/modules/03_minosegbiztositasi_munkavedelmi_ellenorz/test`
* **Naplófájl:** `data/minosegbiztositas_audit_naplo.json`
