# 📸 4.09: Garanciális Reklamáció & Visszáru Fotóelemzés Automata Címkével

## 📋 Áttekintés és Üzleti Érték
A webáruházak egyik legmagasabb élőmunka-igényű folyamata a garanciális panaszok és visszáruk kezelése. Ez az autonóm AI modul:
1. **Vision AI fotóelemzéssel** másodpercek alatt megvizsgálja a vevő által beküldött képeket és hibaleírást, osztályozva a sérülés jellegét (gyári hiba vs. külső behatás/törés vs. szállítási kár).
2. **Ellenőrzi a jótállási jogosultságot** a hatályos magyar fogyasztóvédelmi jogszabályok (151/2003. Korm. rend. és 19/2014. NGM rendelet) szerint az eladási ár és a vásárlási dátum alapján.
3. **Keep-the-Item gazdaságossági szabályt alkalmaz**: alacsony értékű termékeknél (< 15 000 Ft) visszaküldés nélkül azonnal jóváírja az összeget, megtakarítva a felesleges 2 200 Ft-os retúr futárdíjat és raktári adminisztrációt.
4. **Azonnali visszáru futárcímkét és feladókódot generál**:
   - **Foxpost**: 8 jegyű csomagautomata feladási kód (nyomtatás nélküli önkiszolgáló feladás).
   - **GLS Return**: Letölthető és nyomtatható vonalkódos PDF címke.
   - **GLS Pick & Return**: Háztól-házig futár felvétel idősávval a vásárló lakcímére.
5. **Pénzügyi jóváírást vagy raktári cseregépet indít**:
   - **+10% Bónusz Kupon**: Vevőmegtartó levásárolható webshop utalvány.
   - **Jóváíró Számla (Storno)**: Billingo / Számlázz.hu API számlázás + bankkártyás Barion/SimplePay refund.
   - **Azonnali Cserecsomag**: 0 Ft-os prioritásos raktári expediálás.

---

## ⚙️ A Megvalósított Tervezési Döntések (Mind Három Kérdésre Választható / C)

### 1. Vision AI Sérülésosztályozás és Garanciajogosultság
- **Gyári rejtett hiba (`MANUFACTURING_DEFECT`)**: Belső elektronika/motorégés, tokmány gyári megszorulás -> 94% bizonyosság, 100% garanciális fedezet.
- **Szállítási sérülés (`SHIPPING_DAMAGE`)**: Futárkáresemény, azonnali vevői kártalanítás + automatikus futárcégi kárjegyzőkönyv.
- **Rendeltetésellenes használat (`USER_MISHANDLING`)**: Beázás, leejtés, 400V túlfeszültség -> Jótállás elutasítva, kedvezményes javítási ajánlat.
- **Sávos kötelező jótállás**:
  * 10 000 - 100 000 Ft: 1 év
  * 100 001 - 250 000 Ft: 2 év
  * 250 000 Ft felett: 3 év
- **Keep-the-Item opció**: 15 000 Ft alatt nem szükséges visszaküldeni.

### 2. Többcsatornás Retúr Logisztika
- **Foxpost automata feladókód**: Papírmentes, 7 napig érvényes.
- **GLS letölthető PDF vonalkód**: Csomagponton vagy automatában leadható.
- **GLS Pick & Return**: Futáros háztól-házig felvétel.

### 3. Pénzügyi Rendezés és Csereügymenet
- **Vevői preferencia támogatás**:
  * Levásárolható kupon +10% extra hűségbónusszal.
  * Jóváíró számla + azonnali banki visszautalás.
  * Azonnali 0 Ft raktári cseregép kiszállítás.
- **Intelligens hibrid jóváhagyási kapu**: >85% bizonyosság és <50 000 Ft esetén teljesen autonóm; határesetben 1-kattintásos emberi felülvizsgálat.

---

## 🚀 Tesztelés és Futtatás

### Helyi Mock Teszt:
```bash
python modules/04_webshopok/09_garancialis_reklamacio_visszaru_fotoelem/mock_test.py
```

### Éles Hub API Végpont:
- **POST** `/api/v1/modules/09_garancialis_reklamacio_visszaru_fotoelem/test`
- Fejlécek: `Content-Type: application/json`
- Adatbázis napló: `data/garancia_reklamacio_naplo.json`