# 📱 Missed Call Text-Back (Azonnali Érdeklődő-Mentés 5 Másodpercen Belül)

Ez a modul megmenti azokat a megrendelőket, akik munkaidőben vagy tárgyalás közben hívják a céget, de a hívást nem tudja senki felvenni. A hívás megszakadása után 5 másodpercen belül intelligens, személyre szabott válaszüzenetet küld ki.

---

## ⚡ Főbb Funkciók

1. **WhatsApp Elsődleges & Telnyx SMS Fallback:**
   - Elsőként WhatsApp Business API-n próbálja elérni a hívót, és ha az nem elérhető, azonnal automatikusan átvált Telnyx SMS-re.
2. **Külső Ügyfél Adatbázis Beolvasás:**
   - Automatikusan felolvassa a külső adatbázis fájlt (JSON vagy CSV).
   - Ha a hívó telefonszáma szerepel benne, név szerint köszönti (pl. *"Kedves Kovács Béla Úr!"*).
   - Ha ismeretlen szám, új érdeklődőként kezeli és azonnal bejegyzi a CRM-be.
3. **Beállítható Üzenetsablonok & Linkek:**
   - Testreszabható időpontfoglalási naptárlink (Calendly / Cal.com / Saját).
   - 1 perces igényfelmérő űrlap link.
   - Ígért visszahívási időablak (pl. 25 perc).
