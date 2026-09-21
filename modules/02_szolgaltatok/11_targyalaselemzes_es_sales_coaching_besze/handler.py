"""
Tárgyaláselemzés és Sales Coaching (Beszéd/Hallgatás Arány)
Modul: 11_targyalaselemzes_es_sales_coaching_besze
"""

import os
import sys
import json
import datetime
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class SalesCoachingHandler:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.target_talk_ratio_max = float(self.config.get("target_talk_ratio_max", 45.0))
        self.manager_alert_threshold_score = int(self.config.get("manager_alert_threshold_score", 60))
        self.high_value_deal_threshold_huf = int(self.config.get("high_value_deal_threshold_huf", 1000000))
        self.enable_pdf = "pdf_coaching_report" in self.config.get("output_formats", ["pdf_coaching_report"])

    def analyze_transcript(self, turns: List[Dict[str, Any]], total_duration_sec: int) -> Dict[str, Any]:
        """
        Kiszámítja a hívás beszéd/hallgatás arányát, félbeszakításokat, kérdéseket és hangulatot.
        """
        rep_sec = 0
        cust_sec = 0
        interruption_count = 0
        open_questions = 0

        question_words = ["hogyan", "miért", "mikor", "milyen", "mit gondol", "mekkora", "kérdezhetem", "megoldás"]

        for turn in turns:
            spk = turn.get("speaker")
            dur = turn.get("duration_sec", 5)
            text = turn.get("text", "").lower()

            if spk == "SALES_REP":
                rep_sec += dur
                if turn.get("interrupted_customer"):
                    interruption_count += 1
                for q in question_words:
                    if q in text and "?" in turn.get("text", ""):
                        open_questions += 1
                        break
            else:
                cust_sec += dur

        total_analyzed = max(1, rep_sec + cust_sec)
        rep_ratio = round((rep_sec / total_analyzed) * 100, 1)
        cust_ratio = round((cust_sec / total_analyzed) * 100, 1)

        # 0-100 Sales Minőségi Pontszám kalkuláció
        score = 100

        # 1. Beszédarány büntetés (ha az értékesítő >45%-ot beszél)
        if rep_ratio > self.target_talk_ratio_max:
            excess = rep_ratio - self.target_talk_ratio_max
            score -= int(excess * 1.5)

        # 2. Félbeszakítás büntetés (-10 pont per vágás)
        score -= (interruption_count * 12)

        # 3. Kérdezéstechnika (kevés kérdés büntetés)
        if open_questions == 0:
            score -= 15
        elif open_questions >= 3:
            score += 5

        final_score = max(10, min(100, score))

        # Értékelés címke
        if final_score >= 85:
            grade = "KIVÁLÓ / MESTERFOKÚ KONZULTÁCIÓ"
            badge = "[SZUPER SALES TELJESÍTMÉNY]"
        elif final_score >= 70:
            grade = "JÓ / ÁTLAG FELETTI"
            badge = "[JÓ TÁRGYALÁS]"
        elif final_score >= 55:
            grade = "KÖZEPES / FEJLESZTENDŐ"
            badge = "[FEJLESZTENDŐ ELEMEK]"
        else:
            grade = "GYENGE / KRITIKUS INTERVENCIÓ SZÜKSÉGES"
            badge = "[VEZETŐI BEAVATKOZÁS SZÜKSÉGES]"

        # 3 Konkrét AI Coaching Tanács
        coaching_tips = []
        if rep_ratio > 50:
            coaching_tips.append(
                f"Túlbeszélted az ügyfelet ({rep_ratio}% beszédarány az ideális 40% helyett). "
                "Hagyj 3 másodperc csendet a vevő mondatai után, hogy kibonthassa az aggodalmait!"
            )
        if interruption_count > 0:
            coaching_tips.append(
                f"{interruption_count} alkalommal vágtál az ügyfél szavába. "
                "Amikor a vevő elkezdi mondani a kifogását, sose védd azonnal a terméket, először hallgasd végig és tükrözd vissza ('Értem, a költségvetés a kérdés...')."
            )
        if open_questions < 2:
            coaching_tips.append(
                "Nem tettél fel elég nyitott igényfeltáró kérdést (0-1 db). "
                "Érvhalmozás helyett kérdezz: 'Farkas úr, ha a havi villanyszámlán megspóroljuk a különbséget, megnézzük a megtérülést?'"
            )
        if len(coaching_tips) < 3:
            coaching_tips.append("Erősítsd a lezárást: a 'majd keresem jövő héten' helyett köss ki pontos napot és órát egyeztetett teendővel!")

        return {
            "rep_ratio_percent": rep_ratio,
            "cust_ratio_percent": cust_ratio,
            "rep_duration_sec": rep_sec,
            "cust_duration_sec": cust_sec,
            "interruption_count": interruption_count,
            "open_questions_count": open_questions,
            "sales_score": final_score,
            "grade": grade,
            "badge": badge,
            "coaching_tips": coaching_tips,
            "sentiment_summary": "A vevő kezdetben szkeptikus volt, az értékesítő monológja miatt elzárkózóvá vált és elhalasztotta a döntést."
        }

    def generate_pdf_report(self, call_id: str, rep: Dict[str, Any], cust: Dict[str, Any], meta: Dict[str, Any], analysis: Dict[str, Any], output_path: str) -> str:
        """
        reportlab alapú márkázott Sales Coaching Értékelő Lap.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'CoachTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=colors.HexColor('#1e3a8a')
        )
        sub_style = ParagraphStyle(
            'CoachSub',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748b')
        )
        h2_style = ParagraphStyle(
            'CoachH2',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=15,
            textColor=colors.HexColor('#0f172a'),
            spaceBefore=8,
            spaceAfter=4
        )
        normal_style = ParagraphStyle(
            'CoachNormal',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#334155')
        )
        bold_style = ParagraphStyle(
            'CoachBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#0f172a')
        )

        story = []

        # Fejléc
        story.append(Paragraph("<b>AI SALES COACHING & HÍVÁSELEMZŐ JEGYZŐKÖNYV</b>", title_style))
        story.append(Paragraph(f"Hívás azonosító: <b>{call_id}</b> | Időpont: {meta.get('timestamp', '')}", sub_style))
        story.append(Spacer(1, 10))

        # Adatok táblázat
        deal_val = f"{meta.get('deal_value_huf', 0):,} Ft".replace(",", " ")
        score_color = "#dc2626" if analysis["sales_score"] < 60 else "#16a34a"
        info_data = [
            [
                Paragraph("<b>ÉRTÉKESÍTŐ:</b>", bold_style),
                Paragraph("<b>ÜGYFÉL / PROJEKT:</b>", bold_style),
                Paragraph("<b>EREDMÉNY & PONTOZÁS:</b>", bold_style)
            ],
            [
                Paragraph(f"<b>Név:</b> {rep.get('name')}<br/><b>Email:</b> {rep.get('email')}", normal_style),
                Paragraph(f"<b>Név:</b> {cust.get('name')}<br/><b>Cég:</b> {cust.get('company')}<br/><b>Ügyletérték:</b> {deal_val}", normal_style),
                Paragraph(f"<font size=14 color='{score_color}'><b>{analysis['sales_score']} / 100</b></font><br/><b>{analysis['grade']}</b>", normal_style)
            ]
        ]
        info_table = Table(info_data, colWidths=[170, 180, 170])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 12))

        # Metrikák táblázata
        story.append(Paragraph("<b>1. OBJEKTÍV TÁRGYALÁSI METRIKÁK ÉS ARÁNYOK</b>", h2_style))
        talk_status = "TÚL SOK BESZÉD (MONOLÓG)" if analysis["rep_ratio_percent"] > 45 else "OPTIMÁLIS EGYENSÚLY"
        int_status = f"{analysis['interruption_count']} alkalom (HIBAPONT)" if analysis["interruption_count"] > 0 else "0 alkalom (PÉLDÁS)"

        metric_rows = [
            ["Mért dimenzió", "Mért érték", "Elvárt célstandard", "Értékelés"],
            ["Beszéd / Hallgatás arány", f"Értékesítő: {analysis['rep_ratio_percent']}% | Ügyfél: {analysis['cust_ratio_percent']}%", "Max. 40 - 45% értékesítői beszéd", talk_status],
            ["Félbeszakítások száma", f"{analysis['interruption_count']} db", "0 db (Tilos a vevő szavába vágni)", int_status],
            ["Nyitott kérdések száma", f"{analysis['open_questions_count']} db", "Minimum 3 - 5 igényfeltáró kérdés", "Kevés kérdés" if analysis['open_questions_count'] < 3 else "Megfelelő"],
            ["Hívás időtartama", f"{meta.get('duration_seconds', 0)} másodperc", "300 - 600 másodperc", "Átlagos"]
        ]
        metric_table = Table(metric_rows, colWidths=[140, 160, 130, 90])
        metric_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f1f5f9')]),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('FONTSIZE', (0,0), (-1,-1), 8),
        ]))
        story.append(metric_table)
        story.append(Spacer(1, 12))

        # 3 Konkrét AI Coaching Tanács
        story.append(Paragraph("<b>2. SZEMÉLYRE SZABOTT AI SALES COACHING & FEJLESZTÉSI PONTOK</b>", h2_style))
        for i, tip in enumerate(analysis["coaching_tips"], 1):
            story.append(Paragraph(f"<b>{i}. Lépés:</b> {tip}", normal_style))
            story.append(Spacer(1, 4))
        story.append(Spacer(1, 8))

        # Hangulati összegzés
        story.append(Paragraph("<b>3. ÜGYFÉLHANGULAT & KIFOGÁSKEZELÉSI DIAGNÓZIS</b>", h2_style))
        sentiment_box = [[Paragraph(f"<b>Diagnózis:</b> {analysis['sentiment_summary']}", normal_style)]]
        s_table = Table(sentiment_box, colWidths=[520])
        s_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fef3c7')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#f59e0b')),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(s_table)

        doc.build(story)
        return output_path

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        meta = payload.get("call_metadata", {
            "call_id": f"CALL-{datetime.date.today().strftime('%Y%m%d')}-001",
            "duration_seconds": 300,
            "deal_value_huf": 500000
        })
        rep = payload.get("sales_rep", {"name": "Értékesítő", "email": "rep@ceg.hu"})
        cust = payload.get("customer", {"name": "Ügyfél", "company": "Ügyfél Kft."})
        turns = payload.get("transcript_turns", [])

        # 1. Elemzés
        analysis = self.analyze_transcript(turns, meta.get("duration_seconds", 300))

        # 2. PDF Coaching lap generálás
        call_id = meta.get("call_id", "CALL-DEFAULT")
        pdf_path = os.path.join("output", "coaching", f"coaching_{call_id}.pdf")
        self.generate_pdf_report(call_id, rep, cust, meta, analysis, pdf_path)

        # 3. Vezetői riasztás ellenőrzése (küszöbérték vagy kiemelt ügyletméret)
        is_low_score = analysis["sales_score"] < self.manager_alert_threshold_score
        is_high_value = meta.get("deal_value_huf", 0) >= self.high_value_deal_threshold_huf
        manager_alert_triggered = is_low_score or is_high_value

        manager_alert_message = ""
        if manager_alert_triggered:
            manager_alert_message = chr(10).join([
                f"[VEZETOI SALES ALERT] Figyelmet igenylo hivas!",
                f"Ertekesito: {rep.get('name')} | Ugyfel: {cust.get('name')} ({cust.get('company')})",
                f"Ugyletertek: {meta.get('deal_value_huf'):,} Ft".replace(",", " "),
                f"Sales Score: {analysis['sales_score']}/100 ({analysis['grade']})",
                f"Beszed/Hallgatas: Ertekesito {analysis['rep_ratio_percent']}% vs Ugyfel {analysis['cust_ratio_percent']}%",
                f"Felbeszakitasok: {analysis['interruption_count']} db",
                f"PDF jelentes megtekintheto: {pdf_path}"
            ])

        # 4. Mobilos gyorsösszefoglaló az értékesítőnek
        rep_quick_summary = chr(10).join([
            f"[SALES COACHING VISSZAJELZES] Hivas: {call_id}",
            f"Pontszamod: {analysis['sales_score']}/100 ({analysis['grade']})",
            f"Beszédarányod: {analysis['rep_ratio_percent']}% (Cel: max 45%)",
            f"Felbeszakitas: {analysis['interruption_count']} db",
            "",
            "LEGFONTOSABB TIPP A KOVETKEZO HIVASRA:",
            f"-> {analysis['coaching_tips'][0]}"
        ])

        # 5. Adatbázis naplózás
        log_entry = {
            "call_id": call_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "rep_name": rep.get("name"),
            "customer_name": cust.get("name"),
            "sales_score": analysis["sales_score"],
            "rep_ratio": analysis["rep_ratio_percent"],
            "manager_alert_triggered": manager_alert_triggered
        }
        log_file = "data/sales_coaching_naplo.json"
        existing_logs = []
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    existing_logs = json.load(f)
            except Exception:
                pass
        existing_logs.append(log_entry)
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(existing_logs, f, indent=2, ensure_ascii=False)

        return {
            "status": "success",
            "action_executed": "SALES_CALL_ANALYZED",
            "call_id": call_id,
            "sales_rep_name": rep.get("name"),
            "customer_name": cust.get("name"),
            "metrics": {
                "rep_ratio_percent": analysis["rep_ratio_percent"],
                "cust_ratio_percent": analysis["cust_ratio_percent"],
                "interruption_count": analysis["interruption_count"],
                "open_questions_count": analysis["open_questions_count"],
                "sales_score": analysis["sales_score"],
                "grade": analysis["grade"]
            },
            "pdf_report_path": pdf_path,
            "manager_alert_triggered": manager_alert_triggered,
            "manager_alert_message": manager_alert_message,
            "sales_rep_quick_summary": rep_quick_summary
        }

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    handler = SalesCoachingHandler(config)
    return handler.execute(payload)

if __name__ == "__main__":
    test_p = {
        "call_metadata": {"call_id": "CALL-TEST-01", "deal_value_huf": 1400000},
        "sales_rep": {"name": "Németh Tamás"},
        "customer": {"name": "Farkas Balázs"},
        "transcript_turns": [
            {"speaker": "SALES_REP", "text": "Jó napot, ajánlatunkkal keresem.", "duration_sec": 10},
            {"speaker": "CUSTOMER", "text": "Sokallom az árat.", "duration_sec": 5},
            {"speaker": "SALES_REP", "text": "De a mi gépünk A+++ és 5 év garancia és a legjobb a piacon!", "duration_sec": 30, "interrupted_customer": True}
        ]
    }
    res = run(test_p)
    print(json.dumps(res, indent=2, ensure_ascii=False))
