# 🎙️ Autonóm Értekezlet Jegyzetelés & Teendő Szinkron (Meeting Ops)

Ez a modul megszünteti az értekezletek utáni manuális jegyzetelést és feladat-kiosztást. Google Meet, Zoom vagy Teams hívásokból és hangfelvételekből másodpercek alatt kinyeri a meghozott döntéseket, a feladatokat határidőkkel és felelősökkel látja el, és **emberi jóváhagyási fázis után** közvetlenül beküldi őket a feladatkezelőbe (ClickUp, Asana, Notion, Trello, Google Tasks).

---

## 🚀 Bekötési Útmutató (Lépésről Lépésre)

### 1. Lépés: STT Beszédfelismerő Motor Kiválasztása
* **Helyi Faster-Whisper (Ajánlott, ingyenes):** Teljesen privát, közvetlenül a saját számítógépeden fut, és egyetlen bájtnyi hanganyag sem hagyja el a gépedet.
* **OpenAI Whisper API:** Felhős beszédfelismerés, maximális magyar nyelvi pontossággal.
* **Saját Szerver (Custom Whisper Endpoint):** Ha saját GPU szerveren futtatsz Whisper konténert, add meg annak URL-jét.

### 2. Lépés: Cél Feladatkezelő Rendszer Bekötése
Válaszd ki a csapatod által használt felületet a Konfigurációban:
* **ClickUp / Asana / Notion / Trello:** Másold be a személyes API tokent a konfigurációba. A rendszer automatikusan a megfelelő projektbe és felelőshöz rendeli a taskokat.
* **Google Tasks / Calendar:** Határidős naptárbejegyzés és teendő létrehozása.

### 3. Lépés: Emberi Jóváhagyási Kapu (Szerkesztési Lehetőség)
A modul beépített biztonsági fékkel rendelkezik:
1. Az AI elkészíti a jegyzőkönyvet és kigyűjti a feladatokat.
2. A státusz `PENDING_HUMAN_APPROVAL` állapotba kerül: a vezető egyetlen kattintással átfuthatja, és ha kell, módosíthatja a felelőst vagy a határidőt.
3. Csak a vezető jóváhagyása után küldi ki a feladatokat a ClickUp/Asanába és a tájékoztató emailt a csapatnak!

---

## 🧪 Tesztelés
A **Teszt** fülön egy életszerű 3 fős magyar vezetői értekezlet (marketing büdzsé + kivitelezési beszállítói áremelés) leiratával azonnal kipróbálhatod a döntések és feladatok kinyerését, valamint a jóváhagyási kapu működését!
