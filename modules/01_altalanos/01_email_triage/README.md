# ✉️ Intelligens Email Triage & Piszkozatíró Modul

Ez a modul automatikusan átveszi a beérkező ügyfélemeileket, másodpercek alatt kategóriába rendezi őket, kiszűri a spameket és a dühös panaszokat, majd a céges tudásbázis és árlista alapján azonnal előkészíti a 90%-ban kész magyar válaszlevelet.

---

## 🚀 Bekötési Útmutató (Lépésről Lépésre)

### 1. Lépés: AI API Kulcs Beszerzése
A modul támogatja a legmodernebb nyelvi modelleket:
* **OpenAI (Ajánlott):** Regisztrálj az [OpenAI Platformon](https://platform.openai.com/), hozz létre egy új API kulcsot a *API Keys* menüpontban, és másold be az admin felületre. (Modell javaslat: `gpt-4o-mini` a leggyorsabb és leggazdaságosabb).
* **Google Gemini:** Hozz létre egy ingyenes kulcsot a [Google AI Studio](https://aistudio.google.com/) felületén (`gemini-1.5-flash`).
* **Kulcs nélküli próba:** Ha nincs még kulcsod, válaszd a `mock` módot, amivel azonnal kipróbálhatod a munkafolyamatot!

### 2. Lépés: A Céges Tudásbázis Kitöltése
Az admin felületen a **Konfiguráció** fül alatt töltsd ki:
* **Cég neve:** Pl. *Kovács & Társa Villanyszerelés Kft.*
* **Céges Tudásbázis:** Írd le pontokba szedve:
  - Szolgáltatások köre és területe (pl. Budapest és Pest vármegye)
  - Árak, óradíjak, kiszállási díjak
  - Garanciális feltételek
  - Nyitvatartás és elérhetőségek

### 3. Lépés: A Bejövő Email Fiók Összekötése (3 Egyszerű Módszer)

#### A) Módszer: Make.com / n8n / Zapier webhook segítségével (2 perc, legnépszerűbb)
1. Hozz létre egy új forgatókönyvet (Scenario / Workflow).
2. **Trigger:** Válaszd a *Gmail - Watch Emails* vagy *Email - Watch IMAP* modult.
3. **Akció:** Adj hozzá egy *HTTP - Make a Request* modult:
   - **Method:** `POST`
   - **URL:** Másold be a Hub által adott webhook címet: `http://<hub-szerver-ip>:8000/api/v1/webhook/email_triage`
   - **Body Type:** JSON
   - **JSON mezők:**
     ```json
     {
       "sender_name": "{{1.from.name}}",
       "sender_email": "{{1.from.address}}",
       "subject": "{{1.subject}}",
       "body": "{{1.textPlain}}"
     }
     ```
4. **Válasz mentése:** Az AI azonnal visszaküldi a választ (`draft_reply`). Ezt a következő lépésben a *Gmail - Create a Draft* modulba kötheted be.

#### B) Módszer: Google Workspace / Gmail Apps Script (Közvetlen és ingyenes)
Másold be a Gmail script szerkesztőbe a mellékelt webhook küldő kódot, ami minden olvasatlan levél esetén meghívja a Hub végpontját.

#### C) Módszer: Saját Python IMAP Figyelő Daemon
A modul mappájában futtatható a háttérben egy apró szinkronizáló folyamat, ami percenként lekérdezi az IMAP postafiókot.

---

## 🧪 Tesztelés
Kattints az Admin felületen a **„Kapcsolat tesztelése”** gombra, vagy futtasd a terminálból a `python mock_test.py` parancsot!
