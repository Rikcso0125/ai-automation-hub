# 🤖 Zárt Hatósági Portálok és Régi ERP-k AI-RPA Böngésző Robotjai (Module 5.05)

Emberi beavatkozás nélkül lép be a zárt állami portálokra (ÉTDR, e-Közmű, Ügyfélkapu+, DÁP) és a modern API nélküli régi ERP rendszerekbe (pl. IBM AS400, régebbi raktárprogramok). Önállóan hitelesíti és feltölti a PDF tervdokumentációkat AVDH digitális aláírással és időbélyeggel, kitölti az űrlapmezőket, kezeli a DOM változásokat (önjavító navigáció), letölti a hatósági határozatot és tértivevényt, valamint szinkronizálja a belső rendszereket.

---

## 🎯 Üzleti Érték és Funkciók

1. **🏛️ Zárt Állami Portálok & Régi ERP Hibrid Navigáció (Opció C):**
   * Támogatja az ÉTDR (Építésügyi Hatósági Rendszer), e-Közmű és Ügyfélkapu+ felületeket.
   * Vizuális látómodellel vezérelt böngésző robot, amely nem omlik össze a weboldalak dizájn-frissítéseinél.

2. **🔐 Zero-Trust Kriptográfiai Vault & AVDH Minősített Aláírás (Opció C):**
   * Hardveresen védett szoftveres TOTP generálás a kétlépcsős belépéshez.
   * Cégvezetői mobil push jóváhagyási kapu a hatósági beadás előtt.
   * Automatikus **AVDH digitális aláírás és minősített időbélyeg** elhelyezése a PDF tervrajzokon és műszaki leírásokon.

3. **🔄 Önjavító DOM-Navigáció & Kétirányú ERP/Felhő Szinkron (Opció C):**
   * Ha a hatósági portálon egy gomb azonosítója megváltozik (pl. `#btn-upload` helyett `div.dropzone-v2`), az AI látómodell 320 ms alatt automatikusan felismeri az új elemet (Self-Healing DOM).
   * A beadás után azonnal letölti az időbélyegzett hatósági határozatot és ügyiratszámot (pl. `BP-11/EPIT/2026-04812-3`), majd terminál-emulációval visszatölti a régi AS400 belső rendszerbe és a központi Google Drive / OneDrive felhőmappába.

---

## ⚙️ Konfigurációs Paraméterek (`config.schema.json`)

| Mező | Típus | Alapérték | Leírás |
|------|-------|-----------|--------|
| `target_platform_mode` | string | `"hybrid_universal_ai_browser_rpa"` | Támogatott portálok és rendszerek módja |
| `security_auth_vault_mode` | string | `"zero_trust_vault_push_avdh"` | Biztonsági Vault és AVDH aláírási mód |
| `resilience_and_audit_mode` | string | `"self_healing_dom_video_dms_sync"` | Reziliencia és dokumentumtár szinkron mód |
| `auto_avdh_signing_enabled` | boolean | `true` | Automatikus AVDH digitális aláírás |
| `notification_channel` | string | `"telegram"` | Riasztási csatorna (telegram, email, sms) |

---

## 📡 Webhook Végpont

* **URL:** `POST http://<szerver-ip>:8000/api/v1/modules/05_zart_hatosagi_portalok_es_regi_erp_k_ai_/test`
* **Naplófájl:** `data/hatosagi_portalok_rpa_naplo.json`
