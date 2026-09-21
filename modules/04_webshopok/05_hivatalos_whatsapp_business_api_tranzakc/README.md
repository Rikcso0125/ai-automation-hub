# 💬 Hivatalos WhatsApp Business API Tranzakciós Vevőszolgálat

Automatikus rendelésigazolások, futárkövetési értesítők és 0-24 chatügyfélszolgálat a vásárlók által leginkább használt üzenetküldő appban választható sablonokkal, AI hatáskörrel és Add-to-Order csomagbővítéssel.

---

## 🌟 Működési Logika

### 1. Választható Tranzakciós Sablonok és Kézbesítés (1. Kérdés)
* **HSM Utility:** Meta által előzetesen jóváhagyott hivatalos tranzakciós sablonok interaktív CTA gombokkal (*„Csomagkövetés”*, *„Számla letöltése”*).
* **Interaktív Gombok:** Dinamikus Quick Reply és lista menük a csevegés azonnali megnyitásához.
* **Hibrid Fallback:** Ha a számon nincs WhatsApp fiók, a rendszer automatikusan Telnyx SMS-ben küldi el az értesítést.

### 2. Választható 0-24 AI Vevőszolgálati Hatáskör (2. Kérdés)
* **Önálló AI (`autonomous_full`):** Automatikusan kezeli a kérdéseket (rendelésállapot, számlamásolat, műszaki infók).
* **Emberi Kézbeadás (`human_handoff_rules`):** Alacsony bizonyosság (<80%) vagy panasz esetén azonnal élő operátorhoz irányít és riasztást küld.
* **Jóváhagyási Kapu (`hitl_approval_gate`):** Rutin válaszok azonnal, de érzékeny kéréseknél (címváltoztatás, rendeléstörlés) 1-kattintásos jóváhagyási kártyát készít az ügyfélszolgálatnak.

### 3. Feladás Előtti Add-to-Order Csomagbővítés (3. Kérdés - C)
* A rendelés leadása után 15 perces időablakban felajánl egy kompatibilis kiegészítőt (pl. bitkészlet vagy pótakku) ingyenes szállítással, növelve a kosárértéket.

---

## 🚀 API Végpont
`POST http://localhost:8000/api/v1/modules/05_hivatalos_whatsapp_business_api_tranzakc/test`
