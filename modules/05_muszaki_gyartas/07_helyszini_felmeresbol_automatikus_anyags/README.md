# 🏗️ Helyszíni Felmérésből Automatikus Anyagszükséglet- és Normaidő-Számítás (Module 5.07)

A helyszínen felmért fizikai méretekből (kézi, lézeres távmérő vagy CAD terv) a beépített mérnöki szabályok és az ÉN (Építőipari Normarendszer) normagyűjtemény szerint automatikusan kiszámítja a tételes anyagszükségletet, a vágási hulladék-ráhagyást (scrap rate), a nehezítő szorzókkal korrigált munkaórákat és a kivitelezési időtartamot. Automatikusan előállítja a TERC-kompatibilis tételes költségvetést, a tüzépes beszállítói árajánlatkérő kosarat és a közvetlenül elküldhető márkázott PDF árajánlatot.

---

## 🎯 Üzleti Érték és Funkciók

1. **📐 Technológiai Hulladék-Optimalizálás & Anyagszükséglet (Opció C):**
   * Geometriai felületekből automatikus nettó és bruttó anyagszámítás szakterületenként (Knauf gipszkarton lapok, CW/UW profilok, Isover szigetelés, Armstrong álmennyezet, Desso szőnyegmodulok).
   * Dinamikus technológiai vágási ráhagyás (scrap rate: 5-10%), megelőzve a hiány miatti leállásokat és a felesleges raktári felesleget.

2. **⏱️ Hivatalos ÉN Normarendszer & Dinamikus Helyszíni Szorzók (Opció C):**
   * Szakipari tételes normaidő-számítás (fő $	imes$ óra $/ m^2$).
   * Valós helyszíni nehezítő körülmények automatikus szorzói (pl. 3.5 m feletti magasság és állványozási pótlék: +18%, éjszakai/hétvégi zajkorlátozott munkavégzés: +15%).
   * Brigádlétszám (pl. 6 fő) és munkanap-ütemezési kalkuláció (13.1 munkanap).

3. **💰 TERC-Kompatibilis Költségvetés & Nagyker Beszerzési Kosár (Opció C):**
   * Anyag és munkadíj önköltség vs. célzott haszonkulcsos eladási ár (pl. 22.0% Margin).
   * Automatikus beszállítói árajánlatkérő kosár generálása a partner tüzépekre/nagykereskedésekre (`PO-REQ-PRJ-2026-VG-C4`).
   * 1-kattintásos márkázott PDF árajánlat generálása és letöltése az ügyfél részére.

---

## ⚙️ Konfigurációs Paraméterek (`config.schema.json`)

| Mező | Típus | Alapérték | Leírás |
|------|-------|-----------|--------|
| `survey_calculation_mode` | string | `"hybrid_multi_input_scrap_optimization"` | Felmérési és vágási hulladékszámítási mód |
| `labor_norm_engine` | string | `"en_norms_dynamic_site_multipliers"` | Normaidő és szorzókalkulációs mód |
| `quotation_output_mode` | string | `"full_terc_budget_quote_procurement"` | Költségvetési és értékesítési mód |
| `default_scrap_waste_pct` | number | `10.0` | Alapértelmezett hulladék-ráhagyás (%) |
| `target_profit_margin_pct` | number | `22.0` | Célzott haszonkulcs (%) |
| `master_hourly_labor_rate_huf` | integer | `8500` | Szakipari rezsióradíj (Ft/óra) |
| `notification_channel` | string | `"telegram"` | Riasztási csatorna (telegram, email, sms) |

---

## 📡 Webhook Végpont

* **URL:** `POST http://<szerver-ip>:8000/api/v1/modules/07_helyszini_felmeresbol_automatikus_anyags/test`
* **Naplófájl:** `data/anyagszukseglet_normaido_naplo.json`
