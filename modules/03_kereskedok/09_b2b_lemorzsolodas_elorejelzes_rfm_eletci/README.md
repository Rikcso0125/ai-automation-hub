# Modul 09: B2B Lemorzsolódás Előrejelzés & RFM Életciklus Figyelő

## Áttekintés
A **09_b2b_lemorzsolodas_elorejelzes_rfm_eletci** modul a B2B nagykereskedelmi viszonteladók vásárlási tranzakcióit elemzi RFM (Recency, Frequency, Monetary) és idősoros anomália-detektálás alapján. Proaktívan észleli, ha egy partner rendelési gyakorisága lelassul vagy forgalma visszaesik, megelőzve a konkurenciához való észrevétlen átpártolást.

---

## Fő Funkciók

### 1. Kettős Lemorzsolódási Kockázat Elemzés (Dual Trigger Sensitivity)
- **Ciklusidő Késési Szorzó (Cycle Delay Multiplier):**
  - Méri a partner egyéni rendelési ritmusát (pl. átlagosan 12 naponta rendel).
  - Ha az utolsó vásárlás óta eltelt idő eléri az átlagos ciklus 1.5x-esét, figyelmeztető zónába lép; 2.5x felett magas lemorzsolódási riasztás lép életbe.
- **Forgalom Visszaesési Arány (Revenue Drop-off %):**
  - Összeveti az utolsó 30 nap költését a korábbi havi átlaggal (pl. 2,8M Ft -> 0 Ft: 100%-os kiesés).
- **RFM Szegmentáció:**
  - Besorolás: *Champions*, *Loyal Customers*, *Drifting / Need Attention*, *At-Risk High Churn*, *Dormant*.

### 2. Kategória-Kiesés & Konkurencia-Átpártolás Detektálás
- Észleli, ha a partner bizonyos kategóriákat (pl. csövek és szerelvények) hirtelen abbahagy vásárolni, miközben más termékeket még rendel:
  - *"Konkurencia-riasztás: A partner korábban havi 1,2M Ft értékben vásárolt rézcsövet, az elmúlt 45 napban 0 Ft. Valószínűsíthető konkurens beszállító belépése!"*

### 3. Testreszabható Visszatartó Ajánlatok (Tier-Adaptive Retention)
- **Gold / Platinum VIP Partnerek:**
  - Személyre szabott visszatérő bónusz levéltervezet (extra +5% kedvezmény a top vásárolt termékekre 14 napig + ingyenes helyszíni projektkiszállítás).
  - Vezetői tárgyalási forgatókönyv és 1-kattintásos telefonos híváslink.
- **Silver / Bronze Partnerek:**
  - Célzott elégedettségi kérdéssor és beszélgetésindító sablon az értékesítő számára.

### 4. Hibrid Riasztási Csatorna
- Azonnali riasztás (Telegram, Dashboard, Email) a VIP partnereknél (48 órás reakció SLA).
- Heti összesítő „At-Risk Partnerek” vezetői jelentés a hétfői sales meetingre.

---

## Adatbázisok és Naplózás
- **Lemorzsolódási Napló:** `data/b2b_lemorzsolodas_naplo.json`
- **Partner Törzs:** `data/b2b_partnerek.json`
- **Terméktörzs:** `data/termektorzs_katalogus.json`
