# 📑 Tömeges B2B Árajánlatadás Partner Kedvezményszintekkel

**Modul azonosító:** `03_tomeges_b2b_arajanlatadas_partner_kedvez`  
**Kategória:** Kereskedő Cégek Automatizációi (3. Kategória / 03. Modul)

---

## 🎯 Cél és Működési Áttekintés

A nagykereskedelmi és disztribúciós értékesítők munkaidejük akár 30-40%-át azzal töltik, hogy ömlesztett viszonteladói emaileket és táblázatokat bogarásznak:
- Meg kell keresniük az egyes termékek cikkszámát.
- Ellenőrizniük kell az adott vevő egyedi szerződéses kedvezményszintjét (Bronz, Ezüst, Arany, Platina).
- Át kell nézniük a raktárkészletet, és készlethiány esetén helyettesítő terméket kell vadászniuk.
- Formázott ajánlatot kell szerkeszteniük, miközben a vevő azonnal várja az árat.

Ez a modul autonóm B2B ajánlatadó copilotként működik:
1. **Természetes szöveg és email feldolgozás:** Nyers email szövegből (pl. *„Kérek árat 150 m rézcsőre és 5 db szivattyúra”*) vagy táblázatból automatikusan kinyeri a tételeket és mennyiségeket.
2. **Partner és kedvezményszint felismerés:** Partnerkód, adószám vagy cégnév alapján azonnal hozzárendeli a szerződéses engedményt (Bronz -10%, Ezüst -15%, Arany -22%, Platina -28%).
3. **Élő készletvizsgálat & Automatikus alternatíva-ajánlás:** Ha a kért mennyiség nem érhető el a raktárban, azonnal felajánlja a raktáron lévő egyenértékű helyettesítő terméket (pl. Grundfos helyett Wilo).
4. **Mennyiségi sávos bónuszkedvezmény:** 500e Ft és 1M Ft felett automatikus extra volumentámogatást számol.
5. **Hivatalos B2B válaszlevél & PDF ajánlat 60 másodperc alatt:** 15 napos ajánlati kötöttséggel és szerződéses fizetési feltételekkel.
6. **1-Kattintásos értékesítői jóváhagyás:** Az értékesítő azonnal átfuthatja és egyetlen kattintással jóváhagyhatja a kiküldést.
7. **Perzisztens ajánlat-naplózás:** `data/b2b_ajanlatok_naplo.json`.

---

## ⚙️ Főbb Konfigurációs Beállítások

| Mező | Típus | Alapérték | Leírás |
|------|-------|-----------|--------|
| `company_name` | `string` | `"ProfiGépész Nagykereskedelmi Kft."` | Nagykereskedés neve |
| `quote_validity_days` | `integer` | `15` | Ajánlati kötöttség időtartama napokban |
| `discount_tiers` | `object` | `{"BRONZE": 10.0, "SILVER": 15.0, ...}` | Szerződéses szintek (%) |
| `volume_discount_thresholds` | `object` | `{"500000": 2.0, "1000000": 4.0}` | Mennyiségi sávos bónuszok |
| `approval_mode` | `string` | `"manual_approval_only"` | Manuális vagy automata kiküldés |
| `partners_db_path` | `string` | `"data/b2b_partnerek.json"` | Partner adatbázis útvonala |
| `catalog_db_path` | `string` | `"data/termektorzs_katalogus.json"` | Terméktörzs és készletadatok |
| `quotes_db_path` | `string` | `"data/b2b_ajanlatok_naplo.json"` | Kiadott ajánlatok naplója |

---

## 📡 API és Webhook Végpontok

- **Ajánlatkérés feldolgozása:** `POST /api/v1/modules/03_tomeges_b2b_arajanlatadas_partner_kedvez/test`
- **Külső Webhook fogadás:** `POST /api/v1/webhook/03_tomeges_b2b_arajanlatadas_partner_kedvez`
- **1-Kattintásos jóváhagyás:** `POST /api/v1/modules/03_tomeges_b2b_arajanlatadas_partner_kedvez/test` (`{"action": "APPROVE_QUOTE", "quote_id": "..."}`)
