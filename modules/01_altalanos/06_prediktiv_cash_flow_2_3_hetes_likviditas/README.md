# 📊 Prediktív Cash-Flow & 2-3 Hetes Likviditási Vészjelző

Ez a modul megszünteti a hóközi váratlan pénzhiányt és a fizetésképtelenségi meglepetéseket. Nem az elméleti számlalevelekre támaszkodik, hanem a **partnerek valós, múltbeli fizetési fegyelmét és késéseit** figyelembe véve szimulálja a bankszámla egyenlegét a következő 21–30 napra.

---

## 🚀 Bekötési Útmutató (Lépésről Lépésre)

### 1. Lépés: Biztonsági Tartalék Limit Beállítása
Állítsd be a **Biztonsági Tartalék Limitet (Safety Buffer)** a Konfiguráció fülön (pl. `1.000.000 Ft`). 
* Amint a szimuláció azt jelzi, hogy az egyenleg bármelyik nap ezen érték alá esne, a rendszer **2-3 héttel korábban riasztást küld**.

### 2. Lépés: Fix Havi Költségek Rögzítése
Add meg a rendszeres, kikerülhetetlen fix kiadásaidat:
* **Havi bérköltség** és a fizetés napja (pl. 10-e).
* **Bérjárulékok a NAV felé** és a határidő (pl. 12-e).
* **Becsült ÁFA fizetés** és a határidő (pl. 20-a).

### 3. Lépés: Partnerek Fizetési Késésének Korrekciója
A rendszer automatikusan hozzáad egy becsült késési napot a vevői számlákhoz (alapértelmezetten 6 nap), így a pénz befolyását nem a naiv számlahatáridőre, hanem a valóságos beérkezési napra számolja!

### 4. Lépés: Heti Vezetői Jelentés és Vészjelzés
* **Minden hétfő reggel:** Vezetői összefoglaló email a következő 3 hét várható pénzügyi görbéjével.
* **Azonnali Vészjelzés:** Ha likviditási hullámvölgy várható, konkrét, 3 lépéses akciótervet ad a hiány elhárítására (melyik vevőt kell azonnal felszólítani, és melyik beszállítótól érdemes halasztást kérni).

---

## 🧪 Tesztelés
A **Teszt** fülön egy életszerű céges pénzügyi állapot adataival azonnal futtathatod a 21 napos szimulációt: látni fogod a mélypontot, az egyenleggörbét és a megfogalmazott AI akciótervet!
