# -*- coding: utf-8 -*-
"""
Module 4.03: Dinamikus Kosárelhagyás Visszahódítás (SMS és Email)
Szerkeszthető 2-lépcsős visszahódító szekvencia (SMS + Email),
saját szerkesztésű ösztönzőkkel és 1-kattintásos kosár-visszaállító linkkel.
"""
import os
import sys
import json
import datetime
import hashlib
from typing import Dict, Any, List, Optional

class DynamicAbandonedCartRecoveryHandler:
    """Dinamikus kosárelhagyás visszahódítási motor"""
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.service_mode = self.config.get("service_mode", "mock")
        self.sms_delay_minutes = int(self.config.get("sms_delay_minutes", 30))
        self.email_delay_hours = int(self.config.get("email_delay_hours", 24))
        self.incentive_mode = self.config.get("incentive_mode", "tiered_discount")
        self.storage_path = self.config.get("storage_path", "data/kosarelhagyas_naplo.json")
        
        # Szerkeszthető SMS sablon
        self.sms_template = self.config.get(
            "sms_template",
            "Szia {customer_first_name}! A kosaradban levo {product_name} megvar. " 
            "Fejezd be a rendelest 1 kattintassal {coupon_text}: {restore_url}"
        )
        
        # Saját szerkeszthető ösztönző szabályok
        self.custom_rules = self.config.get("custom_rules", [
            {
                "min_cart_value": 0,
                "coupon_code": "INGYENSZALLITAS",
                "discount_label": "Ingyenes házhozszállítás (1 990 Ft megtakarítás)",
                "highlight_benefit": "30 napos ingyenes csere és azonnali raktári feladás"
            },
            {
                "min_cart_value": 50000,
                "coupon_code": "VIP5PERCENT",
                "discount_label": "5% Extra Kedvezmény",
                "highlight_benefit": "3 év kiterjesztett garancia és VIP elsőbbségi szerviz"
            }
        ])
        
        # Kategória-specifikus aggálykezelő érvek
        self.category_arguments = {
            "szerszamgep": {
                "warranty": "3 Év Hivatalos Magyar Gyári Garancia",
                "social_proof": "Több mint 4 200 elégedett hazai szakember választása.",
                "urgency_tip": "A beszállítói áremelkedés előtt még a jelenlegi áron garantáljuk a készletet."
            },
            "epitoanyag": {
                "warranty": "Törés- és sérülésbiztos raktári csomagolás",
                "social_proof": "100% minőségi tanúsítvánnyal rendelkező szakipari alapanyagok.",
                "urgency_tip": "Nagy tételes raktárkészletünkből azonnal szállítható."
            },
            "altalanos": {
                "warranty": "30 Napos Kérdés Nélküli Pénzvisszafizetési Garancia",
                "social_proof": "4.9 / 5.0 vásárlói elégedettségi értékelés Árukeresőn.",
                "urgency_tip": "Raktáron lévő termék, rendelés esetén holnap átadjuk a futárnak."
            }
        }

    def _determine_incentive(self, cart_total: float) -> Dict[str, Any]:
        """Ösztönző meghatározása a választott vagy egyedi szerkesztett szabályok szerint"""
        if self.incentive_mode == "no_coupon_value_only":
            return {
                "coupon_code": None,
                "discount_label": "Kupon nélküli értékfókusz",
                "benefit": "30 napos ingyenes visszaküldés és 100% pénzvisszafizetési garancia",
                "sms_coupon_text": "garanciaval es ingyenes visszakuldessel"
            }
        elif self.incentive_mode == "free_shipping":
            return {
                "coupon_code": "INGYENFUVAL",
                "discount_label": "Ingyenes Szállítás",
                "benefit": "Megajándékozunk az 1 990 Ft értékű házhozszállítással",
                "sms_coupon_text": "INGYEN SZALLITASSAL"
            }
        else:
            # tiered_discount vagy custom_rules a szabálylista alapján
            matched = self.custom_rules[0]
            for rule in sorted(self.custom_rules, key=lambda r: r.get("min_cart_value", 0), reverse=True):
                if cart_total >= rule.get("min_cart_value", 0):
                    matched = rule
                    break
                    
            return {
                "coupon_code": matched.get("coupon_code"),
                "discount_label": matched.get("discount_label"),
                "benefit": matched.get("highlight_benefit"),
                "sms_coupon_text": f"ajandek kuponnal ({matched.get('coupon_code')})"
            }

    def _build_restore_url(self, session_id: str, coupon_code: Optional[str] = None) -> str:
        """1-kattintásos kosár-újraépítő direkt link generálása"""
        token = hashlib.sha256(f"{session_id}-RECOVERY-SECRET".encode("utf-8")).hexdigest()[:12]
        base = f"https://profigepesz.hu/cart/restore?session={session_id}&token={token}"
        if coupon_code:
            base += f"&coupon={coupon_code}"
        return base

    def process_recovery(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Kosárelhagyás feldolgozása és a 2-lépcsős szekvencia összeállítása"""
        session_id = payload.get("cart_session_id", f"CART-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}")
        cust = payload.get("customer", {})
        c_name = cust.get("name", "Vásárló")
        c_first = c_name.split()[0] if c_name else "Kedves Vásárlónk"
        c_phone = cust.get("phone", "")
        c_email = cust.get("email", "")
        
        cart_items = payload.get("cart_items", [])
        if not cart_items:
            # Minta tétel, ha üres lenne
            cart_items = [{
                "sku": "DEFAULT-ITEM",
                "name": "Kiválasztott Termék",
                "category": "altalanos",
                "quantity": 1,
                "unit_price_gross": 29990,
                "stock_remaining": 3
            }]
            
        cart_total = sum(item.get("unit_price_gross", 0) * item.get("quantity", 1) for item in cart_items)
        hero_item = max(cart_items, key=lambda x: x.get("unit_price_gross", 0))
        category = hero_item.get("category", "altalanos")
        cat_args = self.category_arguments.get(category, self.category_arguments["altalanos"])
        
        # Ösztönző és direkt helyreállító link
        incentive = self._determine_incentive(cart_total)
        restore_url = self._build_restore_url(session_id, incentive.get("coupon_code"))
        
        now = datetime.datetime.now()
        sms_schedule = (now + datetime.timedelta(minutes=self.sms_delay_minutes)).isoformat()
        email_schedule = (now + datetime.timedelta(hours=self.email_delay_hours)).isoformat()
        
        # 1. LÉPÉS: SMS Generálás
        sms_text = self.sms_template.format(
            customer_first_name=c_first,
            product_name=hero_item.get("name", "terméked"),
            cart_total=f"{int(cart_total):,} Ft".replace(",", " "),
            coupon_text=incentive.get("sms_coupon_text", ""),
            restore_url=restore_url,
            coupon_code=incentive.get("coupon_code", "")
        )
        if hero_item.get("stock_remaining", 99) <= 3:
            sms_text += f" (Mar csak {hero_item.get('stock_remaining')} db raktaron!)"
            
        # 2. LÉPÉS: Részletes Formázott Email Generálás
        coupon_badge_html = ""
        if incentive.get("coupon_code"):
            coupon_badge_html = f'<div style="background:#e8f5e9;border:1px dashed #2e7d32;padding:12px;border-radius:6px;margin:15px 0;"><strong>Ajándék kuponkód:</strong> <span style="color:#2e7d32;font-size:16px;font-weight:bold;">{incentive.get("coupon_code")}</span> ({incentive.get("discount_label")})</div>'
            
        items_html = "".join([
            f'<tr><td style="padding:8px;border-bottom:1px solid #eee;">{it.get("name")} ({it.get("quantity")} db)</td><td style="padding:8px;border-bottom:1px solid #eee;text-align:right;"><strong>{int(it.get("unit_price_gross", 0) * it.get("quantity", 1)):,} Ft</strong></td></tr>'.replace(",", " ")
            for it in cart_items
        ])
        
        email_subject = f"Kedves {c_first}, a kosaradban maradt {hero_item.get('name')} még megvár!"
        email_html = chr(10).join([
            '<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;color:#333;line-height:1.6;">',
            f'<h2 style="color:#1a237e;">Kedves {c_first}!</h2>',
            '<p>Észrevettük, hogy a megkezdett megrendelésed befejezése félbeszakadt. Semmi gond, a kosarad tartalmát és az árakat félretettük a részedre!</p>',
            coupon_badge_html,
            '<table style="width:100%;border-collapse:collapse;margin:15px 0;background:#fafafa;border-radius:6px;overflow:hidden;">',
            items_html,
            f'<tr><td style="padding:10px;font-size:16px;"><strong>Összesen:</strong></td><td style="padding:10px;text-align:right;font-size:16px;color:#d32f2f;"><strong>{int(cart_total):,} Ft</strong></td></tr>'.replace(",", " "),
            '</table>',
            '<div style="background:#f5f5f5;padding:12px;border-radius:6px;margin:15px 0;font-size:13px;">',
            f'<p style="margin:4px 0;">🛡️ <strong>Biztonság:</strong> {cat_args["warranty"]}</p>',
            f'<p style="margin:4px 0;">⭐ <strong>Vásárlói visszajelzés:</strong> {cat_args["social_proof"]}</p>',
            f'<p style="margin:4px 0;">⚡ <strong>Raktárkészlet:</strong> {cat_args["urgency_tip"]}</p>',
            '</div>',
            f'<div style="text-align:center;margin:25px 0;"><a href="{restore_url}" style="background:#ff6f00;color:#fff;padding:14px 28px;text-decoration:none;font-size:16px;font-weight:bold;border-radius:6px;display:inline-block;">KOSÁR BETÖLTÉSE ÉS RENDELÉS BEFEJEZÉSE &raquo;</a></div>',
            '<p style="font-size:12px;color:#777;text-align:center;">Ha kérdésed merült fel, válaszolj erre az emailre vagy hívd ügyfélszolgálatunkat.</p>',
            '</div>'
        ])
        
        email_plain = chr(10).join([
            f"Kedves {c_first}!",
            "",
            f"A kosaradban maradt tételeket ({hero_item.get('name')}) elmentettük a részedre.",
            f"Kosárérték: {int(cart_total):,} Ft".replace(",", " "),
            f"Kuponkedvezmény: {incentive.get('discount_label')} ({incentive.get('coupon_code')})" if incentive.get("coupon_code") else "",
            "",
            f"Rendelés befejezése 1 kattintással: {restore_url}",
            "",
            f"Garancia: {cat_args['warranty']}",
            "Üdvözlettel: ProfiGépész Webáruház"
        ])
        
        result = {
            "cart_session_id": session_id,
            "customer": {"name": c_name, "phone": c_phone, "email": c_email},
            "cart_total_gross_huf": cart_total,
            "hero_product": hero_item.get("name"),
            "restore_cart_url": restore_url,
            "incentive_applied": incentive,
            "sequence_steps": [
                {
                    "step": 1,
                    "channel": "SMS",
                    "scheduled_at": sms_schedule,
                    "delay_minutes": self.sms_delay_minutes,
                    "recipient": c_phone,
                    "content": sms_text
                },
                {
                    "step": 2,
                    "channel": "EMAIL",
                    "scheduled_at": email_schedule,
                    "delay_hours": self.email_delay_hours,
                    "recipient": c_email,
                    "subject": email_subject,
                    "plain_text": email_plain,
                    "html_body": email_html
                }
            ],
            "handled_at": now.isoformat()
        }
        
        self._log_recovery(result)
        return result

    def _log_recovery(self, record: Dict[str, Any]) -> None:
        """Naplózás perzisztálása"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        existing = []
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = []
        existing.append(record)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(existing[-100:], f, indent=2, ensure_ascii=False)

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Hub végrehajtási metódus"""
        rec = self.process_recovery(payload)
        return {
            "status": "success",
            "module_id": "03_dinamikus_kosarelhagyas_visszahoditas_sm",
            "processed_at": datetime.datetime.now().isoformat(),
            "recovery_data": rec
        }

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Szabványos hub belépési pont"""
    effective_config = dict(config or {})
    if "config" in payload and isinstance(payload["config"], dict):
        effective_config.update(payload["config"])
        
    handler = DynamicAbandonedCartRecoveryHandler(effective_config)
    return handler.execute(payload)

if __name__ == "__main__":
    sample = {
        "cart_session_id": "CART-TEST-1234",
        "customer": {"name": "Kovács Péter", "phone": "+36301112233", "email": "kovacs.p@example.hu"},
        "cart_items": [{
            "sku": "MAKITA-DHP-484",
            "name": "Makita DHP484Z Akkus Ütvefúró",
            "category": "szerszamgep",
            "quantity": 1,
            "unit_price_gross": 64990,
            "stock_remaining": 2
        }]
    }
    res = run(sample)
    print(json.dumps(res, indent=2, ensure_ascii=False))