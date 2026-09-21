# -*- coding: utf-8 -*-
import os
import json
from pathlib import Path
from typing import Dict, Any

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from docx import Document

def format_huf(val: int | float) -> str:
    return f"{int(val):,} Ft".replace(",", " ")

def generate_pdf_report(report_data: Dict[str, Any], output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'RepTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1e293b')
    )
    
    subtitle_style = ParagraphStyle(
        'RepSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=12
    )
    
    h2_style = ParagraphStyle(
        'RepH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'RepBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155')
    )

    story = []
    
    # Fejléc
    story.append(Paragraph(f"{report_data['company_name']} - VEZETOI GYORSJELENTES", title_style))
    story.append(Paragraph(f"Idoszak: {report_data['period_label']} | Generalva: 2026-09-20 (Autonom Hub)", subtitle_style))
    story.append(Spacer(1, 10))

    # 4 Pillér KPI Táblázat
    kpi_table_data = [
        ["Piller", "Fobb Mutato", "Heti Ertek", "Statusz / Trend"],
        ["Penzugy & Szamlak", "Arbevetel / Koltsegek", f"{format_huf(report_data['kpi']['finance']['invoiced_revenue_huf'])} / {format_huf(report_data['kpi']['finance']['expenses_huf'])}", f"Arres: {report_data['kpi']['finance']['margin_pct']}% [POZITIV]"],
        ["Bank & Cash-Flow", "Zaro Likviditas", format_huf(report_data['kpi']['banking']['closing_cash_huf']), f"Netto Cash: +{format_huf(report_data['kpi']['banking']['net_cash_flow_weekly_huf'])} [STABIL]"],
        ["CRM & Ertekesites", "Megnyert Ugyfelek", f"{report_data['kpi']['crm']['won_deals_count']} db ({format_huf(report_data['kpi']['crm']['won_deals_value_huf'])})", f"Konverzios rata: {report_data['kpi']['crm']['conversion_rate_pct']}%"],
        ["Operacio & Projektek", "Hataridore Teljesites", f"{report_data['kpi']['operations']['on_time_delivery_pct']}%", f"{report_data['kpi']['operations']['completed_tasks_count']} lezart feladat"]
    ]

    t = Table(kpi_table_data, colWidths=[130, 140, 140, 110])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8fafc')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 8.5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    # Vezetői Elemzés és Akcióterv
    story.append(Paragraph("VEZETOI ELEMZES & TRENDEK", h2_style))
    for h in report_data['insights']['highlights']:
        story.append(Paragraph(f"[+] {h}", body_style))
    for a in report_data['insights']['alerts']:
        story.append(Paragraph(f"[!] {a}", body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("JAVASOLT VEZETOI AKCIOTERV A KOVETKEZO HETRE", h2_style))
    for idx, act in enumerate(report_data['insights']['action_plan'], 1):
        story.append(Paragraph(f"{idx}. {act}", body_style))

    doc.build(story)

def generate_docx_report(report_data: Dict[str, Any], output_path: str):
    doc = Document()
    doc.add_heading(f"{report_data['company_name']} - Vezetői Gyorsjelentés", level=1)
    doc.add_paragraph(f"Időszak: {report_data['period_label']} | Készült az AI Hub által.")
    
    table = doc.add_table(rows=1, cols=4)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Pillér'
    hdr_cells[1].text = 'Fő Mutató'
    hdr_cells[2].text = 'Érték'
    hdr_cells[3].text = 'Státusz'
    
    rows = [
        ('Pénzügy', 'Árbevétel', format_huf(report_data['kpi']['finance']['invoiced_revenue_huf']), f"Árrés: {report_data['kpi']['finance']['margin_pct']}%"),
        ('Bank & Cash-Flow', 'Záró Likviditás', format_huf(report_data['kpi']['banking']['closing_cash_huf']), 'Stabil'),
        ('CRM & Értékesítés', 'Megnyert Üzletek', format_huf(report_data['kpi']['crm']['won_deals_value_huf']), f"{report_data['kpi']['crm']['won_deals_count']} db"),
        ('Operáció', 'Határidő Tartás', f"{report_data['kpi']['operations']['on_time_delivery_pct']}%", f"{report_data['kpi']['operations']['completed_tasks_count']} feladat")
    ]
    for p, m, v, s in rows:
        row_cells = table.add_row().cells
        row_cells[0].text = p
        row_cells[1].text = m
        row_cells[2].text = v
        row_cells[3].text = s
        
    doc.add_heading("Javasolt Heti Akcióterv", level=2)
    for idx, act in enumerate(report_data['insights']['action_plan'], 1):
        doc.add_paragraph(f"{idx}. {act}")
        
    doc.save(output_path)

def run(payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    company_name = config.get("company_name", "ProfiTech Ipari & Kereskedelmi Kft.")
    period_label = payload.get("period_label", "2026. szeptember 14 - 2026. szeptember 20.")
    recipients = config.get("executive_email_recipients", "ugyvezetes@profitech.hu")
    
    kpi_data = payload.get("kpi_data", {})
    fin = kpi_data.get("finance", {})
    bank = kpi_data.get("banking", {})
    crm = kpi_data.get("crm", {})
    ops = kpi_data.get("operations", {})

    # AI Vezetői Elemzés & Értékelés (Insights)
    margin = fin.get("margin_pct", 40.0)
    rev_str = format_huf(fin.get("invoiced_revenue_huf", 0))
    cash_str = format_huf(bank.get("closing_cash_huf", 0))
    won_str = format_huf(crm.get("won_deals_value_huf", 0))

    highlights = [
        f"Kiváló árbevételi hét: {rev_str} kiszámlázva, magas {margin}%-os bruttó árréssel.",
        f"Erős értékesítési zárás: {crm.get('won_deals_count', 0)} megnyert ügyfélszerződés összesen {won_str} értékben.",
        f"Megbízható projekt operáció: {ops.get('on_time_delivery_pct', 0)}%-os határidőtartás mellett {ops.get('completed_tasks_count', 0)} feladat lezárva."
    ]

    alerts = []
    if fin.get("outstanding_receivables_huf", 0) > 2000000:
        alerts.append(f"Kintlévőség figyelmeztetés: {format_huf(fin['outstanding_receivables_huf'])} kifizetetlen vevői számla ketyeg.")
    if ops.get("critical_blockers_count", 0) > 0:
        alerts.append(f"Operatív blokkoló: {ops.get('blocker_summary', 'Kritikus blokkoló észlelve a kiemelt projekten.')}")

    action_plan = [
        f"Pénzügyi akció: A(z) {format_huf(fin.get('outstanding_receivables_huf', 0))} kintlévőségre indítsuk el a 03-as modult (40 EUR behajtási felszólító).",
        f"Értékesítési fókusz: A függőben lévő {format_huf(crm.get('sent_proposals_value_huf', 0))} értékű ajánlatból a 3 legnagyobb döntéshozó felhívása kedd délig.",
        f"Operatív beavatkozás: A(z) '{ops.get('blocker_summary', 'alvállalkozói csúszás')}' kapcsán azonnali vezetői egyeztetés az építésvezetővel."
    ]

    report_data = {
        "company_name": company_name,
        "period_label": period_label,
        "kpi": kpi_data,
        "insights": {
            "highlights": highlights,
            "alerts": alerts,
            "action_plan": action_plan
        }
    }

    # Fájlgenerálás
    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = str(out_dir / "Vezetoi_Gyorsjelentes_Legfrissebb.pdf")
    docx_path = str(out_dir / "Vezetoi_Gyorsjelentes_Legfrissebb.docx")

    generate_pdf_report(report_data, pdf_path)
    generate_docx_report(report_data, docx_path)

    # 30 Másodperces Mobilbarát Vezetői Email
    email_subject = f"[{company_name}] Heti Vezetői Gyorsjelentés - {period_label}"
    email_text = f"""Tisztelt Vezetőség!

Az alábbiakban olvasható a 30 másodperces vezetői gyorsjelentés ({period_label}):

📊 FŐ SZÁMOK:
• Kiszámlázott árbevétel: {rev_str} (Árrés: {margin}%)
• Záró banki likviditás: {cash_str} (Runway: {bank.get('runway_months', 3.0)} hónap)
• Megnyert új üzletek: {crm.get('won_deals_count', 0)} db ({won_str})
• Határidőtartás: {ops.get('on_time_delivery_pct', 0)}% ({ops.get('completed_tasks_count', 0)} lezárt task)

💡 FŐBB TRENDEK:
{chr(10).join(['[+] ' + h for h in highlights])}

⚠️ FIGYELEMFELHÍVÁS:
{chr(10).join(['[!] ' + a for a in alerts])}

🎯 3 JAVASOLT VEZETŐI LÉPÉS A HÉTRE:
1. {action_plan[0]}
2. {action_plan[1]}
3. {action_plan[2]}

A részletes, márkázott PDF és Word riport elkészült és letölthető az AI Hub felületéről.

Üdvözlettel,
AI Autonóm Riport Rendszer
"""

    # Telegram / Slack push üzenet
    first_alert = alerts[0] if alerts else "Minden rendben"
    push_message = (
        f"[{company_name}] Vezetoi Gyorsjelentes ({period_label})\n"
        f"- Arbevetel: {rev_str} (Arres: {margin}%)\n"
        f"- Zaro bank: {cash_str}\n"
        f"- Megnyert dealek: {won_str}\n"
        f"- Hataridotartas: {ops.get('on_time_delivery_pct', 0)}%\n"
        f"- Figyelmeztetes: {first_alert}\n"
        f"- PDF es Word riport generalva."
    )

    return {
        "status": "success",
        "report_period": period_label,
        "company_name": company_name,
        "recipients": recipients,
        "kpi_summary": {
            "invoiced_revenue": rev_str,
            "margin_pct": f"{margin}%",
            "closing_cash": cash_str,
            "won_deals_value": won_str,
            "on_time_delivery": f"{ops.get('on_time_delivery_pct', 0)}%"
        },
        "executive_insights": {
            "highlights_count": len(highlights),
            "alerts_count": len(alerts),
            "action_plan": action_plan
        },
        "generated_files": {
            "pdf_report": pdf_path,
            "docx_report": docx_path,
            "pdf_filename": "Vezetoi_Gyorsjelentes_Legfrissebb.pdf",
            "docx_filename": "Vezetoi_Gyorsjelentes_Legfrissebb.docx"
        },
        "delivery_channels": {
            "email": {
                "to": recipients,
                "subject": email_subject,
                "body_preview": email_text
            },
            "telegram_slack_push": {
                "message": push_message,
                "status": "READY_TO_DISPATCH"
            }
        }
    }
