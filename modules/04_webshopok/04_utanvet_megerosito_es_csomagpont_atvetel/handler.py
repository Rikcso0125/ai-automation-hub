# -*- coding: utf-8 -*-
"""
Module 4.04: Utánvét-Megerősítő és Csomagpont Átvételi SMS Értesítő
Kockázatalapú utánvét (COD) előszűrés, csomagfeladási zárlat nem megerősített rendeléseknél,
és többcsatornás csomagautomata lejárati értesítő családtagoknak továbbítható meghatalmazással.
"""
import os
import sys
import json
import datetime
import hashlib
from typing import Dict, Any, List, Optional

class CodAndLockerVerifierHandler:
    """Utánvét-ellenőrző és csomagpont átvételi menedzser"""
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.service_mode = self.config.get("service_mode", "mock")
        self.risk_threshold = int(self.config.get("cod_risk_threshold", 45))
        self.high_value_limit = float(self.config.get("cod_high_value_limit_huf", 40000.0))
        self.grace_hours = int(self.config.get("confirmation_grace_hours", 24))
        self.shipping_hold_action = self.config.get("shipping_hold_action", "shipping_hold_cs_escalation")
        self.locker_warning_hours = int(self.config.get("locker_warning_hours_before", 24))
        self.storage_path = self.config.get("storage_path", "data/utanvet_es_csomagpont_naplo.json")
        
    def evaluate_cod_risk(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Kockázatalapú intelligens szűrés (1. Kérdés - B opció)"""
        score = 0
        risk_factors = []
        
        cust = order.get("customer", {})
        c_email = cust.get("email", "").lower()
        c_phone = cust.get("phone", "")
        address = cust.get("shipping_address", {})
        total = float(order.get("total_gross_huf", 0))
        
        # 1. Első vásárló-e?
        if order.get("is_first_purchase", True):
            score += 20
            risk_factors.append("Uj vasarlo (nincs rendelesi eloelet)")
            
        # 2. Nagy értékű utánvét
        if total >= self.high_value_limit:
            score += 25
            risk_factors.append(f"Nagy erteku utanvet ({int(total):,} Ft >= {int(self.high_value_limit):,} Ft)".replace(",", " "))
            
        # 3. Hiányos / gyanús szállítási cím
        street = address.get("street", "").strip()
        house_no = address.get("house_number", "").strip()
        if not house_no or len(street) < 4:
            score += 30
            risk_factors.append("Hianyos szallitasi cim (hianyzik a hazszam vagy tul rovid utcanev)")
            
        # 4. Eldobható / gyanús email cím
        suspicious_domains = ["tempmail", "mailinator", "dispostable", "10minutemail", "trashmail"]
        if any(d in c_email for d in suspicious_domains):
            score += 20
            risk_factors.append("Gyanus / eldobhato email cim")
            
        # 5. Múltbéli sikertelen átvétel
        if order.get("past_uncollected_returns", 0) > 0:
            score += 50
            risk_factors.append(f"Múltbéli at nem vett csomag ({order.get('past_uncollected_returns')} db)")
            
        requires_confirmation = score >= self.risk_threshold
        
        order_id = order.get("order_id", "ORD-UNKNOWN")
        token = hashlib.sha256(f"{order_id}-COD-CONFIRM".encode("utf-8")).hexdigest()[:10]
        confirm_url = f"https://profigepesz.hu/cod/confirm?order={order_id}&token={token}"
        
        c_first = cust.get("name", "Vásárló").split()[0]
        sms_text = (
            f"Szia {c_first}! Koszonjuk a ProfiGepesz megrendelesed ({order_id}, {int(total):,} Ft)! " 
            f"Mivel nagy erteku utanvetes csomagrol van szo, kerjuk, erositsd meg 1 kattintassal a feladast: {confirm_url}"
        ).replace(",", " ")
        
        return {
            "order_id": order_id,
            "risk_score": min(100, score),
            "risk_threshold": self.risk_threshold,
            "requires_confirmation": requires_confirmation,
            "risk_factors": risk_factors,
            "fulfillment_status": "PENDING_CUSTOMER_CONFIRMATION" if requires_confirmation else "APPROVED_FOR_FULFILLMENT",
            "confirmation_link": confirm_url if requires_confirmation else None,
            "sms_dispatch": {
                "recipient": c_phone,
                "message": sms_text
            } if requires_confirmation else None
        }

    def handle_unconfirmed_order(self, order_id: str, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Nem megerősített rendelés kezelése: csomagfeladási zárlat és riasztás (2. Kérdés - A opció)"""
        cust = order_data.get("customer", {})
        total = order_data.get("total_gross_huf", 0)
        
        ticket = {
            "ticket_id": f"TICKET-COD-HOLD-{order_id}",
            "action": "SHIPPING_HOLD",
            "severity": "HIGH",
            "assigned_to": "Vevőszolgálat - Utánvét Ellenőrzés",
            "customer_name": cust.get("name"),
            "customer_phone": cust.get("phone"),
            "order_value_huf": total,
            "hold_reason": f"A vevő {self.grace_hours} órán belül nem kattintott az utánvét megerősítésre.",
            "required_action": "Közvetlen telefonos egyeztetés szükséges a futárcímke kinyomtatása előtt!",
            "erp_status": "LOCKED_SHIPPING_HOLD"
        }
        
        return {
            "order_id": order_id,
            "shipping_hold_active": True,
            "label_printing_allowed": False,
            "escalation_ticket": ticket
        }

    def process_locker_deadline_alert(self, locker_data: Dict[str, Any]) -> Dict[str, Any]:
        """Csomagautomata lejárati vészjelzés és továbbítható meghatalmazás (3. Kérdés - C opció)"""
        parcel_id = locker_data.get("parcel_id", "PARCEL-12345")
        carrier = locker_data.get("carrier", "Foxpost")
        locker_name = locker_data.get("locker_name", "Budapest Mammut I. Automata")
        code = locker_data.get("pickup_code", "991823")
        deadline = locker_data.get("deadline_datetime", "2026-09-21 22:00")
        cust = locker_data.get("customer", {})
        c_name = cust.get("name", "Vásárló")
        c_first = c_name.split()[0]
        c_phone = cust.get("phone", "")
        c_email = cust.get("email", "")
        
        token = hashlib.sha256(f"{parcel_id}-PROXY-PICKUP".encode("utf-8")).hexdigest()[:10]
        proxy_link = f"https://profigepesz.hu/locker/proxy?parcel={parcel_id}&token={token}"
        
        sms_text = (
            f"FIGYELEM {c_first}! A {carrier} csomagod ({parcel_id}) atveteli ideje LEJAR: {deadline}! " 
            f"Nyitokod: {code}. Helyszin: {locker_name}. " 
            f"Nem tudsz elmenni? Kuldd el a linket csaladtagodnak az atvetelhez: {proxy_link}"
        )
        
        email_subject = f"[SURGOS] Csomagod atveteli ideje ma lejar ({carrier} - {locker_name})"
        email_body = chr(10).join([
            f"Kedves {c_first}!",
            "",
            f"Értesítünk, hogy a(z) {carrier} csomagautomatában lévő csomagod átvételi határideje hamarosan lejár ({deadline}).",
            f"Átvételi helyszín: {locker_name}",
            f"Nyitókód: {code}",
            "",
            "Amennyiben nem tudsz érte menni, továbbítsd az alábbi 1-kattintásos meghatalmazást egy családtagodnak:",
            f"Meghatalmazott átvételi kártya: {proxy_link}",
            "",
            "Üdvözlettel: ProfiGépész Kézbesítés-menedzsment"
        ])
        
        return {
            "parcel_id": parcel_id,
            "carrier": carrier,
            "deadline": deadline,
            "alert_triggered": True,
            "proxy_pickup_url": proxy_link,
            "notifications_dispatched": {
                "sms": {"recipient": c_phone, "content": sms_text},
                "whatsapp": {"recipient": c_phone, "content": sms_text},
                "email": {"recipient": c_email, "subject": email_subject, "body": email_body}
            }
        }

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fő végrehajtó metódus"""
        event_type = payload.get("event_type", "VERIFY_COD_ORDER")
        now = datetime.datetime.now().isoformat()
        
        if event_type == "VERIFY_COD_ORDER":
            order = payload.get("order", {})
            result = self.evaluate_cod_risk(order)
        elif event_type == "CHECK_UNCONFIRMED_ORDERS":
            order_id = payload.get("order_id", "ORD-UNKNOWN")
            order_data = payload.get("order_data", {})
            result = self.handle_unconfirmed_order(order_id, order_data)
        elif event_type == "LOCKER_DEADLINE_ALERT":
            locker_data = payload.get("locker_data", {})
            result = self.process_locker_deadline_alert(locker_data)
        else:
            result = {"error": f"Ismeretlen event_type: {event_type}"}
            
        # Mentés naplóba
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        existing = []
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = []
        existing.append({"event_type": event_type, "timestamp": now, "result": result})
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(existing[-100:], f, indent=2, ensure_ascii=False)
            
        return {
            "status": "success",
            "module_id": "04_utanvet_megerosito_es_csomagpont_atvetel",
            "processed_at": now,
            "result": result
        }

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Szabványos hub belépési pont"""
    effective_config = dict(config or {})
    if "config" in payload and isinstance(payload["config"], dict):
        effective_config.update(payload["config"])
        
    handler = CodAndLockerVerifierHandler(effective_config)
    return handler.execute(payload)

if __name__ == "__main__":
    sample = {
        "event_type": "VERIFY_COD_ORDER",
        "order": {
            "order_id": "ORD-TEST-99",
            "total_gross_huf": 65000,
            "is_first_purchase": True,
            "customer": {
                "name": "Kovács Dániel",
                "phone": "+36301234567",
                "email": "dani@tempmail.com",
                "shipping_address": {"street": "Fő utca", "house_number": ""}
            }
        }
    }
    res = run(sample)
    print(json.dumps(res, indent=2, ensure_ascii=False))