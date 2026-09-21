# -*- coding: utf-8 -*-
import json
import httpx
from typing import Dict, Any

async def run_async(payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    sender_name = payload.get("sender_name", "Érdeklődő")
    sender_email = payload.get("sender_email", "")
    subject = payload.get("subject", "(Nincs tárgy)")
    body = payload.get("body", "")

    company_name = config.get("company_name", "Vállalkozásunk")
    knowledge_base = config.get("company_knowledge_base", "")
    reply_tone = config.get("reply_tone", "Professzionális és udvarias (Magázó)")
    api_key = config.get("api_key", "").strip()
    provider = config.get("ai_provider", "openai")
    model = config.get("ai_model", "gpt-4o-mini")

    # Ha nincs megadva valódi API kulcs, intelligens Mock módban futunk
    if not api_key or provider == "mock" or api_key.startswith("sk-placeholder"):
        return run_mock(payload, config)

    # Valódi OpenAI hívás
    if provider == "openai":
        return await call_openai(sender_name, sender_email, subject, body, company_name, knowledge_base, reply_tone, api_key, model)
    elif provider == "gemini":
        return await call_gemini(sender_name, sender_email, subject, body, company_name, knowledge_base, reply_tone, api_key, model)
    else:
        return run_mock(payload, config)

async def call_openai(sender_name, sender_email, subject, body, company_name, knowledge_base, reply_tone, api_key, model):
    system_prompt = f"""Te vagy a(z) {company_name} intelligens email asszisztense.
Feladatod:
1. Elemezd a beérkező emailt: kategorizáld (Árajánlatkérés, Ügyfélszolgálati kérdés, Számlázás, Reklamáció, SPAM).
2. Határozd meg a sürgősséget (1-től 5-ig) és az érzelmi tónust.
3. Készíts egy 90%-ban kész, azonnal küldhető magyar válaszpiszkozatot a megadott céges tudásbázis alapján.
4. Ha a levélre nem lehet biztos választ adni a tudásbázisból, fogalmazz udvarias pontosító kérdést.

Céges tudásbázis:
{knowledge_base}

Válasz stílusa: {reply_tone}

A válaszodat KIZÁRÓLAG egy érvényes JSON formátumban add meg a következő mezőkkel:
{{
  "category": "Árajánlatkérés | Ügyfélszolgálat | Reklamáció | Számlázás | SPAM",
  "urgency": 1-5,
  "sentiment": "Pozitív | Semleges | Frusztrált / Dühös",
  "summary": "1-2 mondatos magyar összefoglaló a levél lényegéről",
  "draft_reply": "A megfogalmazott kész magyar válaszlevél",
  "suggested_actions": ["teendő 1", "teendő 2"],
  "requires_escalation": true/false
}}"""

    user_content = f"Feladó: {sender_name} <{sender_email}>\nTárgy: {subject}\n\nSzöveg:\n{body}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.3
            }
        )
        if resp.status_code != 200:
            raise RuntimeError(f"OpenAI API hiba ({resp.status_code}): {resp.text}")

        data = resp.json()
        raw_result = data["choices"][0]["message"]["content"]
        parsed = json.loads(raw_result)
        parsed["provider_used"] = f"OpenAI ({model})"
        return parsed

async def call_gemini(sender_name, sender_email, subject, body, company_name, knowledge_base, reply_tone, api_key, model):
    prompt = f"""Te vagy a(z) {company_name} email asszisztense. Elemezd a levelet és készíts választ a tudásbázis alapján!
Tudásbázis: {knowledge_base}
Stílus: {reply_tone}
Levél feladója: {sender_name} ({sender_email})
Tárgy: {subject}
Szöveg: {body}

Válaszolj JSON-ben: category, urgency, sentiment, summary, draft_reply, suggested_actions, requires_escalation."""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
        if resp.status_code != 200:
            raise RuntimeError(f"Gemini API hiba ({resp.status_code}): {resp.text}")
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        # Tisztítás ha markdown kódblokkban jön
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        parsed = json.loads(text)
        parsed["provider_used"] = f"Google Gemini ({model})"
        return parsed

def run_mock(payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    sender_name = payload.get("sender_name", "Kedves Érdeklődő")
    subject = payload.get("subject", "")
    body = payload.get("body", "").lower()
    company_name = config.get("company_name", "Példa Kft.")

    if any(k in body for k in ["ár", "ajánlat", "mennyibe", "kiszállás"]):
        cat = "Árajánlatkérés"
        urgency = 4
        sentiment = "Érdeklődő / Pozitív"
        summary = f"{sender_name} előzetes felmérésről és kiszállási díjakról érdeklődik."
        draft = f"""Kedves {sender_name}!

Köszönjük szépen a megkeresését és az érdeklődését!

Vállalkozásunk örömmel vállalja a munkát. Budapest területén a kiszállási díjunk 15.000 Ft, a felmérés során pedig pontos műszaki egyeztetést és tételes árajánlatot adunk.

Kérjük, jelezze felénk, hogy a jövő hét melyik napja lenne Önnek a legalkalmasabb egy személyes felmérésre!

Üdvözlettel,
{company_name} Ügyfélszolgálat"""
        actions = ["Naptárbejegyzés felmérésre", "Telefonos visszahívás 24 órán belül"]
    else:
        cat = "Általános érdeklődés"
        urgency = 2
        sentiment = "Semleges"
        summary = "Általános információkérés a cég szolgáltatásairól."
        draft = f"""Kedves {sender_name}!

Köszönjük megkeresését! Üzenetét rögzítettük, munkatársunk hamarosan felveszi Önnel a kapcsolatot a megadott elérhetőségeken.

Üdvözlettel,
{company_name}"""
        actions = ["Értékesítő kijelölése"]

    return {
        "category": cat,
        "urgency": urgency,
        "sentiment": sentiment,
        "summary": summary,
        "draft_reply": draft,
        "suggested_actions": actions,
        "requires_escalation": False,
        "provider_used": "Szimulált AI Motor (Mock Mode - adj meg API kulcsot a valós LLM futtatáshoz)"
    }

def run(payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    import asyncio
    return asyncio.run(run_async(payload, config))
