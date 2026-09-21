# Helyszíni Felmérésből Árajánlat Hangfelvétel Alapján (Voice-to-Quote 3 Perc Alatt)

## 📌 Áttekintés
A terepen dolgozó szakember (klímás, villanyszerelő, gépész, kivitelező) a helyszínről távozva 1 perces kötetlen hangüzenetet és fotókat küld a felmérésről a telefonjára. A modul:
1. Beszédfelismeréssel szöveggé alakítja a hanganyagot és elemzi a feltöltött helyszíni fotókat.
2. A szöveg alapján azonosítja a beépítendő berendezéseket, anyagokat és szakkivitelezési folyamatokat.
3. Összepárosítja a tételeket a központi céges árlistával (`data/arlista_normak.json`).
4. Hozzáadja a beállított anyagveszteségi és biztonsági ráhagyást (+10%).
5. 3 percen belül egy márkázott, hivatalos **PDF árajánlatot** állít elő.
6. Választható módon:
   - **A Mód (review_required):** Elküldi a szakember/vezető mobiljára WhatsApp/Telegram üzenetben 1-kattintásos jóváhagyó linkkel.
   - **B Mód (auto_dispatch):** Közvetlenül kiküldi az ügyfélnek WhatsAppon / Telnyx SMS-ben online megrendelési és digitális elfogadási linkkel.

## ⚙️ Fájlstruktúra
- `manifest.json`: Modul metaadatok és leírás.
- `config.schema.json`: Bemeneti csatornák, jóváhagyási módok (A/B), árlista forrás és ráhagyási százalék.
- `handler.py`: Bemenet feldolgozás, árazás kalkuláció, reportlab PDF generálás és értesítés.
- `mock_test.py`: Standalone teszt A és B módra egyaránt.
- `test_payload.json`: Valósághű próbaadatok.
