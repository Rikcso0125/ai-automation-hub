# 📊 Beszállítói Árlisták Összefésülése (Supplier Feed Harmonizer & Árrésvédelem)

**Modul azonosító:** `01_beszallitoi_arlistak_osszefesulese_suppl`  
**Kategória:** Kereskedő Cégek Automatizációi (3. Kategória / 01. Modul)

---

## 🎯 Cél és Működési Áttekintés

A nagykereskedelmi és importőr cégek életében az egyik legnagyobb pénzügyi kockázat a beszállítói áremelések lassú vagy hibás lekövetése:
- 5–15 különböző nagykereskedő küld heti vagy napi rendszerességgel új árlistákat, teljesen eltérő formátumokban (Excel, CSV, XML, JSON).
- Ha a beszerzési ár emelkedik, de a webshopban vagy az ERP-ben nem frissül azonnal az eladási ár, **a cég hetekig veszteséggel vagy minimális haszonkulccsal értékesíthet termékeket**.

Ez a modul autonóm árrésvédelmi és feed-harmonizációs pajzsként működik:
1. **Smart Field Mapping (Intelligens Mezőfeltérképezés):** Képes bármilyen struktúrájú táblázatból automatikusan beazonosítani a cikkszámot, terméknevet, árat, devizát és készletet merev kódolás nélkül.
2. **Multi-Currency (Többdevizás) Kezelés:** Automatikusan átszámítja az EUR és USD árakat forintra az MNB vagy a beállított vállalati biztonsági árfolyamon.
3. **Árrésvédelmi Vészjelző (Loss-Making Guard):** Azonnal kiszűri a veszélyesen ráfizetéses cikkeket (ahol az új beszerzési ár meghaladja a jelenlegi eladási árat), és piros vezetői vészjelzést küld.
4. **Automatikus Eladási Ár Újraszámítás:** A kívánt minimális haszonkulcs (pl. 25-30%) alapján azonnal kiszámolja a javasolt új fogyasztói/partnerárat.
5. **Legjobb Beszerzési Forrás Kereső (Best Buy):** Ha ugyanaz a tétel több beszállítónál is elérhető, automatikusan a legolcsóbb forrást ajánlja.
6. **Vezetői Jóváhagyási Kapu & ERP Szinkron:** Áttekinthető jelentést ad az árváltozásokról, és 1-kattintásos jóváhagyás után automatikusan frissíti a belső terméktörzset (`data/termektorzs_katalogus.json`).
7. **Perzisztens Audit Napló:** Minden importálási tételt és árrésváltozást rögzít a `data/arresvedelem_naplo.json` adatbázisban.

---

## ⚙️ Főbb Konfigurációs Beállítások

| Mező | Típus | Alapérték | Leírás |
|------|-------|-----------|--------|
| `default_target_margin_percent` | `number` | `25.0` | Alapértelmezett minimális elvárt haszonkulcs (%) |
| `critical_margin_threshold_percent` | `number` | `10.0` | Kritikus árrés-küszöb vészjelzéshez (%) |
| `currency_exchange_rates` | `object` | `{"EUR": 412.5, "USD": 382.0}` | Deviza középárfolyamok |
| `approval_mode` | `string` | `"manual_approval_only"` | Jóváhagyási mód: manuális vagy auto-sync |
| `auto_sync_max_increase_percent` | `number` | `5.0` | Automatikus frissítés maximális áremelési határa (%) |
| `enable_best_buy_comparison` | `boolean` | `true` | Legolcsóbb beszállító kiválasztása |
| `master_catalog_path` | `string` | `"data/termektorzs_katalogus.json"` | Belső terméktörzs útvonala |
| `audit_log_path` | `string` | `"data/arresvedelem_naplo.json"` | Árrésvédelmi napló útvonala |

---

## 📡 API és Webhook Végpontok

- **Feed vizsgálat és árrésvédelem:** `POST /api/v1/modules/01_beszallitoi_arlistak_osszefesulese_suppl/test`
- **Külső Feed Webhook:** `POST /api/v1/webhook/01_beszallitoi_arlistak_osszefesulese_suppl`
- **1-Kattintásos jóváhagyás & ERP frissítés:** `POST /api/v1/modules/01_beszallitoi_arlistak_osszefesulese_suppl/test` (`{"action": "APPROVE_BATCH", "batch_id": "..."}`)
