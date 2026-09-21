# 📱 4.10: Social Selling: Kommentből Messenger / Instagram Vásárlási Tölcsér

## 📋 Áttekintés és Üzleti Érték
A Facebook és Instagram hirdetések és posztok alatti érdeklődő kommentek (pl. *"Ár?", "Kupon?", "Hol kapható?", "Kérem a linket"*) jelentik a legmagasabb konverziós potenciálú forgalmat. Ha az ügyfélszolgálat nem reagál azonnal, a vásárlási szándék elillan. Ez a modul:
1. **5 másodpercen belül** feldolgozza a beérkező kommenteket (ManyChat és Meta Graph API webhook).
2. **Értelmezi a szándékot** természetes nyelvű AI szándékfelismeréssel és kulcsszavas prioritással.
3. **Nyilvános kommentválaszt ad** a poszt alatt dinamikusan rotált emberi sablonokkal és komment-lájkolással, elkerülve a Meta spam szűrőjét és növelve a poszt organikus elérését (algoritmus boost).
4. **Privát üzenetet nyit (Instagram DM vagy Facebook Messenger)** interaktív ManyChat-kompatibilis termékkártyával, 2 óráig érvényes 10%-os villámkuponnal és 1-kattintásos azonnali kosárba helyező linkkel.
5. **Konverziókövetést és 90 perces kosárelhagyás emlékeztetőt ütemez.**

---

## ⚙️ A Megvalósított Tervezési Döntések (Mind Három Kérdésre Választható / C)

### 1. Komment-trigger és Szándékfelismerés
- **Szigorú kulcsszavak**: KUPON, ÁR, LINK, KÉREM, MEGRENDELÉS, ÉRDEKEL.
- **AI szemantikus NLP**: Kötetlen szleng, kérdések és hangulatjelek intelligens megértése.
- **Hibrid szabályrendszer (`hybrid_smart_matching`)**: Kulcsszavak azonnali prioritással + AI szándékpontozás és spamszűrés.

### 2. Nyilvános Komment Reakció & Algoritmus Védelem
- **10+ rotált emberi sablon**: Nincs robot-jelleg, a Meta algoritmusa organikus beszélgetésként értékeli.
- **Automatikus lájk**: Azonnali elismerés a vásárlónak.
- **Engagement kérdés**: Aktivitásnövelő visszakérdezés a kommentszám további pörgetésére.

### 3. Privát Üzenet Tölcsér & Vásárlási Konverzió
- **Villámkupon motor**: 10% kedvezmény 2 órás lejárati idővel (urgency és azonnali döntés).
- **1-kattintásos Checkout URL**: Automatikusan betölti a terméket és a kupont a kosárba.
- **Interaktív gombok (ManyChat/Meta formátum)**:
  * `[🛒 Kosárba rakom (-10%)]`
  * `[⚡ Készlet & Garancia info]`
  * `[💬 Kérdésem van szakértőhöz]`

---

## 🚀 Tesztelés és Futtatás

### Helyi Mock Teszt:
```bash
python modules/04_webshopok/10_social_selling_kommentbol_messenger_inst/mock_test.py
```

### Éles Hub API Végpont:
- **POST** `/api/v1/modules/10_social_selling_kommentbol_messenger_inst/test`
- Fejlécek: `Content-Type: application/json`
- Adatbázis napló: `data/social_selling_naplo.json`