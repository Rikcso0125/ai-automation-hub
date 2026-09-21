# -*- coding: utf-8 -*-
"""
Module 4.13: Webáruházi Anomália Detektálás (Kuponkód & Fizetési Kapu Figyelő)
0-24 órás e-kereskedelmi védőpajzs: SimplePay/Barion/Stripe fizetési kapu leállás figyelés,
automatikus vészhelyzeti átirányítás (Failover), elgépelt kuponkódok miatti negatív árrés
kiszűrése, Circuit Breaker vészfék és többcsatornás riasztás.
"""

import os
import json
import uuid
import datetime
from pathlib import Path
from typing import Dict, Any, List

DATA_DIR = Path(r"c:\Users\krisz\Desktop\Automatizáció\data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
ANOMALY_LOG_FILE = DATA_DIR / "webaruhazi_anomalia_naplo.json"


def _load_anomaly_logs() -> List[Dict[str, Any]]:
    if ANOMALY_LOG_FILE.exists():
        try:
            with open(ANOMALY_LOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def _save_anomaly_log_entry(entry: Dict[str, Any]) -> None:
    logs = _load_anomaly_logs()
    logs.append(entry)
    with open(ANOMALY_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


def evaluate_gateway_health(
    gateway_data: Dict[str, Any],
    consecutive_threshold: int,
    mode: str
) -> Dict[str, Any]:
    """
    1. Kérdés: Fizetési Kapu Hibaérzékelés & Failover
    """
    consecutive_fails = int(gateway_data.get("consecutive_failures", 0))
    hourly_rate = float(gateway_data.get("hourly_success_rate_pct", 100.0))
    baseline_rate = float(gateway_data.get("baseline_success_rate_pct", 98.0))
    gateway_name = gateway_data.get("primary_gateway", "Fizetési kapu")
    last_error = gateway_data.get("last_error_code", "N/A")

    failover_required = False
    anomalies = []

    # Hibaszám-küszöb ellenőrzés
    if consecutive_fails >= consecutive_threshold:
        failover_required = True
        anomalies.append(
            f"Kritikus kapuhalmozódás: {consecutive_fails} egymást követő tranzakció meghiúsult ({last_error})."
        )

    # Statisztikai zuhanás ellenőrzés
    if hourly_rate < 90.0:
        anomalies.append(
            f"Órás sikerességi ráta visszaesés: {hourly_rate:.1f}% (normál: {baseline_rate:.1f}%)."
        )
        if hourly_rate < 80.0:
            failover_required = True

    if failover_required:
        status = "CRITICAL_GATEWAY_OUTAGE"
        failover_action = {
            "active": True,
            "fallback_payment_methods": [
                {
                    "method": "CASH_ON_DELIVERY",
                    "title": "Utánvétes fizetés átvételkor (Futár / Csomagpont)",
                    "priority": 1,
                    "active_in_checkout": True
                },
                {
                    "method": "INSTANT_BANK_TRANSFER",
                    "title": "Azonnali Banki Átutalás (AFR 5 mp)",
                    "priority": 2,
                    "active_in_checkout": True
                }
            ],
            "customer_notice": (
                f"Tájékoztatjuk, hogy a(z) {gateway_name} banki szolgáltatónál átmeneti hiba tapasztalható. "
                f"Rendelését zökkenőmentesen leadhatja utánvéttel vagy azonnali banki átutalással!"
            )
        }
    else:
        status = "GATEWAY_HEALTHY"
        failover_action = {"active": False}

    return {
        "status": status,
        "primary_gateway": gateway_name,
        "consecutive_failures": consecutive_fails,
        "hourly_success_rate_pct": hourly_rate,
        "failover_required": failover_required,
        "failover_plan": failover_action,
        "anomalies": anomalies
    }


def evaluate_coupon_and_margin(
    order_context: Dict[str, Any],
    max_discount_pct: int,
    mode: str
) -> Dict[str, Any]:
    """
    2. Kérdés: Kuponkód & Árrésvédelmi Circuit Breaker
    """
    regular_price = float(order_context.get("regular_retail_price_huf", 0))
    wholesale_cost = float(order_context.get("wholesale_cost_price_huf", 0))
    discounted_price = float(order_context.get("discounted_checkout_price_huf", regular_price))
    coupon_code = order_context.get("applied_coupon_code", "N/A")
    discount_pct = float(order_context.get("coupon_discount_percent", 0))

    # Tényleges árrés forintban
    net_margin = discounted_price - wholesale_cost
    margin_percent = (net_margin / regular_price * 100.0) if regular_price > 0 else 0.0

    is_negative_margin = net_margin < 0
    is_excessive_discount = discount_pct > max_discount_pct

    anomalies = []
    circuit_breaker_tripped = False

    if is_negative_margin:
        circuit_breaker_tripped = True
        anomalies.append(
            f"Veszteséges eladás detektálva! A fizetendő ár ({int(discounted_price):,} Ft) alacsonyabb a "
            f"beszerzési önköltségnél ({int(wholesale_cost):,} Ft). Ráfizetés rendelésenként: {int(abs(net_margin)):,} Ft!"
        )

    if is_excessive_discount:
        circuit_breaker_tripped = True
        anomalies.append(
            f"Túlzó engedmény ({discount_pct:.0f}% > {max_discount_pct}% plafon). Valószínűsíthető elgépelés vagy adminhiba a kuponbeállításban!"
        )

    return {
        "circuit_breaker_tripped": circuit_breaker_tripped,
        "coupon_code": coupon_code,
        "discount_percent": discount_pct,
        "regular_price_huf": int(regular_price),
        "wholesale_cost_huf": int(wholesale_cost),
        "discounted_checkout_huf": int(discounted_price),
        "net_margin_huf": int(net_margin),
        "margin_percent": round(margin_percent, 1),
        "is_negative_margin": is_negative_margin,
        "is_excessive_discount": is_excessive_discount,
        "anomalies": anomalies
    }


def execute_intervention(
    intervention_level: str,
    gateway_eval: Dict[str, Any],
    coupon_eval: Dict[str, Any],
    order_context: Dict[str, Any],
    loss_threshold_huf: int
) -> Dict[str, Any]:
    """
    3. Kérdés: Beavatkozási Hatáskör & Vészleállítás
    """
    coupon_code = coupon_eval.get("coupon_code")
    net_margin = coupon_eval.get("net_margin_huf", 0)
    deficit = abs(net_margin) if net_margin < 0 else 0

    order_id = order_context.get("order_temp_id", "ORD-UNKNOWN")
    review_url = f"https://admin.webshop.hu/security/anomalies/{order_id}/review"

    # Ha nincs sem kapuhiba, sem kupon probléma
    has_anomaly = gateway_eval.get("failover_required") or coupon_eval.get("circuit_breaker_tripped")
    if not has_anomaly:
        return {
            "coupon_system_action": "NONE_HEALTHY",
            "order_handling_action": "ORDER_PROCESSED_SUCCESSFULLY",
            "requires_human_approval": False,
            "emergency_review_url": None,
            "action_summary": "Nincs anomália, a tranzakció zökkenőmentesen és biztonságosan végrehajtható."
        }

    # Döntési fa anomália esetén
    if intervention_level == "fully_autonomous_lockdown":
        coupon_action = f"COUPON_INSTANTLY_DISABLED_VIA_API ({coupon_code})"
        order_action = "TRANSACTION_REJECTED_MARGIN_DEFICIT"
        requires_approval = False
        summary = (
            f"Teljes autonóm vészleállítás: A(z) '{coupon_code}' kupon azonnal inaktiválva a webshop motorban. "
            f"A rendelés leadása elutasítva, azonnali vészhívás kiküldve a tulajdonosnak."
        )

    elif intervention_level == "hitl_operator_review":
        coupon_action = f"COUPON_FLAGGED_WARNING ({coupon_code})"
        order_action = "ORDER_HELD_FOR_REVIEW"
        requires_approval = True
        summary = (
            f"A rendelés ({order_id}) feladás előtti ellenőrzésre zárolva. "
            f"1-kattintásos vezetői döntési link kiküldve a vezérlőpultra."
        )

    else:
        # hybrid_loss_threshold_action: veszteségmérték alapján
        if deficit >= loss_threshold_huf:
            coupon_action = f"COUPON_DISABLED_AUTO ({coupon_code})"
            order_action = "CIRCUIT_BREAKER_HARD_LOCKDOWN"
            requires_approval = True
            summary = (
                f"Azonnali Circuit Breaker vészfék! A veszteség ({deficit:,} Ft) meghaladja a limitet ({loss_threshold_huf:,} Ft). "
                f"A kupon zárolva, a rendelés felfüggesztve, 1-kattintásos vezetői döntés szükséges."
            )
        else:
            coupon_action = f"COUPON_TEMPORARILY_DISABLED ({coupon_code})"
            order_action = "ORDER_HELD_FOR_SUPERVISOR_CONFIRMATION"
            requires_approval = True
            summary = (
                f"Kupon zárolva az újabb visszaélések megelőzésére. A meglévő rendelés ({order_id}) "
                f"méltányossági felülvizsgálatra átadva a boltvezetőnek."
            )

    return {
        "coupon_system_action": coupon_action,
        "order_handling_action": order_action,
        "requires_human_approval": requires_approval,
        "emergency_review_url": review_url,
        "action_summary": summary
    }


def run(payload: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Fő végrehajtó függvény
    """
    event_id = payload.get("event_id") or f"ANOM-{uuid.uuid4().hex[:8].upper()}"
    store_name = payload.get("store_name", "Webáruház")
    order_context = payload.get("cart_order_context", {})
    gateway_data = payload.get("payment_gateway_health", {})
    traffic_data = payload.get("traffic_health", {})

    cfg = dict(config or {})
    if payload.get("config"):
        cfg.update(payload.get("config", {}))

    # Konfigurációs paraméterek
    gw_mode = cfg.get("gateway_monitoring_mode", "hybrid_gateway_guard")
    consecutive_thresh = int(cfg.get("consecutive_payment_failures_threshold", 3))
    coupon_mode = cfg.get("coupon_guard_mode", "hybrid_coupon_protection")
    max_discount_pct = int(cfg.get("max_allowed_discount_percent", 40))
    loss_thresh = int(cfg.get("loss_threshold_huf_for_auto_pause", 20000))
    intervention_level = cfg.get("intervention_level", "hybrid_loss_threshold_action")

    # 1. Lépés: Fizetési Kapu Egészség és Failover Értékelés
    gateway_eval = evaluate_gateway_health(gateway_data, consecutive_thresh, gw_mode)

    # 2. Lépés: Kupon és Árrésvédelmi Circuit Breaker Értékelés
    coupon_eval = evaluate_coupon_and_margin(order_context, max_discount_pct, coupon_mode)

    # 3. Lépés: Beavatkozás és Védelem
    intervention = execute_intervention(
        intervention_level,
        gateway_eval,
        coupon_eval,
        order_context,
        loss_thresh
    )

    # 4. Lépés: Vészjelző Riasztás összeállítása
    alert_lines = [f"🚨 [WEBÁRUHÁZ VÉSZHELYZETI ANOMÁLIA] - {store_name}"]
    if gateway_eval["failover_required"]:
        alert_lines.append(f"• FIZETÉSI KAPU HIBA: {gateway_eval['primary_gateway']} leállt ({gateway_eval['consecutive_failures']} egymást követő hiba). Failover utánvétes fizetés aktiválva!")
    if coupon_eval["circuit_breaker_tripped"]:
        alert_lines.append(f"• KUPON ANOMÁLIA: '{coupon_eval['coupon_code']}' (-{coupon_eval['discount_percent']}%). Veszteség: {coupon_eval['net_margin_huf']} Ft/db!")
    alert_lines.append(f"• BEAVATKOZÁS: {intervention['action_summary']}")
    alert_lines.append(f"👉 DÖNTÉSI MŰSZERFAL: {intervention['emergency_review_url']}")

    alert_message = "\n".join(alert_lines)

    # 5. Lépés: Audit naplózás
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "event_id": event_id,
        "store_name": store_name,
        "gateway_status": gateway_eval["status"],
        "coupon_circuit_breaker": coupon_eval["circuit_breaker_tripped"],
        "intervention": intervention,
        "status": "ANOMALY_HANDLED"
    }
    _save_anomaly_log_entry(log_entry)

    overall_status = "CRITICAL_ANOMALY_TRIGGERED" if (gateway_eval["failover_required"] or coupon_eval["circuit_breaker_tripped"]) else "NORMAL"

    return {
        "status": "success",
        "event_id": event_id,
        "overall_health": overall_status,
        "payment_gateway_monitoring": gateway_eval,
        "coupon_and_margin_protection": coupon_eval,
        "emergency_intervention": intervention,
        "emergency_alert": {
            "channel": cfg.get("notification_channel", "telegram_sms"),
            "message": alert_message
        },
        "summary": (
            f"Anomália kivizsgálás kész ({overall_status}). "
            f"Fizetési kapu: {gateway_eval['status']} (Failover: {gateway_eval['failover_required']}). "
            f"Kupon árrésvédelem: Circuit Breaker lecsapott: {coupon_eval['circuit_breaker_tripped']}. "
            f"Beavatkozás: {intervention['order_handling_action']}."
        )
    }
