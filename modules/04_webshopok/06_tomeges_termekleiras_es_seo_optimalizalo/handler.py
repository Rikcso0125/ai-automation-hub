# -*- coding: utf-8 -*-
"""
Module 4.06: Tömeges Termékleírás és SEO Optimalizáló Motor
Nyers beszállítói adatokból készít vevőcsalogató, Google-re optimalizált
termékleírásokat, meta tag-eket és Schema.org JSON-LD-t választható stílusban és szinkronnal.
"""
import os
import sys
import json
import datetime
import re
import hashlib
from typing import Dict, Any, List, Optional

class BulkSeoDescriptionHandler:
    """Termékleírás és keresőoptimalizáló motor"""
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.service_mode = self.config.get("service_mode", "mock")
        self.style_mode = self.config.get("style_tone_mode", "hybrid_dual")  # b2b_technical, b2c_emotional, hybrid_dual
        self.seo_mode = self.config.get("seo_package_mode", "full_seo_suite")  # serp_meta_only, schema_faq, full_seo_suite
        self.sync_mode = self.config.get("sync_approval_mode", "diff_review_gate")  # direct_api_bulk_sync, csv_excel_export, diff_review_gate
        self.platform = self.config.get("target_ecommerce_platform", "shopify")
        self.storage_path = self.config.get("storage_path", "data/termekleiras_seo_naplo.json")
        
    def _generate_slug(self, text: str) -> str:
        """Tiszta keresőbarát URL slug generálása"""
        slug = text.lower()
        replacements = {"á": "a", "é": "e", "í": "i", "ó": "o", "ö": "o", "ő": "o", "ú": "u", "ü": "u", "ű": "u"}
        for k, v in replacements.items():
            slug = slug.replace(k, v)
        slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
        return slug[:70]

    def generate_description_content(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Termékleírás generálása a választott stílus szerint (1. Kérdés)"""
        sku = product.get("sku", "SKU-001")
        title = product.get("supplier_title", "Termék")
        brand = product.get("brand", "Márka")
        category = product.get("category", "Szerszámok")
        specs = product.get("key_specs", {})
        
        # Műszaki specifikáció táblázat HTML
        table_rows = "".join([
            f'<tr><td style="padding:8px;background:#f9f9f9;font-weight:bold;width:40%;border:1px solid #ddd;">{k}</td><td style="padding:8px;border:1px solid #ddd;">{v}</td></tr>'
            for k, v in specs.items()
        ])
        specs_table_html = f'<table style="width:100%;border-collapse:collapse;margin:15px 0;"><tbody>{table_rows}</tbody></table>'
        
        # B2B Műszaki Leírás
        b2b_html = chr(10).join([
            f'<h3>{brand} Ipari és Szakipari Műszaki Megoldások</h3>',
            f'<p>A <strong>{title}</strong> kifejezetten a folyamatos, intenzív szakipari munkavégzésre tervezett modell. A robusztus felépítés, a korszerű szénkefementes hajtás és a precíziós tokmányrendszer garantálja a maximális hatékonyságot és a minimális karbantartási igényt.</p>',
            '<h4>Főbb Műszaki Paraméterek és Szabványok:</h4>',
            specs_table_html,
            '<p><em>Megfelel a vonatkozó EN/ISO ipari biztonsági szabványoknak. CE minősített termék.</em></p>'
        ])
        
        # B2C Érzelmes & Előnyfókuszú Leírás
        b2c_html = chr(10).join([
            f'<h3>Dolgozz úgy, mint a profik a {brand} csúcsmodelljével!</h3>',
            f'<p>Unod már, hogy a géped lefullad a legkeményebb feladatoknál? A(z) <strong>{title}</strong> nem ismer kompromisszumot: lenyűgöző forgatónyomatékával és pillekönnyű kezelhetőségével a legnehezebb feladatok is gyerekjátéknak tűnnek!</p>',
            '<h4>Miért fogod imádni minden egyes nap?</h4>',
            '<ul>',
            '<li><strong>Brutális Erő:</strong> Akár a legkeményebb fába vagy acélba is könnyedén behatol.</li>',
            '<li><strong>Hosszú Élettartam:</strong> A szénkefementes motornak köszönhetően nem melegszik és nem kopik.</li>',
            '<li><strong>Ergonomikus Kényelem:</strong> Csúszásbiztos markolat a fáradságmentes egész napos munkához.</li>',
            '<li><strong>Gyors Szerszámcsere:</strong> Egyetlen mozdulattal cserélhető bitfejek a fém tokmánynak hála.</li>',
            '</ul>',
            '<div style="background:#e3f2fd;padding:12px;border-left:4px solid #1976d2;margin:15px 0;">',
            '<p style="margin:0;"><strong>Hivatalos Garancia:</strong> Erre a modellre kiterjesztett gyártói jótállást és országos szervizhálózatot biztosítunk!</p>',
            '</div>'
        ])
        
        # Kettős Hibrid Leírás
        hybrid_html = chr(10).join([
            b2c_html,
            '<hr style="border:0;border-top:1px solid #eee;margin:25px 0;">',
            b2b_html
        ])
        
        if self.style_mode == "b2b_technical":
            chosen_html = b2b_html
            clean_title = f"{brand} - {sku} Műszaki Adatlap"
        elif self.style_mode == "b2c_emotional":
            chosen_html = b2c_html
            clean_title = f"{title} – Erő és Megbízhatóság"
        else:
            chosen_html = hybrid_html
            clean_title = f"{brand} {sku} Akkus Fúrócsavarozó"
            
        return {
            "clean_title": clean_title,
            "html_description": chosen_html,
            "style_applied": self.style_mode,
            "raw_input_text": product.get("supplier_raw_text", "")
        }

    def generate_seo_package(self, product: Dict[str, Any], content: Dict[str, Any]) -> Dict[str, Any]:
        """SEO meta tagek és Schema.org JSON-LD generálása (2. Kérdés)"""
        sku = product.get("sku", "SKU-001")
        title = content["clean_title"]
        brand = product.get("brand", "Márka")
        price = product.get("price_gross_huf", 49990)
        
        slug = self._generate_slug(f"{brand}-{sku}")
        meta_title = f"{title} | ProfiGépész"[:60]
        meta_desc = f"Rendeld meg a(z) {title} modellt hivatalos garanciával, raktárról másnapi szállítással a ProfiGépésztől! Kiváló ár, azonnali raktárkészlet."[:155]
        
        h1 = title
        h2s = [
            f"Miért válaszd a(z) {brand} {sku} készüléket?",
            "Részletes Műszaki Paraméterek",
            "Gyakran Ismételt Kérdések és Garancia"
        ]
        
        # Schema.org Product & FAQ JSON-LD
        schema_product = {
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": title,
            "image": [f"https://profigepesz.hu/images/{slug}.jpg"],
            "description": meta_desc,
            "sku": sku,
            "brand": {"@type": "Brand", "name": brand},
            "offers": {
                "@type": "Offer",
                "url": f"https://profigepesz.hu/termek/{slug}",
                "priceCurrency": "HUF",
                "price": price,
                "availability": "https://schema.org/InStock",
                "itemCondition": "https://schema.org/NewCondition"
            }
        }
        
        schema_faq = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": "Mennyi garancia jár a termékre?",
                    "acceptedAnswer": {"@type": "Answer", "text": "A termékre 3 év hivatalos magyarországi gyártói garancia vonatkozik online regisztrációval."}
                },
                {
                    "@type": "Question",
                    "name": "Mikorra várható a szállítás?",
                    "acceptedAnswer": {"@type": "Answer", "text": "Raktáron lévő termék esetén a 14:00-ig leadott rendeléseket már a következő munkanapon kiszállítjuk."}
                }
            ]
        }
        
        return {
            "meta_title": meta_title,
            "meta_description": meta_desc,
            "url_slug": slug,
            "h1": h1,
            "h2_headings": h2s,
            "lsi_keywords": ["akkus furo", "szénkefementes furocsavarozo", "profi szerszam", "18v akku"],
            "schema_product_jsonld": schema_product if self.seo_mode in ["schema_faq", "full_seo_suite"] else None,
            "schema_faq_jsonld": schema_faq if self.seo_mode in ["schema_faq", "full_seo_suite"] else None
        }

    def process_sync_gate(self, product: Dict[str, Any], content: Dict[str, Any], seo: Dict[str, Any]) -> Dict[str, Any]:
        """Szinkronizáció és jóváhagyási folyamat (3. Kérdés)"""
        sku = product.get("sku", "SKU-001")
        
        if self.sync_mode == "direct_api_bulk_sync":
            return {
                "mode": "direct_api_bulk_sync",
                "status": "PUBLISHED_VIA_API",
                "target_platform": self.platform,
                "api_endpoint": f"https://api.{self.platform}.com/v1/products/{sku}",
                "response_code": 200,
                "message": "Termékleírás és SEO meta adatok közvetlenül közzétéve a webáruházban."
            }
        elif self.sync_mode == "csv_excel_export":
            csv_row = {
                "Handle": seo["url_slug"],
                "Title": content["clean_title"],
                "Body (HTML)": content["html_description"][:100] + "...",
                "Vendor": product.get("brand"),
                "Variant SKU": sku,
                "Variant Price": product.get("price_gross_huf"),
                "SEO Title": seo["meta_title"],
                "SEO Description": seo["meta_description"]
            }
            return {
                "mode": "csv_excel_export",
                "status": "EXPORT_READY",
                "export_filename": f"export_products_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                "sample_row": csv_row,
                "message": "Készre formázott importfájl letölthető az admin menedzser számára."
            }
        else:
            # diff_review_gate
            token = hashlib.sha256(f"{sku}-DIFF-GATE".encode("utf-8")).hexdigest()[:10]
            return {
                "mode": "diff_review_gate",
                "status": "PENDING_DIFF_APPROVAL",
                "diff_summary": {
                    "original_raw_length": len(content["raw_input_text"]),
                    "generated_html_length": len(content["html_description"]),
                    "expansion_factor": round(len(content["html_description"]) / max(1, len(content["raw_input_text"])), 1)
                },
                "approval_action_url": f"https://admin.profigepesz.hu/seo/approve?sku={sku}&token={token}",
                "message": "Egymás melletti diff előnézet elkészült, 1-kattintásos vezetői publikálásra kész."
            }

    def process_product(self, raw_product: Dict[str, Any]) -> Dict[str, Any]:
        """Egy termék teljes leírás- és SEO generálása"""
        content = self.generate_description_content(raw_product)
        seo = self.generate_seo_package(raw_product, content)
        sync = self.process_sync_gate(raw_product, content, seo)
        
        result = {
            "sku": raw_product.get("sku"),
            "brand": raw_product.get("brand"),
            "title": content["clean_title"],
            "html_description": content["html_description"],
            "seo": seo,
            "sync_result": sync,
            "generated_at": datetime.datetime.now().isoformat()
        }
        
        self._log_generation(result)
        return result

    def _log_generation(self, record: Dict[str, Any]) -> None:
        """Audit napló perzisztálása"""
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
        raw = payload.get("raw_product", payload)
        res = self.process_product(raw)
        return {
            "status": "success",
            "module_id": "06_tomeges_termekleiras_es_seo_optimalizalo",
            "processed_at": datetime.datetime.now().isoformat(),
            "product_seo_data": res
        }

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Szabványos hub belépési pont"""
    effective_config = dict(config or {})
    if "config" in payload and isinstance(payload["config"], dict):
        effective_config.update(payload["config"])
        
    handler = BulkSeoDescriptionHandler(effective_config)
    return handler.execute(payload)

if __name__ == "__main__":
    sample = {
        "raw_product": {
            "sku": "BOSCH-GSR-18V-55",
            "supplier_title": "BOSCH GSR 18V-55 AKKUS FUROCSAVAROZO SOLO 06019H5202",
            "supplier_raw_text": "Szenkefementes EC motor. 55 Nm nyomatek. 13 mm fem tokmany.",
            "brand": "Bosch Professional",
            "price_gross_huf": 49990,
            "key_specs": {"Feszültség": "18V", "Nyomaték": "55 Nm"}
        }
    }
    res = run(sample)
    print(json.dumps(res, indent=2, ensure_ascii=False))