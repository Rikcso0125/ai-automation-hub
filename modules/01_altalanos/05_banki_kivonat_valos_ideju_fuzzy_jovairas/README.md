# 🏦 Banki Kivonat & Valós Idejű Fuzzy Jóváírás-Párosítás

Ez a modul automatizálja a beérkező banki utalások és a nyitott vevői számlák párosítását. Nem gond, ha a vevő elírta a közleményt vagy lefelejtette a pontos számlaszámot: a beépített intelligens Fuzzy algoritmus az összeg, a partnernév és a közlemény-töredékek alapján megtalálja a megfelelő számlát, automatikusan *Fizetettre* állítja a számlázóban, és **azonnal leállítja a kintlévőség-kezelő robotot**.

---

## 🚀 Bekötési Útmutató (Lépésről Lépésre)

### 1. Lépés: Banki Adatforrás Kiválasztása
A modul bármely magyar és nemzetközi bankkal működik:
* **Billingo Bankszinkron:** A Billingo automatikusan beolvassa a banki tranzakciókat (OTP, Erste, CIB, K&H, MBH, stb.). A Hub a Billingo API-n keresztül azonnal átveszi a jóváírásokat.
* **Számlázz.hu Autokassza:** Közvetlen összeköttetés a Számla Agent segítségével.
* **Wise Business & Revolut Business API:** Globális devizaszámlák azonnali API szinkronja.
* **Banki CSV / CAMT.053 Fájlok:** Bármely bank internetbankjából letöltött napi vagy heti kivonat egyszerű feltöltése.

### 2. Lépés: Biztonsági Fuzzy Küszöb (Alapértelmezett: 85%)
A rendszer 0-tól 100-ig pontozza az egyezést (összeg, számlaszám, névazonosság). 
* **85% felett:** Automatikusan lekönyveli és lezárja a számlát.
* **85% alatt:** Biztonsági okból nem könyvel vakon, hanem riasztást küld a pénzügyesnek kézi ellenőrzésre.

### 3. Lépés: Részfizetés és Egyenlegközlő
Ha a partner csak a számla egy részét utalta át:
1. Rögzíti a beérkezett összeget.
2. Csökkenti a nyitott tartozást a számlázóban.
3. Automatikusan előkészít egy udvarias köszönőlevelet a fennmaradó pontos összeggel és a fizetési határidővel.

### 4. Lépés: Beépített Kintlévőség-Robot Védelem
Sikeres párosításkor a modul automatikus jelet küld a `kintlevoseg_40eur` modulnak, amely azonnal törli a partnerhez tartozó emlékeztető és felszólító SMS/email időzítéseket!

---

## 🧪 Tesztelés
A **Teszt** fülön egy tipikus elírt közleményű banki utalással (*„szla 2026 0842 koszonjuk szepen a munkat”*, feladó: *„Nagy Bela EV”*) azonnal tesztelheted a 94%-os fuzzy párosítást és a számlazárást!
