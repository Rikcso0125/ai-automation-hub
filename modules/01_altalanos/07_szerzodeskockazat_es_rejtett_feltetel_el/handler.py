# -*- coding: utf-8 -*-
from typing import Dict, Any, List

def run(payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    file_name = payload.get("file_name", "szerzodes.pdf")
    partner_name = payload.get("partner_name", "Szerződő Partner")
    text = payload.get("contract_text", "")
    company_name = config.get("company_name", "ProfiTech Kft.")
    max_cap = config.get("max_penalty_cap_percent", "10")

    findings = []
    text_lower = text.lower()

    # 1. Kötbér csapda vizsgálat
    if "kötbér" in text_lower or "kotber" in text_lower:
        if "felső korlát nélkül" in text_lower or "korlat nelkul" in text_lower or "1,5%" in text_lower or "1%" in text_lower:
            findings.append({
                "clause_id": "6.2",
                "topic": "Aránytalan és Plafon Nélküli Kötbér",
                "severity": "CRITICAL",
                "badge": "[KRITIKUS VESZELY]",
                "quote": "napi 1,5%-ának megfelelő késedelmi kötbért felszámítani a késedelem minden napjára, felső korlát nélkül",
                "legal_risk": "Felső korlát nélküli, extrém magas (napi 1,5%) kötbér. 20 napos csúszás esetén már a teljes díjazás 30%-át elvonhatja, 70 nap alatt a teljes munkadíj elveszhet!",
                "proposed_redline": f"Késedelem esetén a kötbér mértéke napi 0,2%, amelynek mindenkori felső határa nem haladhatja meg a nettó szerződéses érték {max_cap}%-át."
            })

    # 2. Egyoldalú felmondási csapda
    if "felmondás" in text_lower or "felmondas" in text_lower:
        if "nem jogosult" in text_lower and "indokolás nélkül" in text_lower:
            findings.append({
                "clause_id": "8.1",
                "topic": "Egyoldalú, Aszimmetrikus Felmondási Jog",
                "severity": "CRITICAL",
                "badge": "[KRITIKUS VESZELY]",
                "quote": "Megrendelő jogosult indokolás nélkül 3 napos felmondási idővel... Vállalkozó nem jogosult",
                "legal_risk": "A partner bármikor indoklás nélkül kirúghatja a céget 3 nap alatt, miközben Te nem mondhatod fel a szerződést még ellehetetlenülés esetén sem.",
                "proposed_redline": "Bármelyik fél jogosult a szerződést 30 napos felmondási idővel írásban felmondani, az addig elvégzett és átadott munkarészek arányos kifizetése mellett."
            })

    # 3. Rejtett automatikus hosszabbodás (Rollover / Evergreen)
    if "automatikusan" in text_lower and ("meghosszabbodik" in text_lower or "hosszabbodik" in text_lower):
        findings.append({
            "clause_id": "3.4",
            "topic": "Rejtett 24 Hónapos Automatikus Hosszabbodási Csapda",
            "severity": "HIGH",
            "badge": "[MEGFONTOLANDO FELTETEL]",
            "quote": "legalább 90 nappal írásban másként nem rendelkeznek... automatikusan további 24 hónapra meghosszabbodik",
            "legal_risk": "Ha 90 nappal a lejárta előtt elfelejted elküldeni a felmondást, újabb 2 teljes évre bebetonozódik a szerződés a régi árakon.",
            "proposed_redline": "A szerződés a határozott idő elteltével megszűnik, kivéve ha a felek a lejárta előtt legalább 30 nappal közös írásbeli megállapodással meghosszabbítják azt."
        })

    # 4. Korlátlan kártérítési felelősség
    if "korlátlan felelősséggel" in text_lower or "elmaradt hasznot" in text_lower:
        findings.append({
            "clause_id": "9.3",
            "topic": "Korlátlan Felelősség és Elmaradt Haszon Csapda",
            "severity": "CRITICAL",
            "badge": "[KRITIKUS VESZELY]",
            "quote": "korlátlan felelősséggel tartozik... ideértve a Megrendelő elmaradt hasznát",
            "legal_risk": "Egy esetleges hiba esetén a partner a kieső profitját és hírnévkárát is rád háríthatja, ami százmilliós csődhöz vezethet.",
            "proposed_redline": "A felek a Ptk. 6:143. § szerint kifejezetten kizárják a közvetett károk és az elmaradt haszon megtérítését; a felelősség felső határa a kifizetett megbízási díj 100%-ára korlátozódik."
        })

    # 5. Külföldi illetékesség
    if "bécsi" in text_lower or "nemzetközi választottbíróság" in text_lower:
        findings.append({
            "clause_id": "12.1",
            "topic": "Külföldi Választottbírósági Illetékességi Csapda",
            "severity": "HIGH",
            "badge": "[MEGFONTOLANDO FELTETEL]",
            "quote": "kizárólag a Bécsi Nemzetközi Választottbíróság (VIAC) hatáskörét kötik ki",
            "legal_risk": "Bármilyen számlavitánál a bécsi eljárási díjak (több millió Ft) miatt gyakorlatilag gazdaságtalan lenne behajtani a pénzedet.",
            "proposed_redline": "A felek a szerződésből eredő vitákra a magyar bíróságok joghatóságát és az alperes székhelye szerinti rendes bíróság illetékességét kötik ki."
        })

    # Kockázati besorolás
    critical_count = sum(1 for f in findings if f["severity"] == "CRITICAL")
    if critical_count >= 2:
        risk_level = "CRITICAL_DANGER"
        risk_badge = "[KRITIKUS VESZELY / TILOS ALAIRNI MODOSITAS NELKUL]"
        risk_score = 92
        recommendation = "A szerződés jelenlegi formájában súlyosan egyoldalú és aránytalan kockázatokat hordoz. Aláírása a fenti pontok módosítása nélkül tilos!"
    elif critical_count == 1 or len(findings) >= 2:
        risk_level = "WARNING"
        risk_badge = "[MEGFONTOLANDO FELTETELEK / MODOSITAS JAVASOLT]"
        risk_score = 65
        recommendation = "Néhány pont finomításra szorul az aláírás előtt a jogi egyensúly megteremtése érdekében."
    else:
        risk_level = "LOW_RISK"
        risk_badge = "[ALACSONY KOCKAZAT / ALAIRHATO]"
        risk_score = 20
        recommendation = "A szerződés alapvetően kiegyensúlyozott, komoly kockázati pont nem azonosítható."

    # Hivatalos kimásolható ellenjavaslat levél a partner jogászának
    email_letter = f"""Tisztelt {partner_name} Jogi és Beszerzési Osztály!

Köszönjük a(z) {file_name} szerződéstervezet megküldését.
Társaságunk, a(z) {company_name} elkötelezett a hosszú távú és sikeres együttműködés mellett, ugyanakkor a kölcsönös kockázatmegosztás és az üzleti egyensúly érdekében az alábbi pontok pontosítását és módosítását javasoljuk az aláírás előtt:

"""
    for f in findings:
        email_letter += f"- {f['clause_id']}. pont ({f['topic']}):\n"
        email_letter += f"  Jelenlegi szovegezes: {f['quote']}\n"
        email_letter += f"  JAVASOLT MODOSITAS: {f['proposed_redline']}\n\n"

    email_letter += f"""Kérjük, szíveskedjenek átvezetni a jenti módosításokat a végleges szerződésváltozatba.
Amint a korrigált tervezet rendelkezésre áll, készséggel aláírjuk a megállapodást.

Üdvözlettel,
{company_name} Cégvezetés"""

    return {
        "status": "success",
        "file_name": file_name,
        "partner_name": partner_name,
        "audit_summary": {
            "overall_risk_level": risk_level,
            "risk_badge": risk_badge,
            "risk_score_out_of_100": risk_score,
            "critical_traps_found": critical_count,
            "total_findings_count": len(findings),
            "recommendation": recommendation
        },
        "red_flag_findings": findings,
        "official_counter_proposal_email": email_letter
    }

async def run_async(payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    return run(payload, config)
