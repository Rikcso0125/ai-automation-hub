# ⚡ Enterprise AI Automation Hub

> **62 beépített, moduláris AI munkafolyamat és automatizációs motor vállalkozások számára, modern reszponzív webes vezérlőpulttal.**

Az **AI Automation Hub** egy központi vezérlőmotor, amely lehetővé teszi vállalkozások, KKV-k és nagyvállalatok számára, hogy intelligens mesterséges intelligencia funkciókat kössenek be meglévő rendszereikbe (CRM, ERP, Webáruház, számlázók, Google Workspace, Make.com, n8n, Zapier).

---

## 🚀 Főbb Jellemzők

- 🧩 **62 Üzleti Modul 5 Kategóriában:** Minden modul önálló mappával, JSON sémával, részletes leírással, beépített tesztadatokkal és Python végrehajtó motorral rendelkezik.
- 📱 **100% Mobilbarát Web Dashboard:** Érintőképernyőre és okostelefonokra optimalizált reszponzív kezelőfelület (asztali géptől a legkisebb mobilokig).
- 🔗 **Azonnali Webhook Végpontok:** Minden modulhoz külön `POST /api/v1/webhook/{id}` végpont tartozik, amely Make.com, n8n és Zapier kompatibilis.
- ⚙️ **Dinamikus és Típusbiztos Konfiguráció:** Sémavezérelt beállítási felület jelszómezőkkel, csúszkákkal, listákkal és azonnali mentéssel (SQLite adatbázis perzisztencia).
- 🧪 **Élő Tesztelő Környezet:** Beépített JSON tesztelő azonnali válasz- és futásiidő-visszajelzéssel (`duration_ms`).
- 📜 **Valós Idejű Rendszernapló:** Minden hívás bemenete, kimenete és hibája naplózásra kerül.

---

## 📂 Modul Kategóriák Áttekintése

1. **1. Általános & Pénzügy (15 modul):**
   - Intelligens email triage & CRM ticket szortírozó
   - Számla OCR és NAV XML adategyeztető
   - 40 EUR behajtási díjátalány & kintlévőség-kezelő
   - Valós idejű banki kivonat fuzzy párosító
   - 2-3 hetes prediktív cash flow likviditás-előrejelző
   - Kétnyelvű hasábos szerződésfordító & kockázatelemző
   - Autonóm értekezlet jegyzetelő & teendő-szétosztó
   - Természetes nyelvű SQL adatbázis-lekérdező (Text-to-SQL)
   - Automatikus heti/havi vezetői riportgeneráló
   - Zero-touch munkatárs és ügyfél onboarding
   - Céges költségelszámolás blokk-feldolgozó
   - Vezetői hangparancs asszisztens
   - Önjavító munkafolyamat felügyelet (Self-Healing Watchdog)

2. **2. Szolgáltató Cégek (17 modul):**
   - AI ügyfélszolgálati diszpécser & hang- és szöveg triage
   - 0-24 intelligens időpontfoglaló és naptárkezelő
   - Google Cégem véleményfigyelő és automatikus válaszadó
   - Árajánlat-készítő és felmérési munkalap generátor
   - Dinamikus munkalap és digitális aláírás feldolgozó
   - Alvállalkozói és műszaki partner megfelelőségi audit
   - Facebook & Instagram lead azonnali visszahívás-riasztó
   - B2B hideg lead kutató és LinkedIn profil szinkron
   - B2B Lead Scoring & Intent Scoring algoritmus
   - B2B Megbízási szerződés és titoktartási (NDA) generátor
   - Elvesztett ajánlatok visszanyerő (Win-Back) automatizmus
   - Ügyféllemorzsolódás-megelőző (Churn Predictor)
   - Sales coaching és tárgyaláselemző asszisztens
   - Garanciális és hibajegy automatikus panaszkezelő
   - Munkatársi belső tudásbázis (RAG) chatbot
   - Automatikus B2B LinkedIn tartalomgeneráló
   - Kétlépcsős ajánlatküldő és automatikus utánkövető (Follow-up)

3. **3. Kereskedő Cégek (10 modul):**
   - Beszállítói árlisták összefésülése & árváltozás-detektor
   - 3-Way Matching: Beszerzési számla, szállítólevél és megrendelés egyeztető
   - B2B Portál: Tömeges rendelés-feldolgozó (Excel/PDF rendelésből azonnali kosár)
   - Dinamikus készlet-újrarendelési algoritmus & kifutási előrejelzés
   - B2B Kintlévőség- és hitelkeret-figyelő
   - Automatikus szállítmány-nyomkövető és késés-előrejelző
   - Sales tárgyalási intelligencia & egyedi kedvezmény-kalkulátor
   - Intelligens cserealkatrész- és helyettesítőtermék kereső
   - Kereskedelmi árrésvédelmi riasztó & anomália-detektáló
   - B2B Vevői holtpont-aktiváló & automatikus újrarendelés-serkentő

4. **4. Webáruházak & E-kereskedelem (13 modul):**
   - WISMO (Where Is My Order) 0-24 futárkövető
   - Többcsatornás készlet- és árszinkronizáció (Webshop + Marketplaces)
   - AI Kosárelhagyás-mentő & elakadáskezelő
   - Utánvét-megerősítő és csomagpont-átvétel maximalizáló
   - Hivatalos WhatsApp Business API tranzakciós asszisztens
   - Tömeges SEO és konverzióoptimalizált termékleírás-író
   - AI Termékfotó-stúdió & háttércsere
   - Szemantikus webes virtuális eladó (Termékajánló RAG)
   - Hirdetéskreatív és konverziós szövegoptimalizáló AI
   - Social Selling komment- és privát üzenet kezelő
   - Dinamikus és kosárérték-növelő (Upsell / Cross-sell) motor
   - Automatikus rövidvideó (Reels/TikTok) vágó szkript generátor
   - Webáruházi anomália-detektálás & kuponcsalás-szűrő

5. **5. Műszaki, Kivitelező & Gyártó Cégek (7 modul):**
   - Építési napló és napi jelentés hangjegyzetből (Speech-to-Report)
   - Raktári hangvezérelt polckezelő & komissiózó
   - Gépi látás alapú alkatrész- és állapotfelismerő (Edge Vision)
   - Anyagszükséglet és norma-idő kalkulátor műszaki rajzból
   - Minőségbiztosítási jegyzőkönyv és vizuális selejtfelmérő
   - Terepi számla- és szállítólevél szkennelő terepjáró csapatoknak
   - Hatósági portálok és közmű-egyeztetések automatizálása (RPA)

---

## 🛠️ Telepítés és Indítás

### 1. Követelmények
- **Python 3.10+**
- **Git**

### 2. Klónozás
```bash
git clone https://github.com/Rikcso0125/ai-automation-hub.git
cd ai-automation-hub
```

### 3. Függőségek telepítése
```bash
pip install -r requirements.txt
```

### 4. Szerver indítása
Windows alatt egyszerűen kattints kétszer a `run_hub.bat` fájlra, vagy futtasd parancssorból:
```bash
python hub_server.py
```

### 5. Használat
- **Webes Admin Vezérlőpult:** `http://localhost:8000`
- **Swagger API Dokumentáció:** `http://localhost:8000/docs`
- **Webhook végpontok:** `http://localhost:8000/api/v1/webhook/{module_id}`

---

## 🔒 Biztonság & Architektúra

- **Adatbiztonság:** Minden konfiguráció helyben, az SQLite adatbázisban tárolódik.
- **Mock / Offline Mód:** Minden modul azonnal tesztelhető harmadik féltől származó API kulcsok megadása nélkül is (intelligens szimuláció).
- **RESTful API:** Egységes JSON specifikáció, OpenAPI 3.0 támogatással.

---

## 📄 Licenc
MIT Licenc - Szabadon felhasználható és testreszabható vállalati célokra.