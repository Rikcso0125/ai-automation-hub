# -*- coding: utf-8 -*-
import time
import importlib.util
from pathlib import Path
from typing import Dict, Any, Optional
from core.module_registry import get_module_by_id
from core.execution_logger import log_execution, get_module_config

async def dispatch_event(module_id: str, payload: Dict[str, Any], tenant_user_id: Optional[int] = None) -> Dict[str, Any]:
    module_info = get_module_by_id(module_id, user_id=tenant_user_id)
    if not module_info:
        raise ValueError(f"Ismeretlen modul azonosító: {module_id}")

    module_dir = Path(module_info["dir_path"])
    handler_path = module_dir / "handler.py"
    if not handler_path.exists():
        raise FileNotFoundError(f"A(z) {module_id} modulhoz nem található handler.py fájl!")

    config = module_info.get("config", {})
    if not config.get("_is_active", True):
        return {
            "status": "skipped",
            "message": f"A(z) {module_id} modul jelenleg ki van kapcsolva.",
            "module_id": module_id
        }

    start_time = time.time()
    try:
        # Dinamikus handler importálás
        spec = importlib.util.spec_from_file_location(f"module_{module_id}", handler_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "run_async"):
            result = await module.run_async(payload, config)
        elif hasattr(module, "run"):
            result = module.run(payload, config)
        else:
            raise AttributeError("A handler.py nem tartalmaz 'run' vagy 'run_async' függvényt!")

        duration_ms = int((time.time() - start_time) * 1000)
        log_execution(module_id, "success", duration_ms, payload, result)

        return {
            "status": "success",
            "module_id": module_id,
            "duration_ms": duration_ms,
            "data": result
        }

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        err_msg = str(e)
        log_execution(module_id, "error", duration_ms, payload, None, error_message=err_msg)
        return {
            "status": "error",
            "module_id": module_id,
            "duration_ms": duration_ms,
            "error": err_msg
        }
