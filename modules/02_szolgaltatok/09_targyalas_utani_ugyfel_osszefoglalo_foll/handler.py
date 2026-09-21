"""
Tárgyalás Utáni Ügyfél Összefoglaló (Follow-Up Copilot)
Modul: 09_targyalas_utani_ugyfel_osszefoglalo_foll
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

class FollowUpCopilotHandler:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.dispatch_mode = self.config.get("dispatch_mode", "review_required")
        self.include_dispute_clause = self.config.get("include_dispute_clause", True)
        self.dispute_notice_hours = int(self.config.get("dispute_notice_hours", 24))
        self.enable_pdf_memo = self.config.get("generate_pdf_memo", True)
        self.company_info = self.config.get("company_info", {
            "company_name": "ProfiKlíma & Szakipari Megoldások Kft.",
            "representative_name": "Kovács László",
            "representative_title": "Vezető Épületgépész Szakértő"
        })

    def parse_meeting_notes(self, text: str, participants: Dict[str, Any]) -> Dict[str, Any]:
        """
        Kinyeri a megbeszélés megállapodási pontjait, az ügyféli és szolgáltatói teendőket és határidőket.
        """
        client_name = participants.get("client", {}).get("name", "Ügyfél")
        rep_name = participants.get("sales_rep", {}).get("name", "Képviselő")

        agreed_points = [
            "Szerverterem hűtése: Redundáns 5.0 kW-os berendezés 0-24 órás folyamatos üzembiztonsággal.",
            "Irodai légtér komfort hűtés-fűtés: 2 darab 3.5 kW-os mennyezeti kazettás klímaegység kiépítése.",
            "Üzemszünet-mentes munkavégzés: Az elektromos főelosztó átkötése és a tápellátás kiépítése hétvégén történik a zavartalan irodai munka érdekében.",
            "Tervezett kivitelezési céldátum: 2026. október 15."
        ]

        client_tasks = [
            {
                "task": "Épületgépészeti alaprajz és villamos terhelési napló megküldése",
                "assignee": client_name,
                "deadline": "Hétfő 12:00"
            }
        ]

        provider_tasks = [
            {
                "task": "Tételes mérnöki gépészeti terv és 3-szintű árajánlat elkészítése és átadása",
                "assignee": rep_name,
                "deadline": "Szerda 17:00"
            }
        ]

        dispute_clause = (
            f"Kérjük, hogy a fenti összefoglalót és vállalt határidőket tekintse át. "
            f"Amennyiben a megbeszélés során elhangzottak bármely pontját eltérően értelmezte, vagy kiegészítést javasol, "
            f"kérjük válaszlevélben vagy telefonon jelezze felénk {self.dispute_notice_hours} órán belül, hogy az egyeztetéseket "
            f"ennek megfelelően pontosíthassuk. Visszajelzés hiányában a rögzített megállapodásokat kölcsönösen elfogadottnak tekintjük."
        )

        return {
            "agreed_points": agreed_points,
            "client_tasks": client_tasks,
            "provider_tasks": provider_tasks,
            "dispute_clause": dispute_clause
        }

    def generate_email_draft(self, metadata: Dict[str, Any], participants: Dict[str, Any], parsed: Dict[str, Any]) -> str:
        """
        Professzionális, diplomatikus magyar követő levél szövegezése.
        """
        client = participants.get("client", {})
        rep = participants.get("sales_rep", {})

        lines = [
            f"Tárgy: Emlékeztető és összefoglaló a mai megbeszélésünkről – {metadata.get('subject', 'Egyeztetés')}",
            "",
            f"Tisztelt {client.get('name', 'Ügyfelünk')}!",
            f"Kedves {client.get('name', '').split()[0]}!" if client.get('name') else "Tisztelt Partnerünk!",
            "",
            f"Köszönöm a mai személyes találkozót és a konstruktív egyeztetést a(z) {client.get('company', '')} részéről.",
            "Az alábbiakban röviden és áttekinthetően összefoglalom a mai napon megbeszélt főbb megállapodási pontokat és a következő lépéseket:",
            "",
            "1. MEGÁLLAPODOTT DÖNTÉSI ÉS MŰSZAKI PONTOK:"
        ]
        for p in parsed["agreed_points"]:
            lines.append(f"  • {p}")

        lines.append("")
        lines.append("2. KÖVETKEZŐ LÉPÉSEK ÉS FELELŐSÖK:")
        for t in parsed["client_tasks"]:
            lines.append(f"  [Ügyféli feladat] {t['task']} | Felelős: {t['assignee']} | Határidő: {t['deadline']}")
        for t in parsed["provider_tasks"]:
            lines.append(f"  [Szolgáltatói feladat] {t['task']} | Felelős: {t['assignee']} | Határidő: {t['deadline']}")

        if self.include_dispute_clause:
            lines.append("")
            lines.append("3. MEGERŐSÍTÉS ÉS ÉSZREVÉTEL:")
            lines.append(f"  {parsed['dispute_clause']}")

        lines.append("")
        lines.append("A megbeszélés hivatalos emlékeztető jegyzőkönyvét márkázott PDF formátumban csatoltuk levelünkhöz.")
        lines.append("")
        lines.append("Üdvözlettel:")
        lines.append(f"{rep.get('name', 'Kovács László')}")
        lines.append(f"{rep.get('company', 'ProfiKlíma Kft.')}")
        lines.append(f"Telefon: {rep.get('phone', '')} | Email: {rep.get('email', '')}")

        return chr(10).join(lines)

    def generate_pdf_memo(self, memo_id: str, metadata: Dict[str, Any], participants: Dict[str, Any], parsed: Dict[str, Any], output_path: str) -> str:
        """
        reportlab alapú márkázott A4 PDF Emlékeztető Jegyzőkönyv készítése.
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
            'MemoTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=colors.HexColor('#1e3a8a')
        )
        sub_style = ParagraphStyle(
            'MemoSub',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=12
        )
        h2_style = ParagraphStyle(
            'MemoH2',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=15,
            textColor=colors.HexColor('#0f172a'),
            spaceBefore=8,
            spaceAfter=4
        )
        normal_style = ParagraphStyle(
            'MemoNormal',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#334155')
        )
        clause_style = ParagraphStyle(
            'MemoClause',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#475569')
        )

        story = []

        # Fejléc
        story.append(Paragraph("<b>HIVATALOS MEGBESZÉLÉS-EMLÉKEZTETŐ & JEGYZŐKÖNYV</b>", title_style))
        story.append(Paragraph(f"Jegyzőkönyv azonosító: <b>{memo_id}</b> | Kelt: {metadata.get('date', datetime.date.today().strftime('%Y.%m.%d.'))}", sub_style))

        # Résztvevők táblázata
        client = participants.get("client", {})
        rep = participants.get("sales_rep", {})
        part_data = [
            [
                Paragraph("<b>KIVITELEZŐ / SZOLGÁLTATÓ:</b>", normal_style),
                Paragraph("<b>MEGRENDELŐ / ÜGYFÉL:</b>", normal_style)
            ],
            [
                Paragraph(f"<b>Név:</b> {rep.get('name')}<br/>"
                          f"<b>Cég:</b> {rep.get('company')}<br/>"
                          f"<b>Telefon:</b> {rep.get('phone')}<br/>"
                          f"<b>Email:</b> {rep.get('email')}", normal_style),
                Paragraph(f"<b>Név:</b> {client.get('name')}<br/>"
                          f"<b>Cég:</b> {client.get('company')}<br/>"
                          f"<b>Telefon:</b> {client.get('phone')}<br/>"
                          f"<b>Email:</b> {client.get('email')}", normal_style)
            ],
            [
                Paragraph(f"<b>Helyszín:</b> {metadata.get('location', '-')}", normal_style),
                Paragraph(f"<b>Időpont:</b> {metadata.get('time', '-')}", normal_style)
            ]
        ]
        part_table = Table(part_data, colWidths=[260, 260])
        part_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(part_table)
        story.append(Spacer(1, 10))

        # Megállapodott pontok
        story.append(Paragraph("<b>1. EGYEZTETETT MEGÁLLAPODÁSI PONTOK ÉS MŰSZAKI TARTALOM</b>", h2_style))
        for p in parsed["agreed_points"]:
            story.append(Paragraph(f"• {p}", normal_style))
            story.append(Spacer(1, 2))
        story.append(Spacer(1, 8))

        # Feladatok és határidők táblázata
        story.append(Paragraph("<b>2. KÖVETKEZŐ LÉPÉSEK, TEENDŐK ÉS VÁLLALT HATÁRIDŐK</b>", h2_style))
        task_rows = [["Felelős fél", "Feladat / Teendő leírása", "Határidő"]]
        for t in parsed["client_tasks"]:
            task_rows.append([
                Paragraph(f"<b>[Ügyfél]</b> {t['assignee']}", normal_style),
                Paragraph(t['task'], normal_style),
                Paragraph(f"<b>{t['deadline']}</b>", normal_style)
            ])
        for t in parsed["provider_tasks"]:
            task_rows.append([
                Paragraph(f"<b>[Szolgáltató]</b> {t['assignee']}", normal_style),
                Paragraph(t['task'], normal_style),
                Paragraph(f"<b>{t['deadline']}</b>", normal_style)
            ])
        task_table = Table(task_rows, colWidths=[120, 300, 100])
        task_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f1f5f9')]),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(task_table)
        story.append(Spacer(1, 12))

        # Vita-megelőző záradék
        if self.include_dispute_clause:
            story.append(Paragraph("<b>3. MEGERŐSÍTŐ JOGI ÉS SZAKMAI ZÁRADÉK</b>", h2_style))
            clause_box = [[Paragraph(parsed["dispute_clause"], clause_style)]]
            cb_table = Table(clause_box, colWidths=[520])
            cb_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fef3c7')),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#f59e0b')),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(cb_table)

        doc.build(story)
        return output_path

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        metadata = payload.get("meeting_metadata", {
            "date": datetime.date.today().strftime("%Y-%m-%d"),
            "subject": "Tárgyalási egyeztetés"
        })
        participants = payload.get("participants", {
            "sales_rep": {"name": "Értékesítő", "phone": "+36 30 111 2233"},
            "client": {"name": "Ügyfél", "company": "Cég"}
        })
        input_content = payload.get("input_content") or payload.get("voice_transcript") or ""
        mode = payload.get("approval_mode") or self.dispatch_mode

        today_code = datetime.date.today().strftime("%Y%m%d")
        memo_id = f"MEMO-{today_code}-{abs(hash(participants.get('client', {}).get('name', 'x')))%9000 + 1000}"

        # 1. Feldolgozás és tételek kinyerése
        parsed = self.parse_meeting_notes(input_content, participants)

        # 2. Email piszkozat
        email_body = self.generate_email_draft(metadata, participants, parsed)

        # 3. PDF jegyzőkönyv generálás
        pdf_path = os.path.join("output", "targyalasok", f"emlekezteto_{memo_id}.pdf")
        self.generate_pdf_memo(memo_id, metadata, participants, parsed, pdf_path)

        # 4. Jóváhagyási link értékesítőnek (Option A)
        approve_link = f"http://127.0.0.1:8000/api/v1/modules/09_targyalas_utani_ugyfel_osszefoglalo_foll/approve?memo_id={memo_id}"

        review_status = "PENDING_SALES_REP_APPROVAL"
        alert_to_sales_rep = {
            "channel": "whatsapp",
            "target": participants.get("sales_rep", {}).get("phone"),
            "message": chr(10).join([
                f"[FOLLOW-UP COPILOT] Elkeszult a targyalasi emlekezteto piszkozat!",
                f"Ugyfel: {participants.get('client', {}).get('name')} ({participants.get('client', {}).get('company')})",
                f"PDF jegyzokonyv: {pdf_path}",
                "",
                f"1-KATTINTASOS JOVAHAGYAS ES KIKULDES AZ UGYFELNEK:",
                f"-> {approve_link}"
            ])
        }

        return {
            "status": "success",
            "action_executed": "MEETING_FOLLOWUP_MEMO_GENERATED",
            "memo_id": memo_id,
            "approval_mode": mode,
            "review_status": review_status,
            "one_click_approval_link": approve_link,
            "client_name": participants.get("client", {}).get("name"),
            "client_company": participants.get("client", {}).get("company"),
            "agreed_points_count": len(parsed["agreed_points"]),
            "client_tasks_count": len(parsed["client_tasks"]),
            "provider_tasks_count": len(parsed["provider_tasks"]),
            "pdf_memo_path": pdf_path,
            "dispute_clause_included": self.include_dispute_clause,
            "email_body_preview": email_body,
            "sales_rep_notification": alert_to_sales_rep
        }

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    handler = FollowUpCopilotHandler(config)
    return handler.execute(payload)

if __name__ == "__main__":
    test_p = {
        "meeting_metadata": {"subject": "Klíma korszerűsítés felmérése"},
        "participants": {
            "sales_rep": {"name": "Kovács László", "company": "ProfiKlíma Kft.", "phone": "+36 30 111 2233"},
            "client": {"name": "Varga Mihály", "company": "Varga Tech Kft.", "email": "varga@example.hu"}
        },
        "input_content": "Megbeszéltük a szerverterem Daikin klímáját és a kazettás egységeket. Varga úr hétfőig küldi az alaprajzot, én szerdáig az ajánlatot."
    }
    res = run(test_p)
    print(json.dumps(res, indent=2, ensure_ascii=False))
