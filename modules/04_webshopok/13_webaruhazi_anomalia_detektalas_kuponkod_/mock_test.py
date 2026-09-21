# -*- coding: utf-8 -*-
"""
Mock teszt a Webaruhazi Anomalia Detektalas modulhoz.
3 uzleti forgatokonyv tesztelese:
1. Kritikus kettos anomalia (SimplePay 3 hiba + Elgepelt 50%-os veszteseges kupon)
2. Csak fizetesi kapu leallas (egeszseges kosar, de kapu elakadas -> Failover aktiv)
3. Egeszseges tranzakcio (98%-os kapu, ervenyes 10%-os kupon pozitiv arressel)
"""

import sys
import os
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from handler import run


def test_scenario_1_double_critical_anomaly():
    print("\n--- TESZT 1: Kettos anomalia (SimplePay kapuhalmozas + Negativ arres kupon) ---")
    payload = {
        "event_id": "ANOM-TEST-001",
        "store_name": "ProfiSzerszam Webshop",
        "cart_order_context": {
            "order_temp_id": "ORD-TMP-99410",
            "item_sku": "BOSCH-GBH-2-28",
            "item_name": "Bosch GBH 2-28 Furokalapacs",
            "regular_retail_price_huf": 68900,
            "wholesale_cost_price_huf": 48500,
            "applied_coupon_code": "SUPERVIP50",
            "coupon_discount_percent": 50,
            "discounted_checkout_price_huf": 34450
        },
        "payment_gateway_health": {
            "primary_gateway": "SimplePay OTP",
            "consecutive_failures": 3,
            "hourly_success_rate_pct": 82.5,
            "last_error_code": "HTTP_504_TIMEOUT"
        },
        "config": {
            "gateway_monitoring_mode": "hybrid_gateway_guard",
            "consecutive_payment_failures_threshold": 3,
            "max_allowed_discount_percent": 40,
            "intervention_level": "hybrid_loss_threshold_action",
            "loss_threshold_huf_for_auto_pause": 20000
        }
    }
    
    res = run(payload)
    print(f"Status: {res.get('status')}")
    print(f"Osszesitett egeszseg: {res.get('overall_health')}")
    print(f"Kapu Failover szukseges: {res.get('payment_gateway_monitoring', {}).get('failover_required')}")
    print(f"Kupon Circuit Breaker lecsapott: {res.get('coupon_and_margin_protection', {}).get('circuit_breaker_tripped')}")
    print(f"Netto arres / darab: {res.get('coupon_and_margin_protection', {}).get('net_margin_huf')} Ft")
    print(f"Beavatkozas: {res.get('emergency_intervention', {}).get('order_handling_action')}")
    print(f"Kupon kezelese: {res.get('emergency_intervention', {}).get('coupon_system_action')}")
    print(f"Veszhelyzeti link: {res.get('emergency_intervention', {}).get('emergency_review_url')}")
    
    assert res.get("status") == "success"
    assert res.get("overall_health") == "CRITICAL_ANOMALY_TRIGGERED"
    assert res.get("payment_gateway_monitoring", {}).get("failover_required") is True
    assert res.get("coupon_and_margin_protection", {}).get("circuit_breaker_tripped") is True
    assert res.get("coupon_and_margin_protection", {}).get("net_margin_huf") == -14050
    print("[OK] Teszt 1 sikeresen lefutott!")


def test_scenario_2_gateway_failover_only():
    print("\n--- TESZT 2: Csak fizetesi kapu leallas (Failover utanvetre) ---")
    payload = {
        "event_id": "ANOM-TEST-002",
        "store_name": "ProfiSzerszam Webshop",
        "cart_order_context": {
            "order_temp_id": "ORD-TMP-99411",
            "regular_retail_price_huf": 45000,
            "wholesale_cost_price_huf": 30000,
            "applied_coupon_code": "NORMAL10",
            "coupon_discount_percent": 10,
            "discounted_checkout_price_huf": 40500
        },
        "payment_gateway_health": {
            "primary_gateway": "Barion Smart Gateway",
            "consecutive_failures": 4,
            "hourly_success_rate_pct": 74.0,
            "last_error_code": "INTERNAL_SERVER_ERROR"
        },
        "config": {
            "consecutive_payment_failures_threshold": 3
        }
    }
    
    res = run(payload)
    print(f"Kapu statusz: {res.get('payment_gateway_monitoring', {}).get('status')}")
    print(f"Failover terv aktiv: {res.get('payment_gateway_monitoring', {}).get('failover_plan', {}).get('active')}")
    print(f"Kupon Circuit Breaker: {res.get('coupon_and_margin_protection', {}).get('circuit_breaker_tripped')}")
    
    assert res.get("status") == "success"
    assert res.get("payment_gateway_monitoring", {}).get("failover_plan", {}).get("active") is True
    assert res.get("coupon_and_margin_protection", {}).get("circuit_breaker_tripped") is False
    print("[OK] Teszt 2 sikeresen lefutott!")


def test_scenario_3_healthy_order():
    print("\n--- TESZT 3: Teljesen egeszseges tranzakcio ---")
    payload = {
        "event_id": "ANOM-TEST-003",
        "store_name": "ProfiSzerszam Webshop",
        "cart_order_context": {
            "regular_retail_price_huf": 89900,
            "wholesale_cost_price_huf": 62000,
            "applied_coupon_code": "SPRING10",
            "coupon_discount_percent": 10,
            "discounted_checkout_price_huf": 80910
        },
        "payment_gateway_health": {
            "primary_gateway": "SimplePay OTP",
            "consecutive_failures": 0,
            "hourly_success_rate_pct": 98.8
        }
    }
    
    res = run(payload)
    print(f"Osszesitett egeszseg: {res.get('overall_health')}")
    print(f"Kapu Failover szukseges: {res.get('payment_gateway_monitoring', {}).get('failover_required')}")
    print(f"Netto arres: {res.get('coupon_and_margin_protection', {}).get('net_margin_huf')} Ft")
    
    assert res.get("status") == "success"
    assert res.get("overall_health") == "NORMAL"
    assert res.get("payment_gateway_monitoring", {}).get("failover_required") is False
    assert res.get("coupon_and_margin_protection", {}).get("circuit_breaker_tripped") is False
    print("[OK] Teszt 3 sikeresen lefutott!")


if __name__ == "__main__":
    print("=== MODULE 4.13: WEBARUHAZI ANOMALIA DETEKTALAS MOCK TESZT ===")
    test_scenario_1_double_critical_anomaly()
    test_scenario_2_gateway_failover_only()
    test_scenario_3_healthy_order()
    print("\n[MINDEN TESZT SIKERESEN LEFUTOTT!]")
