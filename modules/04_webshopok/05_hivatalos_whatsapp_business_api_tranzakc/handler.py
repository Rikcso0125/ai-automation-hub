# -*- coding: utf-8 -*-
"""
Module 4.05: Hivatalos WhatsApp Business API Tranzakciós Vevőszolgálat
Automatikus rendelésigazolások, futárkövetési értesítők és 0-24 chatügyfélszolgálat
választható kézbesítési móddal (HSM / Interaktív / Hibrid SMS), AI hatáskörrel és Add-to-Order bővítéssel.
"""
import os
import sys
import json
import datetime
import time
from typing import Dict, Any, List, Optional

class WhatsAppBusinessSupportHandler:
    """WhatsApp Business API és AI ügyfélszolgálati motor"""
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.service_mode = self.config.get("service_mode", "mock")
        self.delivery_mode = self.config.get("template_delivery_mode", "hybrid_sms_fallback")  # hsm_utility, interactive_buttons, hybrid_sms_fallback
        self.ai_support_mode = self.config.get("ai_support_mode", "hitl_approval_gate")  # autonomous_full, human_handoff_rules, hitl_approval_gate
        self.enable_add_to_order = bool(self.config.get("enable_add_to_order", True))
        self.add_to_order_window_min = int(self.config.get("add_to_order_window_minutes", 15))
        self.storage_path = self.config.get("storage_path", "data/whatsapp_vevoszolgalat_naplo.json")
        
    def dispatch_outbound_notification(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Kimenő tranzakciós WhatsApp értesítés összeállítása (1. és 3. Kérdés)"""
        order_id = order.get("order_id", "ORD-UNKNOWN")
        c_name = order.get("customer_name", "Vásárló")
        c_first = c_name.split()[0]
        c_phone = order.get("customer_phone", "")
        total = order.get("total_gross_huf", 0)
        carrier = order.get("carrier", "GLS")
        track_url = order.get("tracking_url", f"https://gls-group.com/track/{order_id}")
        invoice_url = order.get("invoice_pdf_url", f"https://szamlak.profigepesz.hu/pdf/{order_id}.pdf")
        items = order.get("items", [])
        main_item_name = items[0].get("name", "megrendelt termék") if items else "megrendelt termék"
        
        # 1. Sablon formátum kiválasztása
        payload_structure = {}
        if self.delivery_mode == "hsm_utility":
            payload_structure = {
                "type": "template",
                "template_name": "order_confirmation_v2_utility",
                "language": {"code": "hu"},
                "components": [
                    {"type": "header", "parameters": [{"type": "text", "text": f"Rendelés: {order_id}"}]},
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": c_first},
                            {"type": "text", "text": f"{int(total):,} Ft".replace(",", " ")},
                            {"type": "text", "text": carrier},
                            {"type": "text", "text": main_item_name}
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type": "url",
                        "index": 0,
                        "parameters": [{"type": "text", "text": track_url}]
                    }
                ]
            }
        else:
            # interactive_buttons vagy hybrid
            payload_structure = {
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {
                        "text": (
                            f"Szia {c_first}! Örömmel értesítünk, hogy a(z) {order_id} számú rendelésedet rögzítettük! " 
                            f"Összeg: {int(total):,} Ft. Futár: {carrier}."
                        ).replace(",", " ")
                    },
                    "action": {
                        "buttons": [
                            {"type": "reply", "reply": {"id": "BTN_TRACK", "title": "Csomagkövetés"}},
                            {"type": "reply", "reply": {"id": "BTN_INVOICE", "title": "Számla letöltés"}},
                            {"type": "reply", "reply": {"id": "BTN_HELP", "title": "Kérdésem van"}}
                        ]
                    }
                }
            }
            
        # 2. Hibrid SMS Fallback szimuláció (ha a szám nem WhatsApp képes)
        has_whatsapp = order.get("has_whatsapp_account", True)
        delivery_report = {}
        if self.delivery_mode == "hybrid_sms_fallback" and not has_whatsapp:
            sms_fallback_text = f"Szia {c_first}! A {order_id} rendelesed rogzitettuk ({int(total):,} Ft). Futar: {carrier}. Nyomkovetes: {track_url}".replace(",", " ")
            delivery_report = {
                "channel": "SMS_FALLBACK_TELNYX",
                "reason": "NO_WHATSAPP_ACCOUNT_ON_PHONE",
                "recipient": c_phone,
                "sms_content": sms_fallback_text,
                "status": "DELIVERED_VIA_SMS"
            }
        else:
            delivery_report = {
                "channel": "WHATSAPP_CLOUD_API",
                "recipient": c_phone,
                "meta_wamid": f"wamid.HBgL{int(time.time()*1000)}",
                "status": "DELIVERED_TO_WHATSAPP"
            }
            
        # 3. Add-to-Order csomagbővítés felajánlása (3. Kérdés - C opció)
        add_to_order_offer = None
        if self.enable_add_to_order:
            add_to_order_offer = {
                "active": True,
                "time_window_minutes": self.add_to_order_window_min,
                "recommended_sku": "BOSCH-BIT-SET-32",
                "recommended_name": "Bosch Professional 32-részes Csavarozó Bitkészlet",
                "special_price_huf": 4990,
                "original_price_huf": 6990,
                "shipping_cost_huf": 0,
                "message": (
                    f"Még van {self.add_to_order_window_min} perced! Tedd a csomagodba a prémium 32-részes Bosch bitkészletet " 
                    "6 990 Ft helyett csak 4 990 Ft-ért, és a meglévő rendeléseddel együtt DÍJMENTESEN szállítjuk!"
                ),
                "action_button": "HOZZÁADOM (+4 990 Ft)"
            }
            
        return {
            "order_id": order_id,
            "delivery_mode_used": self.delivery_mode,
            "delivery_report": delivery_report,
            "whatsapp_payload": payload_structure,
            "add_to_order_offer": add_to_order_offer,
            "sent_at": datetime.datetime.now().isoformat()
        }

    def process_inbound_chat_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Bejövő WhatsApp vásárlói kérdés autonóm megválaszolása (2. Kérdés)"""
        sender_phone = message.get("sender_phone", "")
        user_text = message.get("text", "").strip()
        order_ref = message.get("order_reference", "ORD-WEB-2026-7711")
        
        # Szándékfelismerés
        t_low = user_text.lower()
        if "hol" in t_low or "csomag" in t_low or "mikor" in t_low or "futar" in t_low:
            intent = "ORDER_STATUS_INQUIRY"
            ai_reply = "A csomagodat a GLS futárszolgálat dolgozza fel. Várható érkezés: holnap 09:00 és 14:00 között. Követés: https://gls-group.com/track/" + order_ref
            is_sensitive = False
        elif "szamla" in t_low or "számla" in t_low or "afa" in t_low:
            intent = "INVOICE_REQUEST"
            ai_reply = f"A rendelésed hivatalos elektronikus számláját közvetlenül letöltheted innen: https://szamlak.profigepesz.hu/pdf/{order_ref}.pdf"
            is_sensitive = False
        elif "cím" in t_low or "cim" in t_low or "modos" in t_low or "lemond" in t_low or "torol" in t_low:
            intent = "SENSITIVE_ORDER_MODIFICATION"
            ai_reply = "Érzékeltem a szállítási adat módosítási / rendeléstörlési kérésedet."
            is_sensitive = True
        else:
            intent = "GENERAL_SUPPORT"
            ai_reply = "Köszönjük a megkeresést! ProfiGépész AI asszisztens vagyok. Miben segíthetek a rendeléseddel kapcsolatban?"
            is_sensitive = False
            
        # AI Hatáskör kiértékelése
        handling_result = {}
        if is_sensitive:
            if self.ai_support_mode == "hitl_approval_gate":
                handling_result = {
                    "mode": "hitl_approval_gate",
                    "status": "APPROVAL_CARD_CREATED",
                    "ai_draft_response": "Kérésedet rögzítettük és átadtuk az ügyfélszolgálatnak, amint a kollégánk 1 kattintással jóváhagyja, módosítjuk a címet.",
                    "human_approval_card": {
                        "order_id": order_ref,
                        "customer_phone": sender_phone,
                        "requested_action": user_text,
                        "risk_level": "MEDIUM",
                        "approve_button_url": f"https://admin.profigepesz.hu/approve?order={order_ref}&action=address_change"
                    }
                }
            elif self.ai_support_mode == "human_handoff_rules":
                handling_result = {
                    "mode": "human_handoff_rules",
                    "status": "TRANSFERRED_TO_LIVE_AGENT",
                    "ai_draft_response": "Kérlek várj egy pillanatot, átkapcsollak az élő ügyfélszolgálati munkatársunkhoz!",
                    "handoff_ticket_id": f"TICKET-WA-{int(time.time())}"
                }
            else:
                handling_result = {
                    "mode": "autonomous_full",
                    "status": "AUTONOMOUSLY_EXECUTED",
                    "ai_draft_response": f"Rendelésed ({order_ref}) adatainak módosítását a rendszer automatikusan elvégezte!"
                }
        else:
            handling_result = {
                "mode": "autonomous_resolved",
                "status": "DIRECT_ANSWER_SENT",
                "ai_draft_response": ai_reply
            }
            
        return {
            "inbound_message": user_text,
            "sender_phone": sender_phone,
            "intent_detected": intent,
            "ai_support_mode": self.ai_support_mode,
            "resolution": handling_result,
            "handled_at": datetime.datetime.now().isoformat()
        }

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Hub végrehajtási metódus"""
        event_type = payload.get("event_type", "ORDER_CONFIRMATION_OUTBOUND")
        now = datetime.datetime.now().isoformat()
        
        if event_type in ["ORDER_CONFIRMATION_OUTBOUND", "SHIPPING_UPDATE_OUTBOUND"]:
            order = payload.get("order", {})
            data = self.dispatch_outbound_notification(order)
        elif event_type == "CUSTOMER_MESSAGE_INBOUND":
            msg = payload.get("message", {})
            data = self.process_inbound_chat_message(msg)
        else:
            order = payload.get("order", payload)
            data = self.dispatch_outbound_notification(order)
            
        # Mentés naplóba
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        existing = []
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = []
        existing.append({"event_type": event_type, "timestamp": now, "data": data})
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(existing[-100:], f, indent=2, ensure_ascii=False)
            
        return {
            "status": "success",
            "module_id": "05_hivatalos_whatsapp_business_api_tranzakc",
            "processed_at": now,
            "whatsapp_data": data
        }

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Szabványos hub belépési pont"""
    effective_config = dict(config or {})
    if "config" in payload and isinstance(payload["config"], dict):
        effective_config.update(payload["config"])
        
    handler = WhatsAppBusinessSupportHandler(effective_config)
    return handler.execute(payload)

if __name__ == "__main__":
    sample = {
        "event_type": "ORDER_CONFIRMATION_OUTBOUND",
        "order": {
            "order_id": "ORD-TEST-1234",
            "customer_name": "Balogh Ádám",
            "customer_phone": "+36304445566",
            "total_gross_huf": 49990
        }
    }
    res = run(sample)
    print(json.dumps(res, indent=2, ensure_ascii=False))