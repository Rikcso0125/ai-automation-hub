# 🎬 4.11: Automata Rövidvideó Vágás & Feliratozás (Opus Clip Reels/TikTok)

## 📋 Áttekintés és Üzleti Érték
A hosszú (10-30 perces) YouTube termékbemutatókból, unboxingokból és tesztvideókból készített TikTok, Instagram Reels és YouTube Shorts videók jelentik a leghatékonyabb ingyenes organikus vevőszerzési csatornát. Ez az autonóm AI modul:
1. **AI Virality Scoring motorral** átfésüli a felvételt, és azonosítja a 3-5 legfigyelemfelkeltőbb 30-60 másodperces szakaszt (3 másodperces erős felütéssel - hook).
2. **Automatikusan 9:16 vertikális formátumra vágja** a videót intelligens arc- és termékkövető mozgással (Auto-Reframe).
3. **Dinamikus animált magyar feliratokat éget rá** (szóról-szóra karaoke stílusú kiemelések és automatikus emojik).
4. **Záró animált Call-to-Action kártyát illeszt be** (termékkép, webshop URL és 10%-os kuponkód).
5. **Platform-specifikus címsorokat és hashtageket generál** a TikTok, Reels és Shorts közzétételhez.

---

## ⚙️ A Megvalósított Tervezési Döntések (Mind Három Kérdésre Választható / C)

### 1. AI Viralitási Pontozás & Vágási Stratégia
- **Virality Score alapú rangsorolás**: Whisper AI leirat, hangerő-dinamika és beszédtempó alapján (90-99 pont közötti klipek).
- **Tematikus termékteszt fókusz**: 3 dedikált forgatókönyv:
  1. *Problémafelvetés & Megoldás*: Miért ég le a hagyományos gép a panelban?
  2. *Brutális Demonstráció*: C30 betonfúrás 4 másodperc alatt.
  3. *Ajánlat & Csomag*: L-BOXX koffer, 3 év garancia és kupon.
- **Hibrid klipgenerálás (`hybrid_smart_clips`)**: Tematikus sokszínűség a legmagasabb virality pontszámokkal.

### 2. Dinamikus Feliratozás & Képi Megjelenés
- **Viral Karaoke (Hormozi / MrBeast stílus)**: Sárga `#FFE600` és neonzöld `#00FF66` szóról-szóra animált kiemelés, fekete körvonal és releváns emojik (💥, 🔥, 😱, ⚡).
- **Prémium Minimalista**: Letisztult fehér felirat diszkrét sötét háttérsávval és céglogó vízjellel.
- **Választható kettős stílus (`selectable_dual_style`)**: Mindkét stílus azonnal elérhető A/B teszteléshez.

### 3. Záró Call-to-Action & Közzétételi Ügymenet
- **Konverziós Zárókártya**: 3 másodperces animált banner kuponkóddal (`REELS10`) és webshop linkkel.
- **Választható ügymenet**:
  * Teljesen automata közzététel (Direct Auto Publish).
  * ZIP exportálás és szerkesztői jóváhagyási kapu (HITL Review).
  * Hibrid 1-kattintásos közzététel a webes felületről.

---

## 🚀 Tesztelés és Futtatás

### Helyi Mock Teszt:
```bash
python modules/04_webshopok/11_automata_rovidvideo_vagas_feliratozas_op/mock_test.py
```

### Éles Hub API Végpont:
- **POST** `/api/v1/modules/11_automata_rovidvideo_vagas_feliratozas_op/test`
- Fejlécek: `Content-Type: application/json`
- Adatbázis napló: `data/rovidvideo_vagas_naplo.json`