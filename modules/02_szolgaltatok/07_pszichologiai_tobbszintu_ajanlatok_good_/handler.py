"""
Pszichológiai Többszintű Ajánlatok (Good-Better-Best Csomagok)
Modul: 07_pszichologiai_tobbszintu_ajanlatok_good_
"""

import os
import sys
import json
import datetime
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class GoodBetterBestHandler:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        customization = self.config.get("packages_customization", {})
        self.good_label = customization.get("good_label", "Alap (Racionális Választás)")
        self.better_label = customization.get("better_label", "Ajánlott Prémium (Legnépszerűbb)")
        self.best_label = customization.get("best_label", "VIP All-Inclusive (Csúcsminőség)")
        self.better_markup_percent = float(customization.get("better_markup_percent", 25.0))
        self.best_markup_percent = float(customization.get("best_markup_percent", 65.0))
        self.highlighted_package = customization.get("highlighted_package", "better")

        follow_up = self.config.get("follow_up_automation", {})
        self.enable_48h_reminder = follow_up.get("enable_48h_reminder", True)
        self.enable_downsell_upsell = follow_up.get("enable_downsell_upsell", True)
        self.upsell_addon_price_huf = int(follow_up.get("upsell_addon_price_huf", 15000))

    def build_packages(self, base_material_net: float, base_labor_net: float) -> Dict[str, Any]:
        """
        Kialakítja a 3 szintű pszichológiai csomagot árakkal és feature összehasonlítással.
        """
        base_net = base_material_net + base_labor_net

        # 1. GOOD (Alap)
        good_mat_net = round(base_material_net)
        good_labor_net = round(base_labor_net)
        good_total_net = good_mat_net + good_labor_net
        good_vat = round(good_total_net * 0.27)
        good_gross = good_total_net + good_vat

        # 2. BETTER (Prémium +25% felár)
        better_mat_net = round(base_material_net * (1 + self.better_markup_percent / 100.0))
        better_labor_net = round(base_labor_net * 1.1)
        better_total_net = better_mat_net + better_labor_net
        better_vat = round(better_total_net * 0.27)
        better_gross = better_total_net + better_vat

        # 3. BEST (VIP +65% felár)
        best_mat_net = round(base_material_net * (1 + self.best_markup_percent / 100.0))
        best_labor_net = round(base_labor_net * 1.25)
        best_total_net = best_mat_net + best_labor_net
        best_vat = round(best_total_net * 0.27)
        best_gross = best_total_net + best_vat

        packages = {
            "good": {
                "id": "good",
                "title": self.good_label,
                "badge": "Megbízható & Költséghatékony",
                "is_highlighted": False,
                "equipment": "Gree Pulse 3.2 kW A+/A+ Inverteres Klíma",
                "warranty_years": 1,
                "energy_rating": "A+ / A+",
                "noise_level": "28 dB (Standard)",
                "smart_wifi": "Opcionális (+15 000 Ft)",
                "annual_maintenance": "Díjköteles (22 000 Ft/év)",
                "service_response_time": "3 - 5 munkanap",
                "included_extras": [
                    "Standard oldalfali szerelés 3 méterig",
                    "1 év teljes körű jogszabályi garancia",
                    "Rendeltetésszerű alapfunkciók"
                ],
                "pricing": {
                    "material_net": good_mat_net,
                    "labor_net": good_labor_net,
                    "total_net": good_total_net,
                    "vat_amount": good_vat,
                    "gross_total": good_gross
                }
            },
            "better": {
                "id": "better",
                "title": self.better_label,
                "badge": "LEGNÉPSZERŰBB - LEGJOBB ÁR/ÉRTÉK ARÁNY",
                "is_highlighted": True,
                "equipment": "Gree Comfort X 3.5 kW A++/A+ Japán Kompresszoros Klíma",
                "warranty_years": 3,
                "energy_rating": "A++ / A+",
                "noise_level": "21 dB (Suttogó halk éjszakai üzemmód)",
                "smart_wifi": "Beépített Okosotthon & Mobilapplikáció (Alaptartozék)",
                "annual_maintenance": "1. ÉVI AJÁNDÉK Szezonális Tisztítás & Ózonos Fertőtlenítés",
                "service_response_time": "48 órás garantált szakember reakció",
                "included_extras": [
                    "Standard oldalfali szerelés 3 méterig + prémium kábelcsatorna",
                    "3 év teljes körű kiterjesztett garancia",
                    "Cold Plasma antibakteriális légszűrő vírusok és pollenek ellen",
                    "I-Feel intelligens távirányítós hőmérséklet-követés",
                    "Ajándék 1. évi szezonális karbantartás (25 000 Ft értékben)"
                ],
                "pricing": {
                    "material_net": better_mat_net,
                    "labor_net": better_labor_net,
                    "total_net": better_total_net,
                    "vat_amount": better_vat,
                    "gross_total": better_gross
                }
            },
            "best": {
                "id": "best",
                "title": self.best_label,
                "badge": "VIP ALL-INCLUSIVE - MAXIMÁLIS LUXUS ÉS NYUGALOM",
                "is_highlighted": False,
                "equipment": "Daikin Perfera / Stylish 3.5 kW A+++ Csúcskategóriás Dizájn Klíma",
                "warranty_years": 5,
                "energy_rating": "A+++ / A+++ (Minimális fogyasztás)",
                "noise_level": "19 dB (Alig hallható prémium komfort)",
                "smart_wifi": "Beépített 5G WiFi + Hangvezérlés (Alexa, Google Assistant)",
                "annual_maintenance": "2 ÉV DÍJMENTES Teljes Karbantartás és Klímatakarítás",
                "service_response_time": "VIP 24 órás azonnali helyszíni cseregarancia hétvégén is",
                "included_extras": [
                    "Prémium rezgéscsillapított rozsdamentes acél fali konzol",
                    "5 év teljes körű prémium gyártói és kivitelezői garancia",
                    "Flash Streamer légtisztító technológia",
                    "2 év teljes körű ingyenes karbantartási csomag",
                    "VIP 24 órás szervizügyeleti hozzáférés",
                    "Díjmentes régi berendezés bontás és elszállítás"
                ],
                "pricing": {
                    "material_net": best_mat_net,
                    "labor_net": best_labor_net,
                    "total_net": best_total_net,
                    "vat_amount": best_vat,
                    "gross_total": best_gross
                }
            }
        }
        return packages

    def generate_comparison_pdf(self, quote_id: str, customer: Dict[str, Any], packages: Dict[str, Any], output_path: str) -> str:
        """
        Fekvő tájolású, 3-hasábos összehasonlító PDF táblázat generálása reportlabbal.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        doc = SimpleDocTemplate(
            output_path,
            pagesize=landscape(A4),
            rightMargin=25,
            leftMargin=25,
            topMargin=25,
            bottomMargin=25
        )
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'LandscapeTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=colors.HexColor('#1e3a8a')
        )
        sub_style = ParagraphStyle(
            'LandscapeSub',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#64748b')
        )
        cell_bold = ParagraphStyle(
            'CellBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#0f172a')
        )
        cell_normal = ParagraphStyle(
            'CellNormal',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#334155')
        )
        cell_highlight = ParagraphStyle(
            'CellHighlight',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#0284c7')
        )

        story = []
        today_str = datetime.date.today().strftime("%Y.%m.%d.")
        
        header_text = (
            f"<b>ÖSSZEHASONLÍTÓ CSOMAGAJÁNLAT – 3 SZINTŰ VÁLASZTÁSI LEHETŐSÉG</b><br/>"
            f"<font size=8 color='#64748b'>Ajánlat azonosító: {quote_id} | Ügyfél: {customer.get('name')} ({customer.get('site_address')}) | Kelt: {today_str}</font>"
        )
        story.append(Paragraph(header_text, title_style))
        story.append(Spacer(1, 10))

        g = packages["good"]
        b = packages["better"]
        v = packages["best"]

        def fmt_curr(amount):
            return f"{amount:,} Ft".replace(",", " ")

        table_data = [
            [
                Paragraph("<b>SZEMPONTOK / CSOMAGOK</b>", cell_bold),
                Paragraph(f"<b>{g['title']}</b><br/><font color='#64748b'>{g['badge']}</font>", cell_bold),
                Paragraph(f"<b>★ {b['title']} ★</b><br/><font color='#0284c7'><b>{b['badge']}</b></font>", cell_highlight),
                Paragraph(f"<b>{v['title']}</b><br/><font color='#d97706'>{v['badge']}</font>", cell_bold)
            ],
            [
                Paragraph("<b>Készülék típusa</b>", cell_bold),
                Paragraph(g['equipment'], cell_normal),
                Paragraph(f"<b>{b['equipment']}</b>", cell_highlight),
                Paragraph(f"<b>{v['equipment']}</b>", cell_normal)
            ],
            [
                Paragraph("<b>Energiaosztály</b>", cell_bold),
                Paragraph(g['energy_rating'], cell_normal),
                Paragraph(f"<b>{b['energy_rating']}</b>", cell_highlight),
                Paragraph(f"<b>{v['energy_rating']}</b>", cell_normal)
            ],
            [
                Paragraph("<b>Zajszint (Komfort)</b>", cell_bold),
                Paragraph(g['noise_level'], cell_normal),
                Paragraph(f"<b>{b['noise_level']}</b>", cell_highlight),
                Paragraph(f"<b>{v['noise_level']}</b>", cell_normal)
            ],
            [
                Paragraph("<b>Okosotthon & WiFi</b>", cell_bold),
                Paragraph(g['smart_wifi'], cell_normal),
                Paragraph(f"<b>{b['smart_wifi']}</b>", cell_highlight),
                Paragraph(f"<b>{v['smart_wifi']}</b>", cell_normal)
            ],
            [
                Paragraph("<b>Garancia időtartama</b>", cell_bold),
                Paragraph(f"{g['warranty_years']} év alaptörvényi", cell_normal),
                Paragraph(f"<b>{b['warranty_years']} év kiterjesztett</b>", cell_highlight),
                Paragraph(f"<b>{v['warranty_years']} év prémium gyártói</b>", cell_normal)
            ],
            [
                Paragraph("<b>Karbantartási kedvezmény</b>", cell_bold),
                Paragraph(g['annual_maintenance'], cell_normal),
                Paragraph(f"<b>{b['annual_maintenance']}</b>", cell_highlight),
                Paragraph(f"<b>{v['annual_maintenance']}</b>", cell_normal)
            ],
            [
                Paragraph("<b>Szerviz reakcióidő</b>", cell_bold),
                Paragraph(g['service_response_time'], cell_normal),
                Paragraph(f"<b>{b['service_response_time']}</b>", cell_highlight),
                Paragraph(f"<b>{v['service_response_time']}</b>", cell_normal)
            ],
            [
                Paragraph("<b>NETTÓ VÉGÖSSZEG</b>", cell_bold),
                Paragraph(fmt_curr(g['pricing']['total_net']), cell_bold),
                Paragraph(f"<b>{fmt_curr(b['pricing']['total_net'])}</b>", cell_highlight),
                Paragraph(fmt_curr(v['pricing']['total_net']), cell_bold)
            ],
            [
                Paragraph("<b>BRUTTÓ FIZETENDŐ</b>", cell_bold),
                Paragraph(f"<b>{fmt_curr(g['pricing']['gross_total'])}</b>", cell_bold),
                Paragraph(f"<font size=10 color='#1e3a8a'><b>{fmt_curr(b['pricing']['gross_total'])}</b></font>", cell_highlight),
                Paragraph(f"<b>{fmt_curr(v['pricing']['gross_total'])}</b>", cell_bold)
            ]
        ]

        table = Table(table_data, colWidths=[150, 210, 230, 200])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f8fafc')),
            ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#f0f9ff')), # Better oszlop kék hátterű
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('LINEAFTER', (2,0), (2,-1), 1.5, colors.HexColor('#0284c7')),
            ('LINEBEFORE', (2,0), (2,-1), 1.5, colors.HexColor('#0284c7')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#e2e8f0')),
        ]))
        story.append(table)
        story.append(Spacer(1, 10))

        order_note = (
            "<b>Online megrendelés és jóváhagyás:</b> A fenti csomagok bármelyike egyetlen kattintással megrendelhető a személyre szabott online ajánlati portálon: "
            f"<u>http://127.0.0.1:8000/api/v1/modules/07_pszichologiai_tobbszintu_ajanlatok_good_/portal?quote_id={quote_id}</u>"
        )
        story.append(Paragraph(order_note, sub_style))

        doc.build(story)
        return output_path

    def generate_interactive_html(self, quote_id: str, customer: Dict[str, Any], packages: Dict[str, Any], output_path: str) -> str:
        """
        Mobilbarát, látványos sötét/modern témájú HTML oldal a 3 csomag online kiválasztásához.
        Tartalmazza az Upsell modált a Good csomag kattintása esetén.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        g = packages["good"]
        b = packages["better"]
        v = packages["best"]

        def fmt_curr(amount):
            return f"{amount:,} Ft".replace(",", " ")

        html_content = f"""<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Személyre Szabott Ajánlati Csomagok | {quote_id}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
        body {{ background: #0f172a; color: #f8fafc; padding: 24px; }}
        .header {{ text-align: center; max-width: 800px; margin: 0 auto 32px; }}
        .header h1 {{ font-size: 28px; color: #38bdf8; margin-bottom: 8px; }}
        .header p {{ color: #94a3b8; font-size: 14px; }}
        .cards-container {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 24px; max-width: 1200px; margin: 0 auto; }}
        .card {{
            background: #1e293b; border: 1px solid #334155; border-radius: 16px; width: 340px; padding: 24px;
            display: flex; flex-direction: column; position: relative; transition: transform 0.2s, box-shadow 0.2s;
        }}
        .card:hover {{ transform: translateY(-4px); box-shadow: 0 12px 24px rgba(0,0,0,0.4); }}
        .card.highlighted {{
            border: 2px solid #38bdf8; background: linear-gradient(180deg, #1e293b 0%, #0c4a6e 100%);
            transform: scale(1.04); z-index: 2; box-shadow: 0 16px 32px rgba(56, 189, 248, 0.25);
        }}
        .ribbon {{
            position: absolute; top: -14px; left: 50%; transform: translateX(-50%);
            background: #0284c7; color: white; font-size: 11px; font-weight: bold;
            padding: 4px 16px; border-radius: 20px; letter-spacing: 0.5px;
        }}
        .tier-name {{ font-size: 18px; font-weight: bold; margin-top: 8px; margin-bottom: 6px; }}
        .tier-price {{ font-size: 26px; font-weight: 800; color: #f8fafc; margin-bottom: 4px; }}
        .tier-subprice {{ font-size: 12px; color: #94a3b8; margin-bottom: 16px; }}
        .features-list {{ list-style: none; margin-bottom: 24px; flex-grow: 1; }}
        .features-list li {{ font-size: 13px; color: #cbd5e1; margin-bottom: 10px; display: flex; align-items: flex-start; }}
        .features-list li span.icon {{ margin-right: 8px; color: #38bdf8; font-weight: bold; }}
        .btn {{
            width: 100%; padding: 12px; border-radius: 8px; border: none; font-size: 14px; font-weight: bold;
            cursor: pointer; text-align: center; text-decoration: none; transition: background 0.2s;
        }}
        .btn-default {{ background: #334155; color: white; }}
        .btn-default:hover {{ background: #475569; }}
        .btn-primary {{ background: #0284c7; color: white; }}
        .btn-primary:hover {{ background: #0369a1; }}
        .btn-gold {{ background: #d97706; color: white; }}
        .btn-gold:hover {{ background: #b45309; }}
        
        /* Modal for Good package downsell/upsell */
        #upsellModal {{
            display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.75); z-index: 100; justify-content: center; align-items: center;
        }}
        .modal-box {{
            background: #1e293b; border: 1px solid #38bdf8; border-radius: 16px; max-width: 500px;
            padding: 24px; text-align: center;
        }}
        .modal-box h2 {{ color: #38bdf8; margin-bottom: 12px; }}
        .modal-box p {{ font-size: 14px; color: #cbd5e1; margin-bottom: 20px; line-height: 1.5; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Válassza ki az Önnek legmegfelelőbb megoldást!</h1>
        <p>Ajánlatszám: <b>{quote_id}</b> | Megrendelő: <b>{customer.get('name')}</b> ({customer.get('site_address')})</p>
    </div>

    <div class="cards-container">
        <!-- 1. GOOD CARD -->
        <div class="card">
            <div class="tier-name">{g['title']}</div>
            <div class="tier-price">{fmt_curr(g['pricing']['gross_total'])}</div>
            <div class="tier-subprice">Nettó: {fmt_curr(g['pricing']['total_net'])} (+27% ÁFA)</div>
            <ul class="features-list">
                <li><span class="icon">✓</span> {g['equipment']}</li>
                <li><span class="icon">✓</span> Energiaosztály: {g['energy_rating']}</li>
                <li><span class="icon">✓</span> Zajszint: {g['noise_level']}</li>
                <li><span class="icon">✓</span> {g['warranty_years']} év törvényi garancia</li>
                <li><span class="icon">✗</span> WiFi vezérlés: {g['smart_wifi']}</li>
                <li><span class="icon">✗</span> Karbantartás: {g['annual_maintenance']}</li>
            </ul>
            <button class="btn btn-default" onclick="openUpsellModal('{quote_id}', 'good')">Kiválasztom az Alapot</button>
        </div>

        <!-- 2. BETTER CARD (HIGHLIGHTED) -->
        <div class="card highlighted">
            <div class="ribbon">★ {b['badge']} ★</div>
            <div class="tier-name" style="color: #38bdf8;">{b['title']}</div>
            <div class="tier-price">{fmt_curr(b['pricing']['gross_total'])}</div>
            <div class="tier-subprice">Nettó: {fmt_curr(b['pricing']['total_net'])} (+27% ÁFA)</div>
            <ul class="features-list">
                <li><span class="icon">✓</span> <b>{b['equipment']}</b></li>
                <li><span class="icon">✓</span> <b>Energiaosztály: {b['energy_rating']}</b></li>
                <li><span class="icon">✓</span> <b>Zajszint: {b['noise_level']}</b></li>
                <li><span class="icon">✓</span> <b>{b['warranty_years']} Év Kiterjesztett Garancia</b></li>
                <li><span class="icon">✓</span> <b>{b['smart_wifi']}</b></li>
                <li><span class="icon">✓</span> <b>{b['annual_maintenance']}</b></li>
                <li><span class="icon">✓</span> <b>{b['service_response_time']}</b></li>
            </ul>
            <a href="http://127.0.0.1:8000/api/v1/modules/07_pszichologiai_tobbszintu_ajanlatok_good_/select?quote_id={quote_id}&tier=better" class="btn btn-primary">Megrendelem a Prémium Csomagot</a>
        </div>

        <!-- 3. BEST CARD -->
        <div class="card">
            <div class="tier-name" style="color: #fbbf24;">{v['title']}</div>
            <div class="tier-price">{fmt_curr(v['pricing']['gross_total'])}</div>
            <div class="tier-subprice">Nettó: {fmt_curr(v['pricing']['total_net'])} (+27% ÁFA)</div>
            <ul class="features-list">
                <li><span class="icon">✓</span> <b>{v['equipment']}</b></li>
                <li><span class="icon">✓</span> Energiaosztály: {v['energy_rating']}</li>
                <li><span class="icon">✓</span> Zajszint: {v['noise_level']}</li>
                <li><span class="icon">✓</span> <b>{v['warranty_years']} ÉV Teljes Körű Garancia</b></li>
                <li><span class="icon">✓</span> {v['smart_wifi']}</li>
                <li><span class="icon">✓</span> <b>{v['annual_maintenance']}</b></li>
                <li><span class="icon">✓</span> <b>{v['service_response_time']}</b></li>
            </ul>
            <a href="http://127.0.0.1:8000/api/v1/modules/07_pszichologiai_tobbszintu_ajanlatok_good_/select?quote_id={quote_id}&tier=best" class="btn btn-gold">Megrendelem a VIP Csomagot</a>
        </div>
    </div>

    <!-- Upsell Modal for Option B -->
    <div id="upsellModal">
        <div class="modal-box">
            <h2>Várjon egy pillanatra!</h2>
            <p>
                Kiváló döntés az Alap csomag, de most <b>rendkívüli kedvezménnyel (+{self.upsell_addon_price_huf:,} Ft)</b>
                kérheti a készülékéhez a <b>+1 Év Extra Garanciát</b> és a <b>Szezonális Klímatisztítást</b>!
            </p>
            <div style="display: flex; gap: 12px; justify-content: center;">
                <a href="http://127.0.0.1:8000/api/v1/modules/07_pszichologiai_tobbszintu_ajanlatok_good_/select?quote_id={quote_id}&tier=good_with_upsell" class="btn btn-primary">Kérem a Kedvezményes Extrát (+{self.upsell_addon_price_huf:,} Ft)</a>
                <a href="http://127.0.0.1:8000/api/v1/modules/07_pszichologiai_tobbszintu_ajanlatok_good_/select?quote_id={quote_id}&tier=good" class="btn btn-default">Köszönöm, csak az Alap kell</a>
            </div>
        </div>
    </div>

    <script>
        function openUpsellModal(quoteId, tier) {{
            document.getElementById('upsellModal').style.display = 'flex';
        }}
    </script>
</body>
</html>
""".replace(",", " ")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return output_path

    def generate_48h_followup_message(self, quote_id: str, customer: Dict[str, Any], packages: Dict[str, Any]) -> str:
        """
        48 órás diplomatikus döntéstámogató követő üzenet (Option A) WhatsApp/SMS-re.
        """
        b = packages["better"]
        portal_link = f"http://127.0.0.1:8000/api/v1/modules/07_pszichologiai_tobbszintu_ajanlatok_good_/portal?quote_id={quote_id}"
        lines = [
            f"Kedves {customer.get('name')}!",
            f"Erdeklodom, hogy sikerult-e atneznie a {quote_id} szamu ajanlati csomagjainkat?",
            f"Ugyfeleink 78%-a a '{b['title']}' csomagot valasztja, mivel a beepitett okosvezerles es az A++ energiaosztaly mar az elso 2 evben visszahozza a minimális arkulonbozetet a villanyszamlan.",
            "",
            "A csomagok reszleteit es az 1-kattintasos megrendelest az alabbi linken eri el:",
            f"-> {portal_link}",
            "",
            "Szivesen segitek barmi kerdes eseten!"
        ]
        return chr(10).join(lines)

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        customer = payload.get("customer", {
            "name": "Tisztelt Ügyfél",
            "phone": "+36 30 000 0000",
            "email": "ugyfel@example.hu",
            "site_address": "Budapest"
        })
        project_scope = payload.get("project_scope", {})
        base_mat_net = float(project_scope.get("base_material_net", 210000))
        base_labor_net = float(project_scope.get("base_labor_net", 75000))

        today_code = datetime.date.today().strftime("%Y%m%d")
        quote_id = f"GBB-{today_code}-{abs(hash(customer.get('name', 'x')))%9000 + 1000}"

        # 1. Csomagok felépítése
        packages = self.build_packages(base_mat_net, base_labor_net)

        # 2. PDF táblázat generálás
        pdf_filename = f"good_better_best_{quote_id}.pdf"
        pdf_path = os.path.join("output", "ajanlatok", pdf_filename)
        self.generate_comparison_pdf(quote_id, customer, packages, pdf_path)

        # 3. Interaktív HTML generálás
        html_filename = f"good_better_best_{quote_id}.html"
        html_path = os.path.join("output", "ajanlatok", html_filename)
        self.generate_interactive_html(quote_id, customer, packages, html_path)

        # 4. 48h követő üzenet
        followup_msg = self.generate_48h_followup_message(quote_id, customer, packages)

        # 5. Esetleges kiválasztott csomag kezelése (ha a hívás egy kiválasztást rögzít)
        selected_pkg = payload.get("selected_package")
        upsell_applied = False
        final_selected_data = None
        if selected_pkg:
            if selected_pkg == "good_with_upsell":
                upsell_applied = True
                final_selected_data = {
                    "package": "good",
                    "upsell_addon": "Extra 1 év garancia + szezonális tisztítás",
                    "gross_total": packages["good"]["pricing"]["gross_total"] + self.upsell_addon_price_huf
                }
            elif selected_pkg in packages:
                final_selected_data = {
                    "package": selected_pkg,
                    "gross_total": packages[selected_pkg]["pricing"]["gross_total"]
                }

        portal_url = f"http://127.0.0.1:8000/api/v1/modules/07_pszichologiai_tobbszintu_ajanlatok_good_/portal?quote_id={quote_id}"

        return {
            "status": "success",
            "action_executed": "TIERED_OFFER_GENERATED",
            "quote_id": quote_id,
            "customer_name": customer.get("name"),
            "packages": {
                "good": {"gross_total": packages["good"]["pricing"]["gross_total"]},
                "better": {"gross_total": packages["better"]["pricing"]["gross_total"], "highlighted": True},
                "best": {"gross_total": packages["best"]["pricing"]["gross_total"]}
            },
            "interactive_portal_path": html_path,
            "interactive_portal_url": portal_url,
            "comparison_pdf_path": pdf_path,
            "followup_48h_scheduled": self.enable_48h_reminder,
            "followup_message_preview": followup_msg,
            "upsell_addon_price_huf": self.upsell_addon_price_huf,
            "selected_package_result": final_selected_data
        }

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    handler = GoodBetterBestHandler(config)
    return handler.execute(payload)

if __name__ == "__main__":
    test_p = {
        "customer": {"name": "Varga Mihály", "site_address": "1134 Budapest, Váci út 45."},
        "project_scope": {"base_material_net": 210000, "base_labor_net": 75000}
    }
    res = run(test_p)
    print(json.dumps(res, indent=2, ensure_ascii=False))
