# 📞 0-24 Virtuális AI Telefonos Recepciós (Voice AI)

Ez a modul éjjel-nappal emberi minőségű magyar beszédhangon fogadja a bejövő telefonhívásokat, tehermentesítve a szakembereket és az irodai személyzetet.

---

## ⚡ Főbb Funkciók

1. **Választható Voice AI Telefonos Platformok:**
   - Vapi.ai, Retell AI, Bland.ai, Twilio és Telnyx SIP Trunk közvetlen bekötése.
   - Beépített Hub szimulátor a webes kipróbáláshoz.
2. **Élő Időpontfoglalás & Tudásbázis:**
   - Megválaszolja az árakat, nyitvatartást, szolgáltatásokat.
   - Közvetlenül lefoglalja a szabad időpontot a naptárban.
3. **Hívás Utáni Kétlépcsős Megerősítés:**
   - Elsődlegesen **WhatsApp Business** üzenetet küld az ügyfélnek a részletekkel.
   - Ha nem elérhető, automatikusan **Telnyx SMS-re** vált.
4. **Strukturált Leirat Mentése Külön Fájlba:**
   - Minden hívás teljes dialógusa, szándéka és összefoglalója automatikusan elmentődik az `output/transcripts/` könyvtárba JSON formátumban.
