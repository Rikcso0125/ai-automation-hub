# -*- coding: utf-8 -*-
"""
Module 4.07: AI Termékfotó Stúdió & Életmódképek Generálása (FLUX / Midjourney)
Nyers termékfotók fotorealisztikus életszerű jelenetbe helyezése stúdiódíszletekkel,
többcsatornás marketing képarányokkal (1:1, 4:5, 9:16, 16:9) és trust badge márkázással.
"""
import os
import sys
import json
import datetime
import hashlib
from typing import Dict, Any, List, Optional

class AiProductPhotoStudioHandler:
    """AI Termékfotó és Életmódkép Stúdió Motor"""
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.service_mode = self.config.get("service_mode", "mock")
        self.staging_mode = self.config.get("staging_mode", "category_presets")
        self.preset_scene = self.config.get("preset_scene", "workshop_woodworking")
        self.aspect_ratio_mode = self.config.get("aspect_ratio_mode", "multi_marketing_pack")
        self.branding_mode = self.config.get("branding_sync_mode", "trust_badge_overlay")
        self.storage_path = self.config.get("storage_path", "data/ai_termekfoto_studio_naplo.json")
        
        # Előre definiált stúdiódíszletek és prompt sablonok
        self.presets = {
            "workshop_woodworking": {
                "name": "Professzionális Asztalosműhely",
                "prompt": "Authentic carpentry workshop, rustic oak workbench, soft warm afternoon lighting, subtle wood shavings scattered on surface, blurred background tool wall, commercial 8k product photography, ray tracing shadows",
                "lighting": "Warm 3200K side light with soft fill",
                "best_for": ["szerszamgep", "barkacs", "epitoanyag"]
            },
            "modern_construction_site": {
                "name": "Modern Építkezési Helyszín",
                "prompt": "Modern architectural construction site, polished concrete floor, architectural blueprints and safety gear in background, sharp natural morning sunlight, clean commercial tool staging",
                "lighting": "Crisp 5500K natural daylight",
                "best_for": ["ipari_gepek", "gepeszet", "meromuszerek"]
            },
            "scandinavian_living_room": {
                "name": "Skandináv Világos Nappali",
                "prompt": "Scandinavian minimalist interior, light oak flooring, clean aesthetic, large windows with diffused morning light, modern furniture, architectural magazine quality",
                "lighting": "Diffused soft window light",
                "best_for": ["otthon", "elektronika", "vilagitas"]
            },
            "outdoor_garden_terrace": {
                "name": "Kerti Terasz és Zöld Pázsit",
                "prompt": "Sunny outdoor garden terrace, manicured green lawn in background, wooden decking, vibrant natural outdoor sunshine, lifestyle catalog look",
                "lighting": "Golden hour sunny illumination",
                "best_for": ["kerti_gepek", "ontozes", "szivattyuk"]
            },
            "luxury_marble_countertop": {
                "name": "Prémium Márvány Stúdiópult",
                "prompt": "Polished Italian Carrara marble countertop, clean reflection, subtle studio rim lighting, luxury commercial advertising quality",
                "lighting": "High-contrast studio rim light",
                "best_for": ["furdoszoba", "csaptelepek", "premium_kiegeszitok"]
            }
        }

    def generate_staging_prompt(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """FLUX.1 / Midjourney prompt generálása (1. Kérdés)"""
        name = product.get("name", "Product")
        custom = product.get("custom_staging_instructions", "").strip()
        
        preset_data = self.presets.get(self.preset_scene, self.presets["workshop_woodworking"])
        base_prompt = preset_data["prompt"]
        
        if self.staging_mode == "custom_prompt_hybrid" and custom:
            final_prompt = f"Commercial product photo of {name}, placed in {base_prompt}. Extra styling: {custom}, highly detailed, sharp focus, 8k resolution, Hasselblad shot"
        else:
            final_prompt = f"Commercial product photo of {name}, placed in {base_prompt}, photorealistic material textures, realistic contact shadow"
            
        negative_prompt = "blurry, low quality, distorted brand name, extra buttons, bad anatomy, deformed product, amateur lighting, oversaturated"
        
        return {
            "scene_name": preset_data["name"],
            "lighting_style": preset_data["lighting"],
            "final_positive_prompt": final_prompt,
            "negative_prompt": negative_prompt
        }

    def build_aspect_ratio_renders(self, product: Dict[str, Any], prompt_info: Dict[str, Any]) -> Dict[str, Any]:
        """Többcsatornás marketing képméretek és formátumok (2. Kérdés)"""
        sku = product.get("sku", "SKU-PROD")[:12]
        h = hashlib.sha256(f"{sku}-{self.preset_scene}".encode("utf-8")).hexdigest()[:8]
        base_cdn = f"https://cdn.profigepesz.hu/ai-studio/{sku}-{h}"
        
        renders = {}
        if self.aspect_ratio_mode in ["square_webshop_only"]:
            renders["1:1"] = {
                "label": "Webshop Termékgaléria Négyzetes",
                "aspect_ratio": "1:1",
                "resolution": "1080x1080",
                "format": "image/webp",
                "image_url": f"{base_cdn}_1x1.webp",
                "target_placement": "Shopify / WooCommerce 2. Kiemelt Kép"
            }
        else:
            # multi_marketing_pack vagy custom_selectable
            renders["1:1"] = {
                "label": "Webshop Termékgaléria",
                "aspect_ratio": "1:1",
                "resolution": "1080x1080",
                "format": "image/webp",
                "image_url": f"{base_cdn}_1x1.webp",
                "target_placement": "Webáruház Terméklap"
            }
            renders["4:5"] = {
                "label": "Instagram & Facebook Feed",
                "aspect_ratio": "4:5",
                "resolution": "1080x1350",
                "format": "image/webp",
                "image_url": f"{base_cdn}_4x5.webp",
                "target_placement": "Instagram Hírfolyam & Termékhirdetés"
            }
            renders["9:16"] = {
                "label": "TikTok / Instagram Reels / Story",
                "aspect_ratio": "9:16",
                "resolution": "1080x1920",
                "format": "image/webp",
                "image_url": f"{base_cdn}_9x16.webp",
                "target_placement": "Mobil Teljes Képernyős Videó Háttér"
            }
            renders["16:9"] = {
                "label": "Weboldal Főoldali Banner & YouTube",
                "aspect_ratio": "16:9",
                "resolution": "1920x1080",
                "format": "image/webp",
                "image_url": f"{base_cdn}_16x9.webp",
                "target_placement": "Felső Hero Banner & Facebook Hirdetés"
            }
            
        return renders

    def apply_branding_and_sync(self, product: Dict[str, Any], renders: Dict[str, Any]) -> Dict[str, Any]:
        """Márkajelzés és szinkronizáció feldolgozása (3. Kérdés)"""
        sku = product.get("sku", "SKU-001")
        branding_applied = {}
        
        if self.branding_mode == "trust_badge_overlay":
            branding_applied = {
                "badge_enabled": True,
                "badge_type": "3_EV_HIVATALOS_GARANCIA_PECSÉT",
                "watermark_position": "Jobb alsó sarok (opacity 90%)",
                "badge_text": "3 ÉV GARANCIA | PROFIGÉPÉSZ",
                "message": "Bizalmi pecsét sikeresen ráillesztve a generált képekre."
            }
        elif self.branding_mode == "direct_gallery_sync":
            branding_applied = {
                "badge_enabled": False,
                "gallery_sync_status": "UPLOADED_TO_SHOPIFY_GALLERY",
                "gallery_position": 2,
                "message": "Kép közvetlenül közzétéve a webáruház termékgalériájában."
            }
        else:
            # interactive_preview_gallery
            token = hashlib.sha256(f"{sku}-GALLERY-PREVIEW".encode("utf-8")).hexdigest()[:10]
            branding_applied = {
                "badge_enabled": True,
                "preview_gallery_url": f"https://admin.profigepesz.hu/studio/compare?sku={sku}&token={token}",
                "high_res_download_zip": f"https://cdn.profigepesz.hu/studio/export/{sku}_all_ratios.zip",
                "message": "Előtte-utána összehasonlító galéria és ZIP letöltési csomag elkészült."
            }
            
        return branding_applied

    def process_staging(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Termék életmódkép generálás és csomagolás"""
        prompt_info = self.generate_staging_prompt(product)
        renders = self.build_aspect_ratio_renders(product, prompt_info)
        branding = self.apply_branding_and_sync(product, renders)
        
        result = {
            "sku": product.get("sku"),
            "product_name": product.get("name"),
            "raw_input_image": product.get("raw_image_url"),
            "background_removal_status": "SUCCESS_SUBJECT_ISOLATED",
            "staging_scene": prompt_info["scene_name"],
            "lighting": prompt_info["lighting_style"],
            "ai_prompt_metadata": {
                "positive_prompt": prompt_info["final_positive_prompt"],
                "negative_prompt": prompt_info["negative_prompt"]
            },
            "generated_renders_count": len(renders),
            "marketing_renders": renders,
            "branding_and_sync": branding,
            "generated_at": datetime.datetime.now().isoformat()
        }
        
        self._log_studio_run(result)
        return result

    def _log_studio_run(self, record: Dict[str, Any]) -> None:
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
        """Hub belépési pont"""
        prod = payload.get("product", payload)
        res = self.process_staging(prod)
        return {
            "status": "success",
            "module_id": "07_ai_termekfoto_studio_eletmodkepek_genera",
            "processed_at": datetime.datetime.now().isoformat(),
            "studio_result": res
        }

def run(payload: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Szabványos hub belépési pont"""
    effective_config = dict(config or {})
    if "config" in payload and isinstance(payload["config"], dict):
        effective_config.update(payload["config"])
        
    handler = AiProductPhotoStudioHandler(effective_config)
    return handler.execute(payload)

if __name__ == "__main__":
    sample = {
        "product": {
            "sku": "BOSCH-GSR-18V-55",
            "name": "Bosch Professional GSR 18V-55 Akkus Fúrócsavarozó",
            "raw_image_url": "https://cdn.profigepesz.hu/raw/bosch_white.jpg"
        }
    }
    res = run(sample)
    print(json.dumps(res, indent=2, ensure_ascii=False))