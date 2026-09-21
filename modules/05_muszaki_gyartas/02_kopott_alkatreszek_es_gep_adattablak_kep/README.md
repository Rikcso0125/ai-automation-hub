# 🔧 Kopott Alkatrészek és Gép-Adattáblák Képazonosítása (Vision Part ID - Module 5.02)

Egy koszos, olajos, félig lekopott ipari alkatrész vagy gép-adattábla mobilfotója alapján a modul mesterséges intelligenciával (Vision AI + Multi-Model Fuzzy Rekonstrukció) azonosítja a gyári cikkszámot, megkeresi a gépkönyvi robbantott ábrát (exploded view), felállítja a helyettesítő utángyártott kompatibilitási mátrixot, és automatizálja a beszerzést.

---

## 🎯 Üzleti Érték és Funkciók

1. **🔬 Képfelismerés & Kopott Adattábla Rekonstrukció (Opció C):**
   * Speciális képjavító pipeline (olajfolt-szűrés, CLAHE hisztogram kontraszt-kiemelés, neurális felbontásnövelés).
   * Részleges és sérült szövegtöredékek (pl. `FES?O CPE14-M1HA-5J?-1/8 MN: 1969??`) intelligens kiegészítése gyártói katalógusok alapján, megbízhatósági pontszámmal (Confidence Score: 97.2%).

2. **📐 Gépkönyvi Robbantott Ábra (Exploded View) & Kompatibilitási Mátrix (Opció C):**
   * Azonosítja a gépkönyvi fejezetet, oldalszámot és tételszámot (pl. Krones Canmatic Ch. 04 -> Pos. 14 / Tábla 4B) vizuális koordinátákkal.
   * Teljes Cross-Reference alkatrészmátrix: Eredeti gyári OEM (Festo) vs. 100% egyenértékű prémium alternatívák (SMC, Bosch Rexroth) árelőnnyel és azonnali raktári elérhetőséggel.

3. **⚡ Terepi Karbantartói Munkafolyamat & Beszerzési Autopilot (Opció C):**
   * Keresztreferenciás belső és külső készletellenőrzés (helyi üzem vs. központi raktár vs. 6 km-re lévő B2B partner depó).
   * Állásidő-kockázat és termeléskiesés kalkuláció (pl. 350.000 Ft/óra állásidő-kár kivédése).
   * Automata Műszaki Vezetői Jóváhagyási Kapu Telegram / SMS riasztással és 1-kattintásos gyorsrendeléssel.

---

## ⚙️ Konfigurációs Paraméterek (`config.schema.json`)

| Mező | Típus | Alapérték | Leírás |
|------|-------|-----------|--------|
| `ocr_reconstruction_mode` | string | `"hybrid_fuzzy_catalog_candidate"` | Képfeldolgozási és rekonstrukciós mód |
| `catalog_matching_depth` | string | `"full_cross_reference_aftermarket"` | Katalógus és robbantott ábra mélység |
| `field_workflow_mode` | string | `"end_to_end_procurement_autopilot"` | Terepi és beszerzési munkafolyamat mód |
| `min_confidence_threshold` | number | `0.85` | Minimális megbízhatósági küszöb |
| `require_chief_approval_over_huf` | integer | `40000` | Műszaki vezetői jóváhagyási értékhatár (Ft) |
| `notification_channel` | string | `"telegram"` | Riasztási csatorna (telegram, email, sms, slack) |

---

## 📡 Webhook Végpont

* **URL:** `POST http://<szerver-ip>:8000/api/v1/modules/02_kopott_alkatreszek_es_gep_adattablak_kep/test`
* **Naplófájl:** `data/alkatresz_azonositas_naplo.json`
