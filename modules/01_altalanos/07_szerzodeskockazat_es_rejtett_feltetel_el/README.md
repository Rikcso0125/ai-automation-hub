# 📝 Szerződéskockázat és Rejtett Feltétel Elemző (Red-Flag Audit)

Ez a modul megvédi vállalkozásodat a partnerek, beszállítók vagy multinacionális megrendelők által küldött előnytelen, csapdákkal teli szerződésektől. 60 másodperc alatt átvilágítja a sokoldalas PDF és Word (.docx) szerződéseket, kiszűri a rejtett jogi aknákat 3 kockázati szinten, és **kész, kimásolható hivatalos magyar ellenjavaslat-levelet készít a partner jogászának**.

---

## 🚀 Bekötési Útmutató (Lépésről Lépésre)

### 1. Lépés: Szerződéses Szerep és Preferenciák
A Konfiguráció fülön add meg:
* **Céged szerepe:** Vállalkozó / Szállító vagy Megrendelő.
* **Maximális kötbér plafon (%):** Alapértelmezett: 10% (megelőzi a korlátlan vagy 30-50%-os büntetéseket).
* **Bírósági illetékesség:** Kizárja a drága külföldi bíróságokat.

### 2. Lépés: Feltöltési Csatornák
* **Közvetlen feltöltés a felületen:** PDF vagy Word (.docx) fájl behúzása a Teszt fülre.
* **Email csatolmány továbbítás:** A `szerzodesek@cegem.hu` címre érkező dokumentumok automatikus továbbítása a modul webhookjára.

### 3. Lépés: A 3 Kockázati Szint Értelmezése
* 🟢 **Alacsony kockázat / Aláírható:** A szerződés kiegyensúlyozott, a felelősségek kölcsönösek.
* 🟡 **Megfontolandó feltételek:** Kisebb aszimmetriák (pl. 90 napos felmondási ablak vagy túlzott garancia).
* 🔴 **Kritikus veszély / Tilos aláírni módosítás nélkül:** Korlátlan kötbér, egyoldalú kirúgási jog, felelősség elmaradt haszonért vagy külföldi bíróság.

### 4. Lépés: Kész Jogi Alkupozíció (1 Kattintásos Másolás)
A felület azonnal legenerál egy udvarias, diplomatikus hivatalos levelet a partnernek címezve, amely pontosan tartalmazza a kifogásolt pontok javasolt módosított szövegét (`proposed_redline`).

---

## 🧪 Tesztelés
A **Teszt** fülön egy tipikus trükkös nagyvállalati szerződésmintával azonnal kipróbálhatod: 4 kritikus jogi csapdát azonosít és kész ellenjavaslatot fogalmaz meg!
