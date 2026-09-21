# 🎯 B2B Hideg Lead-Kutatás & Hiper-perszonalizált Megkeresés

**Modul azonosító:** `05_b2b_hideg_lead_kutatas_hiper_perszonaliz`  
**Kategória:** Kereskedő Cégek Automatizációi (3. Kategória / 05. Modul)

---

## 🎯 Cél és Működési Áttekintés

A B2B kereskedelemben az új viszonteladók és kivitelezők megnyerése kritikus fontosságú, de a sablonos tömeges marketing leveleket a cégvezetők és beszerzők 99%-ban törlik.
Ez a modul autonóm B2B hideg megkeresési rendszert valósít meg:
1. **Intelligens Célcsoport-kutatás:** Apollo, Clay és nyilvános cégadatbázisok alapján azonosítja a releváns cégeket (iparág, létszám, árbevétel, földrajzi régió).
2. **Weboldal & Projektreferencia elemzés:** Kigyűjti a cég friss referenciáit (pl. egy nemrég átadott irodaházat vagy ipari csarnokot).
3. **Szerkeszthető, 3-lépcsős Hiper-perszonalizált Levélsorozat:**
   - **1. Levél (0. nap):** Személyre szabott jégtörő a konkrét projektre + 22%-os nagykereskedelmi viszonteladói árréselőny.
   - **2. Levél (4. nap):** Valós esettanulmány a raktári pontosságról és azonnali elérhetőségről.
   - **3. Levél (8. nap):** Elegáns lezáró / breakup levél, naptárfoglalási lehetőséggel.
4. **Auto-Stop on Reply:** Amint a partner válaszol vagy időpontot foglal, a további emailek azonnal leállnak.
5. **Választható Működési Mód:**
   - **A opció:** Értékesítői vezetői jóváhagyási kapu (1-kattintásos indító gomb).
   - **B opció:** Automatizált Drip küldés beépített domainvédelemmel (napi max. 25 levél).
6. **Perzisztens Kampánynapló:** `data/b2b_hideg_leadek_naplo.json`.

---

## ⚙️ Főbb Konfigurációs Beállítások

| Mező | Típus | Alapérték | Leírás |
|------|-------|-----------|--------|
| `company_name` | `string` | `"ProfiGépész Nagykereskedelmi Kft."` | Nagykereskedés neve |
| `sender_name` | `string` | `"Kovács László"` | Feladó neve |
| `sender_title` | `string` | `"B2B Értékesítési Igazgató"` | Feladó pozíciója |
| `calendar_booking_url` | `string` | `"https://profigepesz.hu/talalkozo-egyeztetes"` | Naptárfoglaló link |
| `sending_mode` | `string` | `"manual_approval_only"` | A vagy B opció |
| `daily_drip_limit` | `integer` | `25` | Napi maximális küldési limit |
| `auto_stop_on_reply` | `boolean` | `true` | Automata leállítás válasz esetén |
| `leads_db_path` | `string` | `"data/b2b_hideg_leadek_naplo.json"` | Adatbázis útvonala |

---

## 📡 API és Webhook Végpontok

- **Kampány generálás:** `POST /api/v1/modules/05_b2b_hideg_lead_kutatas_hiper_perszonaliz/test`
- **Kampány jóváhagyása:** `POST /api/v1/modules/05_b2b_hideg_lead_kutatas_hiper_perszonaliz/test` (`{"action": "APPROVE_CAMPAIGN", "campaign_id": "..."}`)
- **Válasz rögzítése:** `POST /api/v1/modules/05_b2b_hideg_lead_kutatas_hiper_perszonaliz/test` (`{"action": "RECORD_REPLY", "campaign_id": "...", "prospect_email": "..."}`)
