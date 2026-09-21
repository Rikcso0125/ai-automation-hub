# Modul 07: B2B Kintlévőség-kezelés 40 EUR Költségátalánnyal

## Áttekintés
A **07_b2b_kintlevoseg_kezeles_40_eur_koltsegat** modul a nagykereskedelmi viszonteladók lejárt számláit kezeli egy szigorú, jogilag megalapozott B2B behajtási és hitelkontrolling folyamat keretében. Összekapcsolja a számlanyilvántartást, a raktári szállítási zárlatot (Credit Hold), a törvényi kamatszámítást és a jogi MOKK FMH előkészítést.

---

## Fő Funkciók

### 1. 4-Lépcsős B2B Felszólító Láncolat
- **1. Lépcső (0 - 7 nap késedelem - Baráti Emlékeztető):**
  - Udvarias értesítés, számlamásolat és közvetlen banki utalási adatok.
- **2. Lépcső (8 - 14 nap késedelem - Hivatalos Felszólítás):**
  - Hivatalos figyelmeztetés a közelgő raktári zárlatról és a 40 EUR költségátalányról. 3 banki napos határidő.
- **3. Lépcső (15 - 29 nap késedelem - Szigorú Zárlat & 40 EUR):**
  - Életbe lép a **2016. évi IX. törvény szerinti 40 EUR behajtási költségátalány** (MNB árfolyamon átszámítva) + a **Ptk. 6:155. § szerinti késedelmi kamat**.
  - **Raktári szállítási stop (Credit Hold):** Új megrendelések és árukiadás automatikus felfüggesztése.
- **4. Lépcső (30+ nap késedelem - FMH Jogi Eszkaláció):**
  - MOKK (Magyar Országos Közjegyzői Kamara) kompatibilis **Fizetési Meghagyás (FMH) dosszié** és jogászi átadó levél generálása.

---

## Választható Konfigurációk (Felhasználói Igények Szerint)

1. **Raktári / ERP Rendelés Zárolási Szabályzat (`credit_hold_policy`):**
   - `grace_period_days`: Beállítható türelmi napok (alapértelmezetten 15 nap).
   - `immediate_freeze`: Azonnali szállítási stop az 1. napos késéstől.
   - `manager_override_warning`: Figyelmeztetés, külön vezetői feloldási joggal.

2. **40 EUR Költségátalány & Kamat Stratégia (`fee_calculation_mode`):**
   - `configurable_per_partner`: VIP partnereknél (Gold/Platinum) egyedileg elengedhető kereskedelmi méltányosságból a tőke azonnali rendezésekor.
   - `auto_invoice_immediate`: Azonnali terhelő számla kiállítása.
   - `notice_first_then_invoice`: Jogi figyelmeztetés a korai szakaszban, számlázás 15 nap után.

3. **Eszkalációs Mód (`escalation_mode`):**
   - `both_combined`: Többcsatornás riasztás (Email + SMS + KAM instant értesítés 1-kattintásos hívással) és 30 nap felett automatikus MOKK FMH csomag.

---

## Adatbázisok és Audit Naplózás
- **Kintlévőség Napló:** `data/b2b_kintlevosegek_naplo.json`
- **Partner Törzs:** `data/b2b_partnerek.json`
- **Központi Hub DB:** `data/hub_data.db`
