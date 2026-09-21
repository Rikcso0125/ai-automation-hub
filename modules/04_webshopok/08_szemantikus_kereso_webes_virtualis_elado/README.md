# 🔎 Szemantikus Kereső & Webes Virtuális Eladó Bot

Megérti a laikus vásárlók kötetlen igényeit (pl. *„Kényelmes túracipő sziklás terepre”*, *„fúró panel betonfalhoz”*), és a pontos készletből közvetlenül a kosárba helyezhető ajánlatokat ad.

---

## 🌟 Főbb Képességek

### 1. Keresési és NLP Motor (1. Kérdés)
* **Szándékkivonatolás:** Kinyeri a felhasználási célt (betonfúrás), meghajtást (akkus), ársávot és méretet.
* **Hibrid Szemantikus Keresés:** Szövegértés és vektoros hasonlóság + pontos cikkszám egyezés + elgépelés-toleráns szinonimakeresés.

### 2. Tanácsadói Dialógus és UI Megjelenés (2. Kérdés)
* **Közvetlen Kártyák:** 1-kattintásos kosárba helyezés szakértői ajánlással.
* **Guided Selling:** Tág kérdésnél pontosító kérdéssor.
* **Döntéstámogató Mátrix:** Belépő vs Bestseller vs Prémium opciók összehasonlítása.

### 3. Készlethiány és Kiegészítő Ajánlás (3. Kérdés)
* **Raktári Alternatíva:** Elfogyott termék esetén azonnali raktáron lévő cseregép felajánlása indoklással.
* **Smart Bundle:** Kompatibilis fúrószárak, pótakkuk és védőfelszerelések ajánlása 1-kattintásos csomagkedvezménnyel.

---

## 🚀 API Végpont
`POST http://localhost:8000/api/v1/modules/08_szemantikus_kereso_webes_virtualis_elado/test`
