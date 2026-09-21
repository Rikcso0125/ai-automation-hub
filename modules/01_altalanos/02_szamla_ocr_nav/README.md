# 🧾 Beszállítói Számla Vision OCR & NAV Ellenőrző Modul

Ez a modul megszünteti a beszállítói számlák manuális pötyögését és a téves utalásokat. Bármilyen formátumban (PDF, mobilfotó, szkennelt dokumentum) érkező számlát másodpercek alatt beolvas tételszinten, ellenőrzi a számla matematikai pontosságát és a NAV adószám valódiságát, majd előkészíti a költségszámla automatikus rögzítését a Billingóban vagy a Számlázz.hu-ban.

---

## 🚀 Bekötési Útmutató (Lépésről Lépésre)

### 1. Lépés: Számla Beérkezési Csatorna Beállítása
A számlákat többféleképpen juttathatod el a modulhoz:
* **Email Továbbítással (Ajánlott):** Hozz létre egy belső email címet (pl. `szamlak@ceged.hu`). A leveleződben (Gmail / Outlook) állíts be egy egyszerű szabályt: minden csatolt PDF-et tartalmazó levelet továbbítson a Hub webhook címére:
  `http://<szerver-ip>:8000/api/v1/webhook/szamla_ocr_nav`
* **Make.com / n8n / Zapier:** A *Gmail - Watch Emails with Attachments* modul kimenetét küldd át a fenti webhook címre.
* **Mobilfotó feltöltés:** A munkatársak fotózhatják a papírszámlákat Telegramon / Slacken vagy a webes felületen keresztül.

### 2. Lépés: Vision AI Motor Beállítása
* **Google Gemini 1.5 Flash (Ajánlott számlákhoz):** Kifejezetten olcsó, villámgyors és kiválóan kezeli a többoldalas magyar PDF dokumentumokat. Kulcs igénylése: [Google AI Studio](https://aistudio.google.com/).
* **OpenAI GPT-4o Vision:** Csúcsminőségű karakterfelismerés még gyűrött, kézzel aláírt vagy rossz fényviszonyok között fotózott papírszámláknál is.
* **Mock Mód:** Kulcs nélkül is azonnal tesztelhető a teljes matematikai és NAV validációs folyamat!

### 3. Lépés: NAV Online Számla Ellenőrzés
A rendszer automatikusan ellenőrzi:
1. A beszállító adószámának alaki helyességét és CDV ellenőrző összegét.
2. Hogy a számla vevő adatai egyeznek-e a Te céged megadott adószámával (megelőzve, hogy tévedésből más cég számláját fizesd ki).
3. Hogy a nettó tételek és áfa összege centire megegyezik-e a feltüntetett bruttó végösszeggel.

### 4. Lépés: Számlázó és Könyvelő Integráció
Válaszd ki a célrendszert a Konfiguráció fülön:
* **Billingo:** A *Beállítások -> API kulcsok* menüpontban hozz létre egy új kulcsot. A jóváhagyott számlák automatikusan bekerülnek a *Kiadások* menüpontba.
* **Számlázz.hu:** Számla Agent kulccsal összekapcsolható a bejövő számlák archiválására.
* **Webhook Only:** Ha saját ERP-t vagy SAP/Dolibarr rendszert használsz, a modul kész JSON formátumban adja át az adatokat.

### 5. Lépés: Emberi Jóváhagyási Limit (Biztonsági Fék)
Állíts be egy maximális összeget (pl. `250.000 Ft`). Ezen összeg alatt a szabályos számlák automatikusan könyvelődnek; efelett vagy bármilyen számlahiba esetén a rendszer megállítja a folyamatot és jóváhagyást kér a megadott pénzügyi email címen.

---

## 🧪 Tesztelés
Nyisd meg a **Teszt** fület, és kattints a **„Teszt Futtatása Most”** gombra!
