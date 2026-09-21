# Modul 01: „Hol a csomagom?” (WISMO) 0-24 Futár API Autopilot

## Áttekintés
A **01_hol_a_csomagom_wismo_0_24_futar_api_auto** modul a webáruházi ügyfélszolgálatok leggyakoribb és leginkább időrabló kérdéstípusát (*„Hol van a rendelésem?” – Where Is My Order*) automatizálja 100%-ban, emberi beavatkozás nélkül a nap 24 órájában.

---

## Fő Funkciók

### 1. Multi-Carrier Futár API Integráció
- Támogatott futárszolgálatok: **GLS, DPD, Foxpost, Packeta, MPL (Magyar Posta)**.
- Keresés támogatott: **Csomagszám (Tracking number)**, **Rendelésszám (Order ID)**, vagy **Vevői email cím / telefonszám** alapján.

### 2. Normalizált Státuszok & Részletes Érkezési Idősáv
- `OUT_FOR_DELIVERY`: Futárnál kiszállítás alatt (pl. *"Ma 11:30 és 13:30 között várható"*), futár hívható telefonszámával.
- `READY_FOR_PICKUP`: Csomagautomatában átvehető (Pontos automata helyszín, nyitókód, átvételi határidő).
- `DELIVERY_FAILED`: Sikertelen kézbesítés (pl. zárt kapu / nem elérhető címzett).
- `IN_TRANSIT` & `LABEL_CREATED`: Depóban / raktári feladás alatt.

### 3. Omnichannel Válaszgenerálás
- Természetes magyar nyelvű azonnali válasz:
  - **Webchat:** Barátságos csevegőablak formátum.
  - **Email:** Hivatalos, formázott válaszlevél számlahivatkozással.
  - **WhatsApp / SMS:** Tömör, azonnali mobil üzenet élő térképes futárkövető linkkel.

### 4. Proaktív Kézbesítési Riasztás & Kivételkezelés
- Sikertelen kézbesítés vagy 24 órán belül lejáró csomagautomata esetén:
  - Azonnali proaktív üzenet a vevőnek 1-kattintásos újrakézbesítési időpont / címváltó linkkel (`https://futar.profigepesz.hu/redelivery?...`).
  - 24 órás inaktivitás esetén automatikus jegynyitás az ügyfélszolgálati Dashboardon.

---

## Adatbázisok és Naplózás
- **Napló:** `data/webshop_wismo_naplo.json` (kérdések, feloldási arány, futár megoszlás).
- **Központi Hub DB:** `data/hub_data.db`
