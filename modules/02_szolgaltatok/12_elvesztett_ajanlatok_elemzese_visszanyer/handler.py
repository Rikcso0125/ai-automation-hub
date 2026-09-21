"""
Elvesztett Ajánlatok Elemzése & Visszanyerése (Win/Loss)
Modul: 12_elvesztett_ajanlatok_elemzese_visszanyer
"""

import os
import sys
import json
import datetime
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class WinLossWinBackHandler:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.approval_gate_mode = self.config.get("approval_gate_mode", "review_required")
        wb_custom = self.config.get("win_back_customization", {})
        self.price_reduction_pct = float(wb_custom.get("price_reduction_percent", 15.0))
        self.re_engagement_delay_days = int(wb_custom.get("re_engagement_delay_days", 45))
        self.allow_installment = wb_custom.get("allow_installment_option", True)
        self.analytics_file = "data/win_loss_statisztika.json"

    def analyze_loss_reason(self, reason_raw: str) -> Dict[str, Any]:
        """
        Besorolja és normalizálja a veszteségi okot.
        """
        r = reason_raw.lower()
        if "ár" in r or "price" in r or "drága" in r or "budget" in r or "keret" in r:
            category = "PRICE_BUDGET"
            title = "Ár és Költségvetési Szűkösség"
            action_type = "SLIM_COUNTER_OFFER"
        elif "idő" in r or "timing" in r or "később" in r or "nem aktuális" in r:
            category = "TIMING_POSTPONED"
            title = "Időzítés / Elhalasztott Beruházás"
            action_type = "SCHEDULED_RE_ENGAGEMENT"
        elif "másik" in r or "konkurencia" in r or "versenytárs" in r:
            category = "COMPETITOR_CHOSEN"
            title = "Konkurens Cég Kiválasztása"
            action_type = "SAFETY_NET_LETTER"
        else:
            category = "TECHNICAL_SCOPE"
            title = "Műszaki Tartalom / Igényeltérés"
            action_type = "RESCOPE_CONSULTATION"

        return {
            "category": category,
            "title": title,
            "action_type": action_type
        }

    def generate_win_back_package(self, deal: Dict[str, Any], customer: Dict[str, Any], reason_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Kidolgozza a személyre szabott visszanyerési ellenajánlatot.
        """
        orig_gross = deal.get("original_gross_huf", 890000)
        c_name = customer.get("name", "Ügyfelünk")
        cat = reason_data["category"]

        if cat == "PRICE_BUDGET":
            # Karcsúsított csomag
            discount_amount = round(orig_gross * (self.price_reduction_pct / 100.0))
            slimmed_gross = orig_gross - discount_amount
            slimmed_net = round(slimmed_gross / 1.27)
            vat_amount = slimmed_gross - slimmed_net

            installment_text = (
                f"vagy 3 x {round(slimmed_gross / 3):,} Ft kamatmentes havi részletfizetéssel"
            ).replace(",", " ")

            proposal = {
                "type": "SLIMMED_COUNTER_OFFER",
                "title": f"Karcsúsított Költségkímélő Alternatíva (-{int(self.price_reduction_pct)}%)",
                "original_gross": orig_gross,
                "discount_percent": self.price_reduction_pct,
                "discount_amount": discount_amount,
                "slimmed_gross": slimmed_gross,
                "installment_option": installment_text,
                "modifications": [
                    "A prémium dizájn helyett megbízható standard berendezés (ugyanazzal a minőségi szereléssel)",
                    "Alap kábelcsatornás nyomvonal (falvésés helyett)",
                    "3 év teljes körű hivatalos számlás garancia és beüzemelési jegyzőkönyv megőrizve"
                ],
                "message_pitch": (
                    f"Kedves {c_name}! Megértjük a szűkebb költségvetési keretet. "
                    f"Összeállítottunk egy karcsúsított műszaki alternatívát, amivel bruttó {slimmed_gross:,} Ft-ból "
                    f"({installment_text}) megvalósítható a beruházás a biztonságos 3 év garanciával. Átnézzük a részleteket?"
                ).replace(",", " ")
            }
        elif cat == "TIMING_POSTPONED":
            re_date = (datetime.date.today() + datetime.timedelta(days=self.re_engagement_delay_days)).strftime("%Y.%m.%d.")
            proposal = {
                "type": "RE_ENGAGEMENT_SCHEDULED",
                "title": f"Időzített Visszakövetés ({self.re_engagement_delay_days} nap)",
                "scheduled_date": re_date,
                "modifications": ["Ajánlat érvényességének meghosszabbítása a szezon kezdetéig"],
                "message_pitch": (
                    f"Kedves {c_name}! Teljesen megértjük, hogy most nem időszerű a beruházás. "
                    f"Bejegyeztük rendszerünkbe az ajánlat fenntartását {re_date}-ig. Ha a szezon előtt kérdése van, állunk rendelkezésre!"
                )
            }
        else:
            proposal = {
                "type": "SAFETY_NET_LETTER",
                "title": "Biztonsági Háló Levél & Későbbi Szervizkapu",
                "modifications": ["Ajtó nyitvatartása ha a választott kivitelezővel probléma merülne fel"],
                "message_pitch": (
                    f"Kedves {c_name}! Köszönjük a visszajelzést. Sok sikert kívánunk a kivitelezéshez! "
                    f"Ha a jövőben karbantartásra vagy szakszerű felülvizsgálatra lenne szüksége, szakértő csapatunk örömmel áll rendelkezésére."
                )
            }

        return proposal

    def generate_pdf_counter_offer(self, deal_id: str, customer: Dict[str, Any], deal: Dict[str, Any], proposal: Dict[str, Any], output_path: str) -> str:
        """
        reportlab alapú márkázott Karcsúsított Visszanyerő PDF Ajánlat.
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
            'WbTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=colors.HexColor('#1e3a8a')
        )
        sub_style = ParagraphStyle(
            'WbSub',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=12
        )
        h2_style = ParagraphStyle(
            'WbH2',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=15,
            textColor=colors.HexColor('#0f172a'),
            spaceBefore=8,
            spaceAfter=4
        )
        normal_style = ParagraphStyle(
            'WbNormal',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#334155')
        )
        bold_style = ParagraphStyle(
            'WbBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#0f172a')
        )

        story = []

        # Fejléc
        story.append(Paragraph("<b>KARCSÚSÍTOTT VISSZANYERŐ ELLENAJÁNLAT (WIN-BACK)</b>", title_style))
        story.append(Paragraph(f"Eredeti ajánlatszám: <b>{deal.get('quote_id')}</b> | Ügyfél: {customer.get('name')} ({customer.get('company')})", sub_style))

        # Árösszehasonlító táblázat (ha árengedményes)
        if proposal["type"] == "SLIMMED_COUNTER_OFFER":
            def fmt(a):
                return f"{a:,} Ft".replace(",", " ")

            price_rows = [
                ["Ajánlati tétel", "Eredeti kalkuláció", "Karcsúsított Win-Back ár", "Megtakarítás"],
                [
                    Paragraph(f"<b>{deal.get('service_name')}</b>", normal_style),
                    Paragraph(f"<strike>{fmt(proposal['original_gross'])}</strike>", normal_style),
                    Paragraph(f"<font color='#0284c7'><b>{fmt(proposal['slimmed_gross'])}</b></font>", bold_style),
                    Paragraph(f"<b>-{proposal['discount_percent']}% ({fmt(proposal['discount_amount'])})</b>", bold_style)
                ]
            ]
            price_table = Table(price_rows, colWidths=[200, 110, 110, 100])
            price_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white]),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('ALIGN', (1,0), (-1,-1), 'RIGHT')
            ]))
            story.append(price_table)
            story.append(Spacer(1, 10))

            # Módosítások
            story.append(Paragraph("<b>HOGYAN CSÖKKENTETTÜK AZ ÁRAT A MINŐSÉG ÉS GARANCIA MEGTARTÁSÁVAL?</b>", h2_style))
            for m in proposal.get("modifications", []):
                story.append(Paragraph(f"✓ {m}", normal_style))
                story.append(Spacer(1, 3))
            story.append(Spacer(1, 8))

            # Részletfizetési opció doboz
            opt_box = [[Paragraph(f"<b>Részletfizetési Kedvezmény:</b> Az ellenajánlat igénybe vehető kamatmentes 3 havi részletekben is: <b>{proposal.get('installment_option')}</b>.", normal_style)]]
            opt_table = Table(opt_box, colWidths=[520])
            opt_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0f9ff')),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#0284c7')),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(opt_table)
        else:
            story.append(Paragraph(f"<b>Stratégia:</b> {proposal['title']}", h2_style))
            story.append(Paragraph(proposal["message_pitch"], normal_style))

        doc.build(story)
        return output_path

    def update_analytics_log(self, deal: Dict[str, Any], reason_data: Dict[str, Any], winback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Frissíti a központi Win/Loss statisztikát a Dashboard számára.
        """
        stats = {
            "total_lost_deals": 0,
            "lost_by_category": {
                "PRICE_BUDGET": 0,
                "TIMING_POSTPONED": 0,
                "COMPETITOR_CHOSEN": 0,
                "TECHNICAL_SCOPE": 0
            },
            "winback_offers_generated": 0,
            "potential_recovered_revenue_huf": 0,
            "recent_events": []
        }

        if os.path.exists(self.analytics_file):
            try:
                with open(self.analytics_file, "r", encoding="utf-8") as f:
                    stats = json.load(f)
            except Exception:
                pass

        stats["total_lost_deals"] += 1
        cat = reason_data.get("category", "PRICE_BUDGET")
        stats["lost_by_category"][cat] = stats["lost_by_category"].get(cat, 0) + 1

        if winback.get("type") == "SLIMMED_COUNTER_OFFER":
            stats["winback_offers_generated"] += 1
            stats["potential_recovered_revenue_huf"] += winback.get("slimmed_gross", 0)

        event = {
            "quote_id": deal.get("quote_id"),
            "timestamp": datetime.datetime.now().isoformat(),
            "category": cat,
            "reason_title": reason_data.get("title"),
            "deal_value": deal.get("original_gross_huf", 0),
            "winback_type": winback.get("type")
        }
        stats["recent_events"].insert(0, event)
        stats["recent_events"] = stats["recent_events"][:50]

        with open(self.analytics_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        return stats

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        deal = payload.get("deal", {
            "quote_id": f"AJ-{datetime.date.today().strftime('%Y%m%d')}-LOST",
            "service_name": "Klímaszerelés",
            "original_gross_huf": 890000
        })
        customer = payload.get("customer", {"name": "Ügyfél", "company": "Cég"})
        feedback = payload.get("loss_feedback", {
            "primary_reason": "price_budget",
            "customer_comment": "Drága"
        })
        sales_rep = payload.get("sales_rep", {"name": "Értékesítő", "phone": "+36 30 111 2233"})

        # 1. Ok elemzése
        reason_data = self.analyze_loss_reason(feedback.get("primary_reason", "") + " " + feedback.get("customer_comment", ""))

        # 2. Visszanyerő ajánlat / csomag összeállítása
        winback = self.generate_win_back_package(deal, customer, reason_data)

        # 3. PDF generálás
        deal_id = deal.get("quote_id", "DEAL-001")
        pdf_path = os.path.join("output", "visszanyeres", f"ellenajanlat_{deal_id}.pdf")
        self.generate_pdf_counter_offer(deal_id, customer, deal, winback, pdf_path)

        # 4. Statisztika frissítése
        stats = self.update_analytics_log(deal, reason_data, winback)

        # 5. Option A: Vezetői / Értékesítői jóváhagyási link
        approve_link = f"http://127.0.0.1:8000/api/v1/modules/12_elvesztett_ajanlatok_elemzese_visszanyer/approve?deal_id={deal_id}"

        alert_to_rep = chr(10).join([
            f"[WIN-BACK COPILOT] Karcsusitott visszanyero ellenajanlat kesz!",
            f"Ugyfel: {customer.get('name')} ({customer.get('company')})",
            f"Veszteseg oka: {reason_data['title']}",
            f"Eredeti ar: {deal.get('original_gross_huf', 0):,} Ft -> Uj ar: {winback.get('slimmed_gross', 0):,} Ft".replace(",", " "),
            f"PDF ellenajanlat: {pdf_path}",
            "",
            "1-KATTINTASOS JOVAHAGYAS & KIKULDES AZ UGYFELNEK:",
            f"-> {approve_link}"
        ])

        return {
            "status": "success",
            "action_executed": "WIN_LOSS_ANALYZED_AND_WINBACK_GENERATED",
            "quote_id": deal_id,
            "customer_name": customer.get("name"),
            "loss_reason_category": reason_data["category"],
            "loss_reason_title": reason_data["title"],
            "win_back_strategy": winback.get("type"),
            "counter_offer_gross_huf": winback.get("slimmed_gross"),
            "counter_offer_pdf_path": pdf_path,
            "approval_gate": "review_required",
            "one_click_approval_link": approve_link,
            "dashboard_analytics_summary": {
                "total_lost": stats["total_lost_deals"],
                "lost_by_price": stats["lost_by_category"].get("PRICE_BUDGET", 0),
                "lost_by_timing": stats["lost_by_category"].get("TIMING_POSTPONED", 0),
                "potential_recovered_revenue_huf": stats["potential_recovered_revenue_huf"]
            },
            "rep_notification_message": alert_to_rep
        }

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    handler = WinLossWinBackHandler(config)
    return handler.execute(payload)

if __name__ == "__main__":
    test_p = {
        "deal": {"quote_id": "AJ-TEST-01", "original_gross_huf": 890000},
        "customer": {"name": "Bartha Gábor", "company": "Bartha Kft."},
        "loss_feedback": {"primary_reason": "price", "customer_comment": "Drága az ajánlat"}
    }
    res = run(test_p)
    print(json.dumps(res, indent=2, ensure_ascii=False))
