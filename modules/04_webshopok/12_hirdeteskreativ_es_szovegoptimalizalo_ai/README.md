# 📢 4.12: Hirdetéskreatív- és Szövegoptimalizáló AI & Ad Fatigue Figyelő

## 📋 Áttekintés és Üzleti Érték
A Meta Ads (Facebook/Instagram), Google Ads és TikTok Ads kampányok leggyakoribb profitgyilkosa a reklámkifáradás (Ad Fatigue): ha a közönség túl sokszor látja ugyanazt a kreatívot, a kattintási arány (CTR) lefeleződik, a vásárlásonkénti költség (CPA) pedig megduplázódik. Ez a modul:
1. **Valós időben pásztázza a hirdetési fiókokat** és kiszámítja a fáradási pontszámot (frekvencia, CTR zuhanás, ROAS és CPA romlás).
2. **Azonnal generál 4 merőben eltérő pszichológiai szögű hirdetésszöveget**:
   - *Fájdalompont & Frusztráció* (Pain Point / Agitation)
   - *Szakmai Státusz & Tekintély* (Status & Pro Authority)
   - *Racionális Megtakarítás & Költséghatékonyság* (Logic & ROI)
   - *Társadalmi Bizonyíték & Sürgősség* (Social Proof & Urgency)
3. **Dinamikus Hook- és Címsormátrixot állít össze** (5 nyitómondat + 3 törzsszöveg elem + 4 CTA variáció) Meta Dynamic Creative vagy Google RSA kampányokhoz.
4. **Védi a költségkeretet**: vészfékkel (Circuit Breaker) lekapcsolja a pénzégető fáradt hirdetést, és előkészíti a friss variációk indítását 1-kattintásos jóváhagyással.

---

## ⚙️ A Megvalósított Tervezési Döntések (Mind Három Kérdésre Választható / C)

### 1. Ad Fatigue Érzékelési Küszöbök
- **Multi-metrika szabályzat (`hybrid_comprehensive_rules`)**:
  * Frekvencia küszöb: $\ge 2.8$
  * CTR zuhanás: $\ge 25\%$ a 7 napos átlaghoz képest
  * ROAS minimum: $< 3.0$
  * Maximális CPA túllépés: $> 7500$ Ft

### 2. AI Szövegíró és Pszichológiai Szögek
- **4 komplett direct-response szövegverzió** címsorokkal, törzsszöveggel, CTA-val és célközönség meghatározással.
- **Dinamikus Hook-mátrix**: 5 figyelmet megragadó nyitómondat, 3 termékelőny és 4 cselekvésre ösztönző gomb.
- **Választható formátumok (`selectable_all_formats`)**.

### 3. Beavatkozási Hatáskör és Fiókvezérlés
- **Intelligens hibrid védelmi szint (`hybrid_smart_guard`)**:
  * 70 feletti kritikus fáradási pontszámnál azonnali automata vészleállítás (Circuit Breaker Emergency Pause).
  * Új hirdetéscsoport vázlat mentése és azonnali 1-kattintásos indítási jóváhagyási kapu.
  * Telegram és Email riasztás a kampánymenedzsernek.

---

## 🚀 Tesztelés és Futtatás

### Helyi Mock Teszt:
```bash
python modules/04_webshopok/12_hirdeteskreativ_es_szovegoptimalizalo_ai/mock_test.py
```

### Éles Hub API Végpont:
- **POST** `/api/v1/modules/12_hirdeteskreativ_es_szovegoptimalizalo_ai/test`
- Fejlécek: `Content-Type: application/json`
- Adatbázis napló: `data/hirdetes_optimalizalo_naplo.json`