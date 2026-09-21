# 🔎 Természetes Nyelvű Adatbázis Kereső (Text-to-SQL & Chat-with-Data)

Ez a modul lehetővé teszi, hogy a vállalat vezetői, projektmenedzserei és munkatársai **egyszerű magyar kérdésekkel forduljanak a cég bármely adatbázisához vagy táblázatához**, bonyolult SQL lekérdezések vagy fejlesztői segítség nélkül.

---

## 🚀 Főbb Képességek és Funkciók

1. **Univerzális Adatforrás Integráció:**
   - **SQL Adatbázisok:** PostgreSQL, MySQL / MariaDB, Microsoft SQL Server (MSSQL), SQLite.
   - **Fájlok & Táblázatok:** Excel (`.xlsx`), CSV fájlok.
   - **Felhős források:** Google Sheets, Airtable API.
   - **Egyedi Adatbázisok:** Bármilyen egyedi JDBC/ODBC vagy Python driverrel rendelkező ERP / belső rendszer csatlakoztatható.
2. **Választható Biztonsági Szint (Strict Read-Only Sandbox):**
   - **Szigorú Csak Olvasás:** Blokkolja a veszélyes utasításokat (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`). Kizárólag lekérdezések futhatnak le.
   - **PII Adatmaszkolás:** Az érzékeny személyes és banki adatok automatikusan elrejtésre kerülnek.
3. **Vezetői Döntéstámogató Válasz:**
   - Természetes nyelvű, szabatos magyar vezetői összefoglaló a pontos számokkal.
   - Átlátható és ellenőrzött SQL lekérdezés (audit naplóhoz).
   - Strukturált rekord táblázat (oszlopok és sorok).
   - Azonnal kirajzolható diagram/grafikon adathalmaz (Oszlopdiagram, Tortadiagram).

---

## 📡 Webhook és API Használat

- **Végpont:** `POST /api/v1/webhook/termeszetes_nyelvu_adatbazis_kereso_text`
- **Minta Bemenet:**
```json
{
  "question": "Melyik 3 termékünk termelte a legnagyobb árbevételt, és melyik vevő vásárolta a legtöbbet?",
  "requested_by": "Dr. Kovács Béla (Ügyvezető Igazgató)",
  "max_results": 5
}
```
