# 🔄 Többcsatornás Készlet- és Árszinkron (Webshop + eMAG + Alza + POS)

Bármelyik csatornán történik eladás, 3 másodpercen belül levonja a készletet az összes többi piactéren, kizárva a készlethiány miatti rendeléstörléseket és bírságokat.

---

## 🌟 Főbb Képességek és Funkciók

### 1. Készletpuffer és Túladás-Védelem (Buffer Stock Strategy)
* **Fix Puffer (`fixed_buffer`):** Ha a készlet eléri a minimális szintet (pl. <= 2 db), a piactereken (eMAG, Alza) automatikusan 0-ra állítja a készletet, kizárva a párhuzamos túladást, miközben a saját webshopban még eladható.
* **Dinamikus Kvóta (`dynamic_quota`):** Arányos elosztás a csatornák között (pl. 60% Webshop, 20% eMAG, 20% Alza).
* **Valós Idejű Zárolás (`realtime_lock`):** 15 perces kosár- és pénztárzárolás (Sub-second Lock & Reservation).

### 2. Csatornánkénti Árképzés & Jutalékvédelem (Price Sync)
* **Egységes Ár (`uniform`):** Minden felületen azonos fogyasztói ár.
* **Jutalékkal Növelt Árrésvédelem (`margin_protected`):** Automatikusan ráterheli az eMAG (~16%) és Alza (~14%) jutalékot, megvédve a tiszta nyereséget.
* **Csatorna Szabályzat (`channel_rules`):** Egyedi százalékos felárak, akciós plafonok és garantált minimális árrés védelem (Floor Margin).

### 3. Fizikai Üzlet / POS Pénztárgép Integráció
* **Valós Idejű Push (`realtime_push`):** POS blokk zárásakor <3 másodperces készletfrissítés minden online csatornán.
* **Időszakos Kötegelt (`batch_periodic`):** 5 perces ciklikus frissítés és nap végi egyeztető audit.
* **Hibrid Szinkron (`hybrid`):** Kritikus/alacsony készletnél azonnali push levonás, plusz 5 perces háttérellenőrzés és automatikus leltáreltérés riasztás.

---

## 🚀 API Használat és Tesztelés

### Végpont
`POST http://localhost:8000/api/v1/modules/02_tobbcsatornas_keszlet_es_arszinkron_webs/test`
