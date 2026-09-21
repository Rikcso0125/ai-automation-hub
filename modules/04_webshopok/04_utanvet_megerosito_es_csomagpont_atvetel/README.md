# 📦 Utánvét-Megerősítő és Csomagpont Átvételi SMS Értesítő

Kockázatalapú utánvét (COD) előszűrés és csomagfeladási zárlat, valamint többcsatornás csomagautomata lejárati riasztás családtagoknak továbbítható átvételi meghatalmazással.

---

## 🌟 Főbb Képességek

### 1. Kockázatalapú Intelligens Szűrés (1. Kérdés - B)
* Pontozza az utánvétes rendeléseket (0-100 kockázati pont):
  - Új vásárló (+20 pont)
  - Nagy kosárérték (> 40 000 Ft: +25 pont)
  - Hiányos cím / nincs házszám (+30 pont)
  - Gyanús vagy eldobható email cím (+20 pont)
* Ha a pontszám meghaladja a küszöböt (45 pont), a rendszer feladás előtt 1-kattintásos megerősítő SMS/WhatsApp linket küld.

### 2. Csomagfeladási Zárlat és Ügyfélszolgálati Riasztás (2. Kérdés - A)
* Ha a vásárló 24 órán belül nem erősíti meg a rendelést, automatikusan érvénybe lép a `SHIPPING_HOLD` zárlat.
* A címkenyomtatás letiltva, és kiemelt telefonos teendő keletkezik az ügyfélszolgálatnak, megóvva a céget az oda-vissza szállítási díj bukásától.

### 3. Csomagautomata Értesítő Továbbítható Átvételi Kóddal (3. Kérdés - C)
* Foxpost, Packeta, GLS és MPL automatáknál 24 órával a rekesz lejárata előtt vészjelző SMS/WhatsApp üzenetet küld.
* Emailben generál egy 1-kattintással megosztható meghatalmazást (`Proxy Pickup link`), amellyel rokon vagy ismerős is könnyedén átveheti a csomagot a határidő lejárta előtt.

---

## 🚀 API Végpont
`POST http://localhost:8000/api/v1/modules/04_utanvet_megerosito_es_csomagpont_atvetel/test`
