# ⚖️ Automatikus Kintlévőség-kezelés & 40 EUR Behajtási Lánc

Ez a modul megszünteti a késedelmes vevői kifizetéseket és a felesleges telefonos könyörgést. A Billingo / Számlázz.hu rendszerből beolvasott számlákra lépcsőzetes, professzionális emlékeztető és felszólító láncolatot indít el Resend/SMTP emailen és Telnyx SMS-en keresztül, azonnali bankkártyás fizetési linkkel. 15 nap késés után automatikusan érvényesíti a magyar jogszabályok szerinti **40 EUR behajtási költségátalányt** és a törvényes késedelmi kamatot.

---

## 🚀 Bekötési Útmutató (Lépésről Lépésre)

### 1. Lépés: Email Küldő Szolgáltató Beállítása
* **Resend API (Ajánlott):** Regisztrálj a [resend.com](https://resend.com/) oldalon, hitelesítsd a céges domainedet (DNS bejegyzések), hozz létre egy API kulcsot (`re_...`), és másold be a konfigurációba.
* **Céges SMTP:** Ha a saját leveleződet használod (pl. Google Workspace vagy cPanel mail), add meg az SMTP szerver címét, felhasználónevét és jelszavát.
* **Mock Mód:** Teszteld a működést azonnal külső kulcsok nélkül!

### 2. Lépés: Telnyx SMS Szolgáltató Bekötése
A Telnyx a világ egyik legmegbízhatóbb és legolcsóbb SMS API szolgáltatója:
1. Regisztrálj a [telnyx.com](https://telnyx.com/) felületen.
2. A *Messaging* menüpont alatt hozz létre egy új Messaging Profile-t.
3. Másold ki a Telnyx API kulcsodat (`KEY...`).
4. Állítsd be a feladó nevét (Alphanumeric Sender ID, pl. a céged nevét ékezetek nélkül), hogy a vevő azonnal felismerje az SMS-t.

### 3. Lépés: Online Fizetési Kapu Kiválasztása
A felszólítások akkor a leghatékonyabbak, ha a partner a telefonján az SMS-re koppintva 10 másodperc alatt ki tudja egyenlíteni a számlát:
* **Billingo / Számlázz.hu fizetés:** Automatikus egyedi fizetési link a számlához.
* **Stripe:** Ha saját webes fizetési rendszert használsz, add meg a Stripe Secret Key-t.
* **Banki átutalás:** Automatikusan beilleszti a bankszámlaszámot és a számlaszámot a közleménybe.

### 4. Lépés: A 40 EUR Törvényi Háttér
A **2016. évi IX. törvény** értelmében a vállalkozások közötti (B2B) ügyleteknél a késedelembe eső vevő a késedelem napjától kezdve köteles megfizetni a jogosultnak a legalább 40 eurónak megfelelő forintösszeget behajtási költségátalányként.
* A rendszer az általad megadott türelmi idő (alapértelmezetten 15 nap) után ezt automatikusan hozzáadja a tartozáshoz a késedelmi kamattal együtt, és jogi formátumú fizetési felszólítást küld.

---

## 🧪 Tesztelés
Kattints a **Teszt** fülre, ahol egy 16 napja lejárt, 420.000 Ft-os számla mintaadataival azonnal láthatod a 40 EUR költségátalány kiszámítását, a kamatot és a legenerált Telnyx SMS szövegét!
