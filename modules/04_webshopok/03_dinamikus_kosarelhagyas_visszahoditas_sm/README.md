# 🛒 Dinamikus Kosárelhagyás Visszahódítás (SMS és Email)

Nem sablon kuponokat küld, hanem a kosárban hagyott konkrét termék előnyeit és a leggyakoribb vásárlói aggályokat kezelő, személyre szabott üzeneteket generál szerkeszthető 2-lépcsős szekvenciával.

---

## 🌟 Működési Logika és Felépítés

### 1. Szerkeszthető 2-lépcsős Szekvencia (A opció szerkeszthetően)
* **1. Lépés (30 perc - szerkeszthető):** Rövid, figyelemfelkeltő SMS az elhagyott kulcstermék legfontosabb előnyével és 1-kattintásos direkt kosár-visszaállító linkkel.
* **2. Lépés (24 óra - szerkeszthető):** Részletes, prémium HTML email a vásárlói véleményekkel, 30 napos garanciával és tételes kosár-összesítővel.
* A késleltetési idők és a szövegsablonok tetszőlegesen átírhatók.

### 2. Saját Szerkesztésű Meggyőzési & Kedvezmény Szabályzat
* Beállítható, hogy a rendszer kupon nélkül (csak értékajánlattal), ingyenes szállítással vagy kosárértékhez kötött lépcsős VIP kedvezménnyel (pl. 50 000 Ft felett 5%) próbálja visszanyerni a vevőt.
* Kategória-specifikus aggálykezelés (pl. szerszámgép garancia, alkatrész-kompatibilitás).

### 3. 1-Kattintásos Kosár-Újraépítő Direkt Link (A opció)
* Egyedi helyreállító token (`restore_cart_url`), amely újratölti az elhagyott tételeket, az alkalmazott kupont és a vevő adatait, közvetlenül a fizetési gombhoz vezetve.

---

## 🚀 API Használat és Tesztelés

### Végpont
`POST http://localhost:8000/api/v1/modules/03_dinamikus_kosarelhagyas_visszahoditas_sm/test`
