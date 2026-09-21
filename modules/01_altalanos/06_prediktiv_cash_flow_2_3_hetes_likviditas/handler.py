# -*- coding: utf-8 -*-
import datetime
from typing import Dict, Any, List

def run(payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    current_balance = float(payload.get("current_bank_balance", 2000000))
    current_date_str = payload.get("current_date", "2026-09-20")
    try:
        start_date = datetime.datetime.strptime(current_date_str, "%Y-%m-%d").date()
    except Exception:
        start_date = datetime.date.today()

    receivables = payload.get("open_receivables", [])
    payables = payload.get("open_payables", [])

    safety_buffer = float(config.get("safety_buffer_huf", 1000000))
    default_delay = int(config.get("default_late_payment_adjustment_days", 6))
    forecast_days = int(config.get("forecast_days", 21))
    salaries = float(config.get("fixed_monthly_salaries_huf", 2800000))
    salary_day = int(config.get("salary_due_day", 10))
    taxes = float(config.get("fixed_monthly_taxes_huf", 1200000))
    tax_day = int(config.get("tax_due_day", 12))
    vat = float(config.get("estimated_vat_huf", 950000))
    vat_day = int(config.get("vat_due_day", 20))
    company_name = config.get("company_name", "Cégünk Kft.")

    # 1. Korrigált bevételek feltérképezése
    adjusted_inflows = []
    for r in receivables:
        due_str = r.get("due_date", current_date_str)
        try:
            d_date = datetime.datetime.strptime(due_str, "%Y-%m-%d").date()
        except Exception:
            d_date = start_date
        delay = int(r.get("historical_delay_days", default_delay))
        proj_date = d_date + datetime.timedelta(days=delay)
        adjusted_inflows.append({
            "partner": r.get("customer_name"),
            "amount": float(r.get("gross_amount", 0)),
            "orig_due": due_str,
            "proj_date": proj_date,
            "delay_applied": delay
        })

    # 2. Kiadások összegyűjtése
    all_outflows = []
    for p in payables:
        due_str = p.get("due_date", current_date_str)
        try:
            d_date = datetime.datetime.strptime(due_str, "%Y-%m-%d").date()
        except Exception:
            d_date = start_date
        all_outflows.append({
            "title": f"Beszállító: {p.get('supplier_name')}",
            "amount": float(p.get("gross_amount", 0)),
            "date": d_date
        })

    # 3. Napi szimuláció
    daily_projection = []
    running_balance = current_balance
    lowest_balance = current_balance
    lowest_date = start_date
    dip_detected = False
    dip_details = []

    for day_offset in range(forecast_days):
        cur_day = start_date + datetime.timedelta(days=day_offset)
        day_inflow = 0.0
        day_outflow = 0.0
        notes = []

        # Fix költségek beillesztése a hónap napja szerint
        if cur_day.day == salary_day:
            day_outflow += salaries
            notes.append(f"Havi bérfizetés: -{salaries:,.0f} Ft")
        if cur_day.day == tax_day:
            day_outflow += taxes
            notes.append(f"Bérjárulékok NAV: -{taxes:,.0f} Ft")
        if cur_day.day == vat_day:
            day_outflow += vat
            notes.append(f"Havi ÁFA befizetés: -{vat:,.0f} Ft")

        # Beszállítói kiadások
        for o in all_outflows:
            if o["date"] == cur_day:
                day_outflow += o["amount"]
                notes.append(f"{o['title']}: -{o['amount']:,.0f} Ft")

        # Korrigált vevői befolyások
        for inf in adjusted_inflows:
            if inf["proj_date"] == cur_day:
                day_inflow += inf["amount"]
                notes.append(f"Várható befolyás: {inf['partner']} (+{inf['amount']:,.0f} Ft)")

        opening = running_balance
        running_balance = running_balance + day_inflow - day_outflow

        is_under_buffer = (running_balance < safety_buffer)
        if is_under_buffer:
            dip_detected = True
            dip_details.append({
                "date": cur_day.isoformat(),
                "balance": running_balance,
                "deficit_from_buffer": safety_buffer - running_balance
            })

        if running_balance < lowest_balance:
            lowest_balance = running_balance
            lowest_date = cur_day

        daily_projection.append({
            "date": cur_day.isoformat(),
            "opening_balance": opening,
            "inflows": day_inflow,
            "outflows": day_outflow,
            "closing_balance": running_balance,
            "status": "DANGER" if running_balance < 0 else ("WARNING" if is_under_buffer else "HEALTHY"),
            "events": notes
        })

    # 4. AI Akcióterv készítése hullámvölgy esetén
    action_plan = []
    if dip_detected:
        shortfall = safety_buffer - lowest_balance
        action_plan.append(f"Azonnali likviditási hiány a mélyponton ({lowest_date}): {shortfall:,.0f} Ft a biztonsági tartalékhoz képest.")
        action_plan.append("1. LÉPÉS: Gyorsítsd fel a legnagyobb késedelmes vevők behajtását a 'kintlevoseg_40eur' modullal!")
        action_plan.append("2. LÉPÉS: Kérj 10 napos fizetési halasztást az Alkatrész Nagyker Kft-től (1.350.000 Ft).")
        action_plan.append(f"3. LÉPÉS: Ha nem befolyásolható a csúszás, aktiválj {shortfall:,.0f} Ft keretösszegű folyószámlahitelt a kritikus nap előtt 3 nappal.")

    # 5. Vezetői jelentés szövegezése
    report_title = f"[CASH-FLOW RIASZTAS] Likviditasi hullamvolgy varhato: {lowest_date}" if dip_detected else "[CASH-FLOW JELENTES] Penzugyi egyenleg stabil a kovetkezo 3 hetben"

    return {
        "status": "warning" if dip_detected else "healthy",
        "current_balance_huf": current_balance,
        "safety_buffer_huf": safety_buffer,
        "forecast_period_days": forecast_days,
        "lowest_projected_balance": {
            "amount_huf": lowest_balance,
            "date": lowest_date.isoformat(),
            "is_critical_under_buffer": dip_detected
        },
        "dip_warning_triggered": dip_detected,
        "recommended_action_plan": action_plan if dip_detected else ["A likviditási egyenleg folyamatosan a biztonsági sáv felett marad, nincs szükség beavatkozásra."],
        "weekly_executive_report": {
            "title": report_title,
            "summary": f"A(z) {company_name} 21 napos cash-flow szimulációja elkészült. A legalacsonyabb várható egyenleg: {lowest_balance:,.0f} Ft ({lowest_date}).",
            "send_to_email": config.get("executive_email", "vezeto@ceg.hu")
        },
        "daily_projection_summary": daily_projection[:7]  # Első 7 nap előnézete
    }

async def run_async(payload: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    return run(payload, config)
