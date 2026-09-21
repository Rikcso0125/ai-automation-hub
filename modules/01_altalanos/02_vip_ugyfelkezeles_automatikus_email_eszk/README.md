# 👑 VIP Ügyfélkezelés & Automatikus Email Eszkaláció

Ez a modul garantálja, hogy a vállalkozás legfontosabb ügyfelei és a sürgős panaszok soha ne várjanak órákat az ügyfélszolgálati postafiókban.

---

## 🚀 Bekötési Útmutató (Lépésről Lépésre)

### 1. Lépés: Telegram Bot Létrehozása (2 perc, Ingyenes)
1. Nyisd meg a Telegramot, és keresd meg a **@BotFather** hivatalos fiókot.
2. Küldd el a `/newbot` parancsot, és adj neki egy nevet (pl. `CegemVipRiasztoBot`).
3. Másold ki a kapott **HTTP API tokent** a konfigurációba.
4. Keresd meg a **@userinfobot**-ot a Telegramon, és írj neki bármit: a válaszban kiírja a saját **ID számodat** (pl. `849204123`). Másold be a `telegram_chat_id` mezőbe!

### 2. Lépés: Telnyx SMS Beállítása
Add meg a vezető mobiltelefonszámát nemzetközi formátumban (pl. `+36301234567`), hogy a Telegram mellett azonnali SMS ébresztést is kapjon kritikus helyzetben.

### 3. Lépés: VIP Lista és Kulcsszavak Megadása
* **VIP Domainek:** Add meg a kulcsfontosságú partnereid céges domainjeit (pl. `mol.hu, audi.hu, otp.hu`). Bármelyik munkatársuktól érkezik levél, azonnal VIP prioritást kap!
* **Kulcsszavak:** Állítsd be a cégedre jellemző vészhelyzeti szavakat (pl. `leállás, kötbér, azonnal, ügyvéd, szerződésbontás`).

### 4. Lépés: Automata Válasz (Nyugtató Email)
Ha be van kapcsolva, a rendszer a levél beérkezése után 5 másodpercen belül küld egy diplomatikus, megnyugtató levelet a dühös vagy sürgős VIP ügyfélnek, jelezve, hogy a felsővezetés már kezeli az ügyet.

---

## 🧪 Tesztelés
A **Teszt** fülön egy kritikus sürgősségű, kötbérrel fenyegető MOL Nyrt. vezérigazgatósági email mintájával azonnal kipróbálhatod az eszkalációs riasztások összeállítását!
