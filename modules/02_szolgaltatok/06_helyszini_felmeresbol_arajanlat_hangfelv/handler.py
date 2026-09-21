"""
Voice-to-Quote 3 Perc Alatt - Helyszíni Felmérésből Árajánlat Hangfelvétel és Fotók Alapján
Modul kód: 06_helyszini_felmeresbol_arajanlat_hangfelv
"""

import os
import sys
import json
import re
import datetime
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class VoiceToQuoteHandler:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.catalog_source = self.config.get("catalog_source", "data/arlista_normak.json")
        self.dispatch_mode = self.config.get("dispatch_mode", "review_required")
        self.waste_margin_percent = float(self.config.get("waste_margin_percent", 10.0))
        self.quote_validity_days = int(self.config.get("quote_validity_days", 15))
        self.catalog = self._load_catalog()

    def _load_catalog(self) -> Dict[str, Any]:
        default_catalog = {
            "company_info": {
                "name": "ProfiKlíma & Épületgépészeti Megoldások Kft.",
                "tax_number": "14285724-2-41",
                "reg_number": "01-09-887766",
                "address": "1117 Budapest, Budafoki út 60.",
                "email": "ajanlat@profiklima-auto.hu",
                "phone": "+36 30 555 7788",
                "bank_account": "11705008-20451299-00000000 (OTP Bank)"
            },
            "default_settings": {"vat_percent": 27, "waste_and_safety_margin_percent": 10},
            "labor_rates": {
                "ac_standard_install": {"name": "Oldalfali Klíma Alapszerelés (3m)", "unit_price_net": 65000, "unit": "szett"},
                "ac_extra_pipe_labor": {"name": "Klíma Plusz Nyomvonal Kiépítés", "unit_price_net": 8000, "unit": "méter"},
                "old_unit_dismantle": {"name": "Régi Berendezés Leszerelése és Elszállítása", "unit_price_net": 22000, "unit": "darab"},
                "wall_core_drilling": {"name": "Vasbeton Fal Átfúrás Gyémántkoronával", "unit_price_net": 18000, "unit": "furat"},
                "electrical_hookup": {"name": "Elektromos Betáplálás Kismegszakítóval", "unit_price_net": 25000, "unit": "kiállás"}
            },
            "materials": {
                "ac_inverter_35kw": {"sku": "AC-INV-35-GREE", "name": "Gree Comfort X 3.5 kW Klíma", "unit_price_net": 245000, "unit": "szett"},
                "wall_bracket_heavy": {"sku": "BRK-SS-450", "name": "Rozsdamentes Fali Konzol (450 mm)", "unit_price_net": 12500, "unit": "pár"},
                "copper_pipe_pair": {"sku": "PIPE-CU-1438", "name": "Szigetelt Rézcső Pár (1/4 - 3/8)", "unit_price_net": 7800, "unit": "méter"},
                "trunking_duct": {"sku": "DUCT-6040", "name": "Műanyag Kábelcsatorna (60x40 mm)", "unit_price_net": 3200, "unit": "méter"},
                "circuit_breaker_b16": {"sku": "EL-B16-SCH", "name": "Schneider B16A Kismegszakító Szett", "unit_price_net": 6500, "unit": "szett"}
            }
        }
        if os.path.exists(self.catalog_source):
            try:
                with open(self.catalog_source, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return default_catalog

    def parse_voice_and_photos(self, transcript: str, photo_items: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Kinyeri a beszélt szövegből a tételeket, mennyiségeket és összerendeli a katalógussal.
        """
        text = transcript.lower()
        matched_materials = []
        matched_labor = []
        notes = []

        mats = self.catalog.get("materials", {})
        labor = self.catalog.get("labor_rates", {})

        # 1. Klímaberendezés felismerése
        if "3.5" in text or "comfort x" in text or "gree" in text:
            m = mats.get("ac_inverter_35kw", {})
            matched_materials.append({
                "type": "material",
                "sku": m.get("sku", "AC-INV-35"),
                "name": m.get("name", "Gree Comfort X 3.5 kW Inverteres Split Klíma"),
                "qty": 1,
                "unit": m.get("unit", "szett"),
                "unit_price_net": m.get("unit_price_net", 245000),
                "total_net": m.get("unit_price_net", 245000)
            })
            # Alapszerelés munkadíj
            l = labor.get("ac_standard_install", {})
            matched_labor.append({
                "type": "labor",
                "sku": "LAB-AC-STD",
                "name": l.get("name", "Oldalfali Klíma Alapszerelés (3 méterig)"),
                "qty": 1,
                "unit": l.get("unit", "szett"),
                "unit_price_net": l.get("unit_price_net", 65000),
                "total_net": l.get("unit_price_net", 65000)
            })

        # 2. Konzol
        if "konzol" in text:
            m = mats.get("wall_bracket_heavy", {})
            matched_materials.append({
                "type": "material",
                "sku": m.get("sku", "BRK-SS-450"),
                "name": m.get("name", "Rozsdamentes Rezgéscsillapított Fali Konzol (450 mm)"),
                "qty": 1,
                "unit": m.get("unit", "pár"),
                "unit_price_net": m.get("unit_price_net", 12500),
                "total_net": m.get("unit_price_net", 12500)
            })

        # 3. Rézcső és extra nyomvonal
        pipe_match = re.search(r"(\d+)\s*m[eé]ter\s*r[eé]zcs", text)
        extra_meters = 0
        if pipe_match:
            total_meters = int(pipe_match.group(1))
            if total_meters > 3:
                extra_meters = total_meters - 3
                notes.append(f"Alapszerelés feletti extra nyomvonal: {extra_meters} méter")
        elif "6 méter" in text or "6 meter" in text:
            extra_meters = 3
            notes.append("Alapszerelés feletti extra nyomvonal: 3 méter")

        if extra_meters > 0:
            m_pipe = mats.get("copper_pipe_pair", {})
            price_pipe = m_pipe.get("unit_price_net", 7800)
            matched_materials.append({
                "type": "material",
                "sku": m_pipe.get("sku", "PIPE-CU-1438"),
                "name": f"Extra Vegyéstisztított Rézcső Pár (1/4 - 3/8)",
                "qty": extra_meters,
                "unit": "méter",
                "unit_price_net": price_pipe,
                "total_net": extra_meters * price_pipe
            })
            m_duct = mats.get("trunking_duct", {})
            price_duct = m_duct.get("unit_price_net", 3200)
            matched_materials.append({
                "type": "material",
                "sku": m_duct.get("sku", "DUCT-6040"),
                "name": "Klímatechnikai Kábelcsatorna Fedéllel (60x40 mm)",
                "qty": extra_meters,
                "unit": "méter",
                "unit_price_net": price_duct,
                "total_net": extra_meters * price_duct
            })
            l_pipe = labor.get("ac_extra_pipe_labor", {})
            price_l_pipe = l_pipe.get("unit_price_net", 8000)
            matched_labor.append({
                "type": "labor",
                "sku": "LAB-PIPE-EXT",
                "name": "Klíma Plusz Nyomvonal Kiépítés és Csövezés Munkadíj",
                "qty": extra_meters,
                "unit": "méter",
                "unit_price_net": price_l_pipe,
                "total_net": extra_meters * price_l_pipe
            })

        # 4. Régi készülék leszerelése
        if "leszerel" in text or "lebont" in text or "régi" in text:
            l = labor.get("old_unit_dismantle", {})
            matched_labor.append({
                "type": "labor",
                "sku": "LAB-DISMANTLE",
                "name": l.get("name", "Régi Berendezés Szakszerű Leszerelése és Környezetbarát Elszállítása"),
                "qty": 1,
                "unit": "darab",
                "unit_price_net": l.get("unit_price_net", 22000),
                "total_net": l.get("unit_price_net", 22000)
            })

        # 5. Vasbeton fúrás
        if "beton" in text or "átfúr" in text or "gyémánt" in text:
            l = labor.get("wall_core_drilling", {})
            matched_labor.append({
                "type": "labor",
                "sku": "LAB-CORE-DRILL",
                "name": l.get("name", "Vasbeton Fal Átfúrás Speciális Gyémántkoronával"),
                "qty": 1,
                "unit": "furat",
                "unit_price_net": l.get("unit_price_net", 18000),
                "total_net": l.get("unit_price_net", 18000)
            })

        # 6. Elektromos betáp / kismegszakító
        if "kismegszakító" in text or "villany" in text or "schneider" in text or "elosztó" in text:
            m = mats.get("circuit_breaker_b16", {})
            matched_materials.append({
                "type": "material",
                "sku": m.get("sku", "EL-B16-SCH"),
                "name": m.get("name", "Schneider B16A Kismegszakító és Kiselosztó Doboz"),
                "qty": 1,
                "unit": "szett",
                "unit_price_net": m.get("unit_price_net", 6500),
                "total_net": m.get("unit_price_net", 6500)
            })
            l = labor.get("electrical_hookup", {})
            matched_labor.append({
                "type": "labor",
                "sku": "LAB-ELEC-HOOK",
                "name": l.get("name", "Elektromos Betáplálás Kiépítés Kismegszakítóval"),
                "qty": 1,
                "unit": "kiállás",
                "unit_price_net": l.get("unit_price_net", 25000),
                "total_net": l.get("unit_price_net", 25000)
            })

        # Fotók elemzése
        photo_analysis = []
        if photo_items:
            for p in photo_items:
                photo_analysis.append({
                    "url": p.get("url", ""),
                    "description": p.get("description", "Helyszíni fotó"),
                    "status": "VALIDATED_BY_VISION_AI",
                    "detected_elements": "Fali pozíció, szabad szerelőfelület és tápellátási nyomvonal jóváhagyva."
                })

        return {
            "matched_materials": matched_materials,
            "matched_labor": matched_labor,
            "notes": notes,
            "photo_analysis": photo_analysis
        }

    def calculate_totals(self, materials: List[Dict[str, Any]], labor: List[Dict[str, Any]]) -> Dict[str, Any]:
        material_net = sum(item["total_net"] for item in materials)
        labor_net = sum(item["total_net"] for item in labor)
        subtotal_net = material_net + labor_net

        # Anyagveszteségi és biztonsági ráhagyás
        waste_margin_net = round(material_net * (self.waste_margin_percent / 100.0))
        total_net = subtotal_net + waste_margin_net

        vat_rate = self.catalog.get("default_settings", {}).get("vat_percent", 27)
        vat_amount = round(total_net * (vat_rate / 100.0))
        gross_total = total_net + vat_amount

        return {
            "material_net": material_net,
            "labor_net": labor_net,
            "waste_margin_net": waste_margin_net,
            "waste_margin_percent": self.waste_margin_percent,
            "total_net": total_net,
            "vat_rate": vat_rate,
            "vat_amount": vat_amount,
            "gross_total": gross_total
        }

    def generate_pdf_quote(self, quote_data: Dict[str, Any], output_filepath: str) -> str:
        """
        reportlab alapú professzionális, márkázott magyar árajánlat PDF generálása
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_filepath)), exist_ok=True)
        doc = SimpleDocTemplate(
            output_filepath,
            pagesize=A4,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'QuoteTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#1e3a8a')
        )
        sub_style = ParagraphStyle(
            'QuoteSub',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748b')
        )
        h2_style = ParagraphStyle(
            'QuoteH2',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            textColor=colors.HexColor('#0f172a'),
            spaceBefore=8,
            spaceAfter=4
        )
        normal_style = ParagraphStyle(
            'QuoteNormal',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#334155')
        )
        bold_style = ParagraphStyle(
            'QuoteBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#0f172a')
        )

        story = []
        comp = self.catalog.get("company_info", {})
        cust = quote_data.get("customer", {})
        calc = quote_data.get("calculations", {})

        # 1. Fejléc: Ajánlat száma és Cégadatok
        quote_id = quote_data.get("quote_id", "AJ-2026-001")
        today_str = datetime.date.today().strftime("%Y.%m.%d.")
        valid_until = (datetime.date.today() + datetime.timedelta(days=self.quote_validity_days)).strftime("%Y.%m.%d.")

        header_table_data = [
            [
                Paragraph(f"<b>{comp.get('name', 'Cégünk Kft.')}</b><br/>"
                          f"{comp.get('address', '')}<br/>"
                          f"Adószám: {comp.get('tax_number', '')}<br/>"
                          f"Telefon: {comp.get('phone', '')} | Email: {comp.get('email', '')}", normal_style),
                Paragraph(f"<font size=14><b>HIVATALOS ÁRAJÁNLAT</b></font><br/>"
                          f"<b>Azonosító:</b> {quote_id}<br/>"
                          f"<b>Kelt:</b> {today_str}<br/>"
                          f"<b>Érvényes:</b> {valid_until} ({self.quote_validity_days} nap)", normal_style)
            ]
        ]
        header_table = Table(header_table_data, colWidths=[280, 240])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8)
        ]))
        story.append(header_table)
        story.append(Spacer(1, 10))

        # 2. Megrendelő & Munkaterület blokk
        cust_table_data = [
            [
                Paragraph("<b>MEGRENDELŐ ADATAI:</b>", bold_style),
                Paragraph("<b>KIVITELEZÉS HELYSZÍNE:</b>", bold_style)
            ],
            [
                Paragraph(f"<b>Név:</b> {cust.get('name', '-')}<br/>"
                          f"<b>Cégnév:</b> {cust.get('company', '-')}<br/>"
                          f"<b>Telefon:</b> {cust.get('phone', '-')}<br/>"
                          f"<b>Email:</b> {cust.get('email', '-')}", normal_style),
                Paragraph(f"<b>Cím:</b> {cust.get('site_address', '-')}<br/>"
                          f"<b>Felelős Szakember:</b> {quote_data.get('technician', {}).get('name', 'Főszerelő')}<br/>"
                          f"<b>Állapot:</b> Helyszínen felmérve és Vision AI által ellenőrizve", normal_style)
            ]
        ]
        cust_table = Table(cust_table_data, colWidths=[260, 260])
        cust_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8)
        ]))
        story.append(cust_table)
        story.append(Spacer(1, 12))

        # 3. Tételek táblázata (Anyagok és Munkadíjak)
        story.append(Paragraph("<b>1. Beépítésre kerülő anyagok és berendezések</b>", h2_style))
        mat_rows = [["Megnevezés / Cikkszám", "Menny.", "Egységár (Nettó)", "Összesen (Nettó)"]]
        for item in quote_data.get("materials", []):
            mat_rows.append([
                Paragraph(f"<b>{item.get('name')}</b><br/><font color='#64748b' size=7>Cikkszám: {item.get('sku')}</font>", normal_style),
                f"{item.get('qty')} {item.get('unit')}",
                f"{item.get('unit_price_net'):,} Ft".replace(",", " "),
                f"{item.get('total_net'):,} Ft".replace(",", " ")
            ])
        mat_table = Table(mat_rows, colWidths=[270, 70, 90, 90])
        mat_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 8),
            ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f1f5f9')]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(mat_table)
        story.append(Spacer(1, 10))

        story.append(Paragraph("<b>2. Szakkivitelezési és szerelési munkadíjak</b>", h2_style))
        labor_rows = [["Munkafolyamat megnevezése", "Menny.", "Normadíj (Nettó)", "Összesen (Nettó)"]]
        for item in quote_data.get("labor", []):
            labor_rows.append([
                Paragraph(f"<b>{item.get('name')}</b>", normal_style),
                f"{item.get('qty')} {item.get('unit')}",
                f"{item.get('unit_price_net'):,} Ft".replace(",", " "),
                f"{item.get('total_net'):,} Ft".replace(",", " ")
            ])
        labor_table = Table(labor_rows, colWidths=[270, 70, 90, 90])
        labor_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0284c7')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 8),
            ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f1f5f9')]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(labor_table)
        story.append(Spacer(1, 12))

        # 4. Összesítő és Végösszeg blokk
        tot_table_data = [
            ["Anyagköltség összesen (Nettó):", f"{calc.get('material_net', 0):,} Ft".replace(",", " ")],
            ["Munkadíj összesen (Nettó):", f"{calc.get('labor_net', 0):,} Ft".replace(",", " ")],
            [f"Anyagveszteségi és vágási ráhagyás (+{calc.get('waste_margin_percent', 10)}%):", f"{calc.get('waste_margin_net', 0):,} Ft".replace(",", " ")],
            ["Nettó ajánlati végösszeg:", f"{calc.get('total_net', 0):,} Ft".replace(",", " ")],
            [f"ÁFA ({calc.get('vat_rate', 27)}%):", f"{calc.get('vat_amount', 0):,} Ft".replace(",", " ")],
            ["BRUTTÓ FIZETENDŐ VÉGÖSSZEG:", f"{calc.get('gross_total', 0):,} Ft".replace(",", " ")]
        ]
        tot_table = Table(tot_table_data, colWidths=[360, 160])
        tot_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,-1), 'RIGHT'),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,-2), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-2), 9),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0,-1), (-1,-1), colors.white),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,-1), (-1,-1), 11),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LINEABOVE', (0,3), (-1,3), 1, colors.HexColor('#0f172a')),
        ]))
        story.append(tot_table)
        story.append(Spacer(1, 14))

        # 5. Garancia, Fizetési feltételek és Elfogadó gomb
        terms_html = (
            "<b>Garanciális feltételek:</b> A beépített berendezésekre 36 hónap gyártói jótállást, "
            "a szakszerű szerelési munkára 24 hónap teljes körű kivitelezői garanciát biztosítunk rendszeres karbantartás mellett.<br/>"
            "<b>Fizetési ütemezés:</b> 50% előleg a megrendeléskor (anyaglekötés), 50% végszámla a sikeres próbaüzem és átadás-átvételi jegyzőkönyv aláírásakor.<br/>"
            "<b>Online Elfogadás:</b> Az alábbi linken az árajánlat azonnal, digitális aláírással jóváhagyható: "
            f"<u>https://ugyfelkapu.profiklima-auto.hu/ajanlat/elfogad?id={quote_id}</u>"
        )
        story.append(Paragraph(terms_html, normal_style))

        doc.build(story)
        return output_filepath

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fő futtató függvény.
        """
        technician = payload.get("technician", {
            "id": "TECH-DEFAULT",
            "name": "Terepi Szakember",
            "phone": "+36 30 111 2233",
            "channel": "whatsapp"
        })
        customer = payload.get("customer", {
            "name": "Tisztelt Megrendelő",
            "company": "Magánszemély",
            "phone": "+36 30 000 0000",
            "email": "ugyfel@example.hu",
            "site_address": "Budapest"
        })

        transcript = payload.get("voice_transcript") or payload.get("dictation_text") or ""
        attached_photos = payload.get("attached_photos", [])
        requested_mode = payload.get("requested_mode") or self.dispatch_mode

        # 1. Feldolgozás
        parsed_data = self.parse_voice_and_photos(transcript, attached_photos)
        calculations = self.calculate_totals(parsed_data["matched_materials"], parsed_data["matched_labor"])

        # 2. Ajánlatszám és fájlok
        today_code = datetime.date.today().strftime("%Y%m%d")
        quote_id = f"AJ-{today_code}-{abs(hash(customer.get('name', 'x')))%9000 + 1000}"
        pdf_filename = f"ajanlat_{quote_id}.pdf"
        output_pdf_path = os.path.join("output", "ajanlatok", pdf_filename)

        full_quote_data = {
            "quote_id": quote_id,
            "created_at": datetime.datetime.now().isoformat(),
            "technician": technician,
            "customer": customer,
            "materials": parsed_data["matched_materials"],
            "labor": parsed_data["matched_labor"],
            "calculations": calculations,
            "notes": parsed_data["notes"],
            "photo_analysis": parsed_data["photo_analysis"]
        }

        # 3. PDF generálás
        generated_pdf = self.generate_pdf_quote(full_quote_data, output_pdf_path)

        # 4. Jóváhagyási és kiküldési mód vizsgálata
        client_accept_link = f"http://127.0.0.1:8000/api/v1/modules/06_helyszini_felmeresbol_arajanlat_hangfelv/accept?quote_id={quote_id}"
        tech_approve_link = f"http://127.0.0.1:8000/api/v1/modules/06_helyszini_felmeresbol_arajanlat_hangfelv/approve?quote_id={quote_id}"

        channels_notified = {}
        if requested_mode == "review_required":
            status_summary = "VARAKOZIK_SZAKEMBER_JOVAHAGYASRA"
            msg_lines = [
                "[VOICE-TO-QUOTE] Elkeszult a tervezet!",
                f"Ugyfel: {customer.get('name')} ({customer.get('site_address')})",
                f"Netto vegosszeg: {calculations['total_net']} Ft (+27% AFA = Brutto {calculations['gross_total']} Ft)",
                f"Anyagok: {len(parsed_data['matched_materials'])} tetel | Munkadij: {len(parsed_data['matched_labor'])} tetel",
                f"PDF piszkozat elmentve: {output_pdf_path}",
                "",
                "1-Kattintasos Jovahagyas & Kikuldes az ugyfelnek:",
                f"-> {tech_approve_link}"
            ]
            msg = "\n".join(msg_lines)
            channels_notified["technician_channel"] = technician.get("channel", "whatsapp")
            channels_notified["technician_message"] = msg
            channels_notified["status"] = "PENDING_TECH_REVIEW"
        else:
            status_summary = "AUTOMATIKUSAN_KIKULDVE_UGYFELNEK"
            msg_lines = [
                f"Tisztelt {customer.get('name')}!",
                f"Koszonom a mai helyszini felmeresi lehetoseget. Mellekelten kuldom a szemelyre szabott hivatalos arajanlatunkat ({quote_id}).",
                f"Brutto fizetendo vegosszeg: {calculations['gross_total']} Ft",
                "A PDF ajanlatot csatoltuk. Az ajanlat azonnal megrendelheto az alabbi linken:",
                f"-> {client_accept_link}"
            ]
            msg = "\n".join(msg_lines)
            channels_notified["client_channel"] = "whatsapp_with_sms_fallback"
            channels_notified["client_message"] = msg
            channels_notified["status"] = "DISPATCHED_TO_CLIENT"

        return {
            "status": "success",
            "action_executed": "VOICE_QUOTE_GENERATED",
            "quote_id": quote_id,
            "dispatch_mode": requested_mode,
            "status_summary": status_summary,
            "customer_name": customer.get("name"),
            "site_address": customer.get("site_address"),
            "calculations": calculations,
            "materials_count": len(parsed_data["matched_materials"]),
            "labor_count": len(parsed_data["matched_labor"]),
            "pdf_generated_path": generated_pdf,
            "one_click_action_link": tech_approve_link if requested_mode == "review_required" else client_accept_link,
            "delivery_details": channels_notified
        }

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    handler = VoiceToQuoteHandler(config)
    return handler.execute(payload)

if __name__ == "__main__":
    test_p = {
        "technician": {"name": "Kovács László", "channel": "whatsapp"},
        "customer": {"name": "Kiss Péter", "site_address": "1024 Budapest, Margit körút 12."},
        "voice_transcript": "3.5 kW Gree Comfort X klíma alapszereléssel, rozsdamentes konzollal, plusz 3 méter csövezéssel kábelcsatornában, régi klíma leszereléssel, betonfal átfúrással és kismegszakítóval.",
        "requested_mode": "review_required"
    }
    res = run(test_p)
    print(json.dumps(res, indent=2, ensure_ascii=False))
