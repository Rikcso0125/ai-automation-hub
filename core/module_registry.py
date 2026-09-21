# -*- coding: utf-8 -*-
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.execution_logger import get_module_config, get_tenant_module_config

BASE_MODULES_DIR = Path(__file__).resolve().parent.parent / "modules"

CATEGORY_NAMES = {
    "altalanos": "1. Általános & Pénzügy",
    "szolgaltatok": "2. Szolgáltató Cégek",
    "kereskedok": "3. Kereskedő Cégek",
    "webshopok": "4. Webshop & E-commerce",
    "muszaki": "5. Gyártás & Műszaki"
}

def scan_modules(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    modules = []
    if not BASE_MODULES_DIR.exists():
        return modules

    for path in BASE_MODULES_DIR.glob("**/*/manifest.json"):
        module_dir = path.parent
        try:
            with open(path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            
            schema_path = module_dir / "config.schema.json"
            schema = {}
            if schema_path.exists():
                with open(schema_path, "r", encoding="utf-8") as f:
                    schema = json.load(f)

            readme_path = module_dir / "README.md"
            readme_content = ""
            if readme_path.exists():
                with open(readme_path, "r", encoding="utf-8") as f:
                    readme_content = f.read()

            test_payload_path = module_dir / "test_payload.json"
            test_payload = {}
            if test_payload_path.exists():
                with open(test_payload_path, "r", encoding="utf-8") as f:
                    test_payload = json.load(f)

            module_id = manifest.get("id", module_dir.name)
            
            # Alapértelmezett értékek kigyűjtése a sémából
            default_config = {}
            for prop_name, prop_data in schema.get("properties", {}).items():
                if "default" in prop_data:
                    default_config[prop_name] = prop_data["default"]

            saved_config = get_module_config(module_id)
            tenant_config = get_tenant_module_config(user_id, module_id) if user_id else {}
            effective_config = {**default_config, **saved_config, **tenant_config}

            # Ellenőrizzük a kötelező mezők kitöltöttségét
            required_fields = schema.get("required", [])
            missing_fields = []
            for rf in required_fields:
                val = effective_config.get(rf)
                if val is None or (isinstance(val, str) and not val.strip()):
                    missing_fields.append(rf)

            has_handler = (module_dir / "handler.py").exists()

            if not has_handler:
                status = "draft"
                status_text = "Tervezés alatt"
            elif not effective_config.get("_is_active", True):
                status = "disabled"
                status_text = "Kikapcsolva"
            elif missing_fields:
                status = "needs_setup"
                status_text = f"Beállítás szükséges ({len(missing_fields)} hiányzó adat)"
            else:
                status = "active"
                status_text = "Aktív & Üzemkész"

            modules.append({
                "id": module_id,
                "title": manifest.get("title", module_dir.name),
                "category": manifest.get("category", "altalanos"),
                "category_name": CATEGORY_NAMES.get(manifest.get("category", "altalanos"), "Egyéb"),
                "icon": manifest.get("icon", "⚡"),
                "description": manifest.get("description", ""),
                "version": manifest.get("version", "1.0.0"),
                "dir_path": str(module_dir),
                "has_handler": has_handler,
                "status": status,
                "status_text": status_text,
                "missing_fields": missing_fields,
                "schema": schema,
                "config": effective_config,
                "saved_config": saved_config,
                "readme": readme_content,
                "test_payload": test_payload
            })
        except Exception as e:
            print(f"Hiba a modul betöltésekor: {path}: {e}")

    # Rendezés kategória és név szerint
    modules.sort(key=lambda m: (m["category"], m["title"]))
    return modules

def get_module_by_id(module_id: str, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    for m in scan_modules(user_id=user_id):
        if m["id"] == module_id or Path(m["dir_path"]).name == module_id:
            return m
    return None
