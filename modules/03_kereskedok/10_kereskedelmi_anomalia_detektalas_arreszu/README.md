# Modul 10: Kereskedelmi Anomália Detektálás (Árrészuhanás Figyelő & Circuit Breaker)

## Áttekintés
A **10_kereskedelmi_anomalia_detektalas_arreszu** modul a kereskedelmi árrésvédelmi rendszer autonóm végrehajtója. Valós időben vizsgál minden beérkező rendelést és kiküldendő árajánlatot, megelőzve a fat-finger elgépelésekből, kedvezményhalmozásból vagy beszállítói áremelésekből származó veszteségeket.

---

## Fő Funkciók

### 1. Multi-faktoros Anomália Detektálás
- **Negatív Árrés (Negative Margin):** Eladási ár < Beszerzési önköltség.
- **Minimális Árréshatár Megsértése (Sub-Minimum Margin Floor):** Árrés < 8.0%.
- **Kedvezményhalmozás (Discount Stacking):** Halmozott engedmények összege > 35%.
- **Elgépelt Mennyiség / Fat-Finger Spike:** A szokásos mennyiség többszöröse vagy 0 Ft-os eladási ár.

### 2. Intelligens Védelmi Pajzs (Adaptive Circuit Breaker)
- **Kemény Zárlat (Hard Block):** Ha a számított árrésveszteség meghaladja az 50 000 Ft-os küszöböt, a rendszer azonnal leállítja a számlázást és a raktári kiadást (`HARD_CIRCUIT_BREAKER_ACTIVE`).
- **Audit Figyelmeztetés (Warning Flag):** 50 000 Ft alatti elméleti eltérésnél figyelmeztető zászlót rögzít a számlán anélkül, hogy megakasztaná az operatív kiszolgálást.

### 3. Kettős Vezetői Feloldási Folyamat (Manager Override)
- **1-Kattintásos Mobil Feloldás:** Azonnali Telegram és Vezérlőpult értesítés a Pénzügyi Igazgatónak tokenes jóváhagyási/elutasítási hivatkozással.
- **PIN Kódos Dashboard Feloldás:** Belső vezetői jóváhagyás audit naplózással.

---

## Adatbázis Kapcsolatok
- **Napló:** `data/arresvedelem_naplo.json` (korábbi árrésvédelmi bejegyzésekkel egybefésülve).
- **Központi Terméktörzs:** `data/termektorzs_katalogus.json`
