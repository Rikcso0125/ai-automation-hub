# Modul 08: Raktári Kétkezes Hangvezérlés (Hands-Free Voice Picking)

## Áttekintés
A **08_raktari_ketkezes_hangvezerles_hands_free** modul egy ipari szintű, kétkezes hangvezérelt raktári szedési és leltározó rendszer. Bluetooth vezeték nélküli fülhallgatón keresztül magyar nyelvű beszédutasításokkal irányítja a raktárost, aki élőszóban igazolja vissza a polchelyet és a szedett darabszámot, feleslegessé téve a kézi PDA-kat és vonalkód-szkennereket.

---

## Fő Funkciók

### 1. Kétkezes Hangos Dialógus Motor (Natural Speech Dialogue)
- **Folyosó és polc navigáció:** *"Menj a B-04 folyosóra, 12-es polchoz!"*
- **Polc ellenőrzés (Check Digit vagy Cikkszám):** Raktáros: *"42"* -> Rendszer: *"Rendben!"*
- **Szedési utasítás:** Rendszer: *"Szedj ki 2 darab Grundfos szivattyút!"* -> Raktáros: *"Kettő kész"*.
- **Útvonal optimalizálás:** Polcrendszerek szerinti logikai sorrend (A -> B -> C) a felesleges lépések minimalizálására.

---

## Választható Konfigurációk (Felhasználói Igények Szerint)

1. **Visszaigazolási Metódus (`verification_method`):**
   - `check_digit`: 2-jegyű polcellenőrző kód bemondása (pl. "42").
   - `sku_last_digits`: Cikkszám utolsó 3 számjegyének bemondása (pl. "567").
   - `hybrid_dual_check`: Kettős ellenőrzés prémium/nagy értékű gépeknél.

2. **Készlethiány és Sérülés Kezelése (`shortage_strategy`):**
   - `redirect_to_backup_shelf`: Tartalék polchely azonnali felajánlása (*"Menj a tartalék D-02-05 polchoz!"*).
   - `log_partial_and_continue`: Részmennyiség rögzítése, azonnali beszerzési értesítés és túra folytatása.
   - `smart_adaptive`: Intelligens kombinált mód készlet-elérhetőség alapján.

3. **Szedési Üzemmód (`picking_mode`):**
   - `single_order`: Egyedi vevői megrendelés szedése kész csomagolási jegyzékkel.
   - `batch_wave`: Több rendelés összevont szedése és zóna szerinti gyűjtése.

---

## Kimenetek és Adatbázisok
- **Szállítólevél & Dobozcímke:** Automatikus digitális csomagolólevél és dobozazonosító a túra végén.
- **Raktári Napló:** `data/raktar_hangvezerles_naplo.json` (operátori produktivitás, szedési sebesség, hiányok).
- **Központi Terméktörzs:** `data/termektorzs_katalogus.json`
