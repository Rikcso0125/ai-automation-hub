# 🛡️ Önjavító Munkafolyamat-Felügyelet (Self-Healing Watchdog)

Ez a modul az AI Automation Hub autonóm védőpajzsa: folyamatosan figyeli az összes futó automatizmust, észleli a külső szolgáltatók (pl. NAV, bankok, számlázók, OpenAI) kieséseit, és emberi beavatkozás nélkül elhárítja a hibákat.

---

## ⚡ A 3-Lépcsős Önjavító Mechanizmus

1. **Exponenciális Újrapróbálkozás (Retry 3x):**
   - Átmeneti hálózati mikrokieséskor növekvő időközönként automatikusan újrapróbálja a műveletet.
2. **Automatikus Átkapcsolás Tartalék Útvonalra (Failover):**
   - Ha egy szerver nem válaszol, automatikusan átkapcsol a másodlagos végpontra vagy aszinkron feldolgozó sorra.
3. **Dead-Letter Queue (DLQ Lemezes Mentés):**
   - Ha semmi nem működik, a tranzakciót biztonságosan elmenti a helyi lemezre, garantálva a **0 adatvesztést**.
4. **1-Kattintásos Javító Gomb:**
   - A vezető és az admin egyetlen gombnyomással újraindíthatja a folyamatot a telefonjáról.
