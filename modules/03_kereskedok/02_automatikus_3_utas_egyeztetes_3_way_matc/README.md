# 🛡️ Automatikus 3-Utas Egyeztetés (3-Way Matching: Számla vs PO vs Szállítólevél & Csalásszűrés)

**Modul azonosító:** `02_automatikus_3_utas_egyeztetes_3_way_matc`  
**Kategória:** Kereskedő Cégek Automatizációi (3. Kategória / 02. Modul)

---

## 🎯 Cél és Működési Áttekintés

A kereskedelmi és disztribútor cégeknél az egyik leggyakoribb rejtett profitveszteség a beszállítói számlák pontatlansága:
- A számlán 100 darab szerepel, de a raktárba valójában csak 85 érkezett meg (mennyiségi hiány).
- A beszállító magasabb egységárat számláz ki, mint amiben a beszerző megállapodott a megrendelőben (PO-ban).
- Egyre gyakoribb az **emailes számlacsalás (CEO / Invoice Fraud)**, ahol csalók a partner nevében módosított bankszámlaszámú (IBAN) számlát küldenek.

Ez a modul automatizált 3-utas összevetést és csalásvédelmet végez:
1. **Három dokumentum keresztellenőrzése:**
   - 1. Beérkező számla (Invoice - PDF Vision OCR vagy NAV Online Számla XML)
   - 2. Jóváhagyott megrendelő (Purchase Order - PO)
   - 3. Raktári bevételezés / Szállítólevél (Goods Receipt / Delivery Note)
2. **IBAN Csalásszűrő Pajzs (Fraud Guard):**
   - Ha a számlán szereplő bankszámlaszám nem egyezik a hivatalos beszállítói törzsben regisztrált IBAN-nal, a rendszer **azonnal fagyasztja a kifizetést**, és vészjelzést küld a gazdasági igazgatónak.
3. **Tételes mennyiségi és áreltérés vizsgálat:**
   - Pontosan kimutatja a túlszámlázást és a raktári hiányt cikkszámonként.
4. **Automatikus Kifogásolási Levél & Jóváíró Számla Igény:**
   - Eltérés esetén azonnal legenerálja a hivatalos reklamációs jegyzőkönyvet a beszállító felé hivatkozási számokkal és a jogosulatlan összeggel.
5. **Auto-Approve 100%-os egyezésnél:**
   - Hiba nélküli számlákat automatikusan fizetésre engedélyez.
6. **Perzisztens Audit Napló:**
   - Minden egyeztetést elment a `data/3way_matching_naplo.json` adatbázisba.

---

## ⚙️ Főbb Konfigurációs Beállítások

| Mező | Típus | Alapérték | Leírás |
|------|-------|-----------|--------|
| `iban_fraud_guard_mode` | `string` | `"STRICT_FREEZE"` | Szigorú zárolás IBAN eltérésnél |
| `price_tolerance_percent` | `number` | `0.0` | Megengedett egységár eltérés (%) |
| `rounding_tolerance_huf` | `number` | `5.0` | Kerekítési matematikai tűréshatár (Ft) |
| `auto_approve_perfect_match` | `boolean` | `true` | Hibátlan egyezésnél automatikus jóváhagyás |
| `generate_dispute_letter` | `boolean` | `true` | Reklamációs levél készítése a beszállítónak |
| `alert_channels` | `array` | `["telegram", "email", "dashboard"]` | Riasztási csatornák |
| `audit_db_path` | `string` | `"data/3way_matching_naplo.json"` | Perzisztens napló |

---

## 📡 API és Webhook Végpontok

- **3-utas egyeztetés futtatása:** `POST /api/v1/modules/02_automatikus_3_utas_egyeztetes_3_way_matc/test`
- **Külső Webhook fogadás:** `POST /api/v1/webhook/02_automatikus_3_utas_egyeztetes_3_way_matc`
- **Kézi felülbírálat (Override):** `POST /api/v1/modules/02_automatikus_3_utas_egyeztetes_3_way_matc/test` (`{"action": "OVERRIDE_APPROVAL", "reconciliation_id": "..."}`)
