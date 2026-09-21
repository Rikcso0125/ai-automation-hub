# 🛡️ 4.13: Webáruházi Anomália Detektálás (Kuponkód & Fizetési Kapu Figyelő)

## 📋 Áttekintés és Üzleti Érték
A modern e-kereskedelemben a technikai leállások és az adminisztrációs elgépelések jelentik a legnagyobb azonnali veszteségforrást:
1. **Fizetési kapu leállás (Failover védelem)**: Ha a bankkártyás fizetési kapu (SimplePay / Barion / Stripe) elakad és egymás után több tranzakció meghiúsul, a vevők kosárelhagyás nélkül elvesznek. A modul ezt azonnal érzékeli, riaszt, és a pénztárban automatikusan előtérbe helyezi az utánvétes vagy azonnali banki átutalásos fizetést.
2. **Kuponkód & Árrésvédelmi Circuit Breaker**: Ha egy elgépelt kupon (pl. véletlen 50-100% kedvezmény) miatt a termék eladási ára a beszerzési önköltség alá esne, az AI azonnal megállítja a rendelést, inaktiválja a kuponkódot és vészféket húz.
3. **Konverziós zárlat figyelés**: Riaszt, ha forgalom mellett hosszú ideje nem érkezik vásárlás (500-as szerverhiba vagy elakadt checkout folyamat).

---

## ⚙️ A Megvalósított Tervezési Döntések (Mind Három Kérdésre Választható / C)

### 1. Fizetési Kapu Hibaérzékelés & Failover
- **Hibalánc küszöb**: $\ge 3$ egymást követő sikertelen fizetésnél azonnali failover.
- **Statisztikai ráta figyelés**: Órás sikeresség 90% alá zuhanásánál sárga riasztás.
- **Automatikus Failover útvonal**: Utánvét és Azonnali Banki Átutalás (AFR) előtérbe helyezése.

### 2. Kuponkód Kockázat & Árrésvédelem
- **Negatív-árrés Circuit Breaker**: Önköltség alatti eladás észlelésekor azonnali zárlat.
- **Plafon-ellenőrzés**: 40% feletti engedmény automatikus gyanúsnak minősítése.
- **Tömeges visszaélés szűrés**: Kuponoldalas illegális terjedés detektálása.

### 3. Beavatkozási Szintek és Riasztás
- **Hibrid intelligens beavatkozás (`hybrid_loss_threshold_action`)**:
  * 20 000 Ft veszteségküszöb felett azonnali automatikus zárlat.
  * Alatta méltányossági felülvizsgálatra küldés a webshop vezetőjének.
- **Többcsatornás vészjelzés**: Telegram és SMS riasztás 1-kattintásos jóváhagyó/törlő gombbal.

---

## 🚀 Tesztelés és Futtatás

### Helyi Mock Teszt:
```bash
python modules/04_webshopok/13_webaruhazi_anomalia_detektalas_kuponkod_/mock_test.py
```

### Éles Hub API Végpont:
- **POST** `/api/v1/modules/13_webaruhazi_anomalia_detektalas_kuponkod_/test`
- Fejlécek: `Content-Type: application/json`
- Adatbázis napló: `data/webaruhazi_anomalia_naplo.json`