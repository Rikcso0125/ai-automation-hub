# Modul 06: AI Lead Scoring – A Forró Viszonteladó-Jelöltek Kiszűrése

## Áttekintés
A **06_ai_lead_scoring_a_forro_viszontelado_jel** modul a beérkező B2B érdeklődőket és regisztrációkat értékeli autonóm módon egy multi-faktoros pontozási mátrix és testreszabható egyedi szabályrendszer alapján. Kiszűri a lakossági és alacsony potenciálú megkereséseket, miközben a valódi, magas kosárértékű nagykereskedelmi partnereket 15 perces értékesítői SLA-val közvetlenül a dedikált területi Key Account Managerhez rendeli.

---

## Fő Funkciók

### 1. Multi-faktoros Pontozási Mátrix (0 - 100 pont)
1. **Pénzügyi Stabilitás és Cégméret (max. 35 pont):**
   - Munkavállalói létszám (>=20 fő: 10 pont, 10-19: 7 pont, 5-9: 5 pont).
   - Éves nettó árbevétel (>500M Ft: 12 pont, 200-500M: 9 pont, 50-200M: 5 pont).
   - Pozitív saját tőke és jövedelmezőség (6 pont, negatív tőke esetén -5 pont büntetés).
   - NAV köztartozásmentes státusz és hitelkockázat (7 pont, végrehajtás esetén -15 pont kizáró).
2. **Iparági és ICP Illeszkedés (max. 35 pont):**
   - Tevékenységi kör: HVAC, Épületgépészet, Villanyszerelés, Fővállalkozás (20 pont).
   - Működési idő: >=5 év cégkor (8 pont), 2-4 év (5 pont).
   - Digitális transzparencia: Valós weboldal és referenciák (7 pont).
3. **Vásárlási Potenciál és Sürgősség (max. 30 pont):**
   - Várható havi forgalom: >3M Ft (15 pont), 1-3M Ft (10 pont), 300e-1M Ft (5 pont).
   - Sürgősség: Azonnali / 1 héten belüli projektigény (10 pont), 1 hónapon belül (6 pont).
   - Konkrét tételes árajánlatkérés (5 pont).
4. **Testreszabható Egyedi Szabályok (Bonus/Malus):**
   - Rugalmasan bővíthető szabálymotor (pl. ISO tanúsítvány +5 pont, visszatérő ügyfél +10 pont, végrehajtási kockázat -25 pont).

---

## 3-Szintű Partnerminősítés (Tiers)

| Tier | Pontszám | Kategória | Értékesítési SLA & Akció |
| :--- | :--- | :--- | :--- |
| **Tier A** | 80 - 100 pont | **Forró Kiemelt Partner** | 15 perces Senior KAM visszahívás, Arany/Platina kedvezménykeret (-22% / -28%), dedikált tárgyalási script |
| **Tier B** | 50 - 79 pont | **Normál B2B Partner** | Automatikus B2B önkiszolgáló regisztrációs link, standard nagyker árlista, webinar hozzáférés |
| **Tier C** | < 50 pont | **Lakossági / Alacsony Potenciál** | 0 perc értékesítői idő, automatikus udvarias elirányítás a lakossági webshophoz |

---

## Választható Továbbítási Módok

- **Mód A (Speciális Területi KAM Routing):** A lead azonnal a területi Key Account Managerhez kerül (Közép-Mo., Nyugat-Mo., Kelet-Mo.), generált 1-kattintásos telefon/WhatsApp linkkel és instant riasztással.
- **Mód B (Központi CRM Lead Pool):** A leadek pontszám szerint rendezett központi felvehető sorba kerülnek a B2B értékesítési csapat számára.

---

## Adatbázis Kapcsolatok
- **Napló:** `data/b2b_lead_scoring_naplo.json` (audit trail, pontszám bontás, SLA határidők).
- **Meglévő Partner Törzs:** `data/b2b_partnerek.json`
- **Központi Hub DB:** `data/hub_data.db`
