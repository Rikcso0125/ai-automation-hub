# -*- coding: utf-8 -*-
"""
AI Automation Hub - FastAPI Server
Központi munkafolyamat-motor és webes adminisztrációs felület.
"""
import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, Any, Optional

from core.module_registry import scan_modules, get_module_by_id
from core.execution_logger import save_module_config, get_recent_logs, get_stats, get_module_config
from core.webhook_dispatcher import dispatch_event

app = FastAPI(
    title="AI Automation Hub",
    description="Vállalati AI automatizációs és munkafolyamat motor",
    version="1.0.0"
)

# Statikus fájlok kiszolgálása a web mappából
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "web")), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    index_file = BASE_DIR / "web" / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Web dashboard nem található!")
    with open(index_file, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/v1/modules")
async def list_modules():
    return scan_modules()

@app.get("/api/v1/modules/{module_id}")
async def get_module(module_id: str):
    m = get_module_by_id(module_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"A(z) '{module_id}' modul nem található!")
    return m

class ConfigUpdateRequest(BaseModel):
    config: Dict[str, Any]
    is_active: bool = True

@app.post("/api/v1/modules/{module_id}/config")
async def update_module_config(module_id: str, req: ConfigUpdateRequest):
    m = get_module_by_id(module_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"A(z) '{module_id}' modul nem található!")
    save_module_config(module_id, req.config, req.is_active)
    return {"status": "success", "module_id": module_id, "message": "Beállítások sikeresen mentve."}

@app.post("/api/v1/modules/{module_id}/toggle")
async def toggle_module(module_id: str):
    m = get_module_by_id(module_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"A(z) '{module_id}' modul nem található!")
    cfg = m.get("config", {})
    saved_cfg = m.get("saved_config", {})
    current_active = cfg.get("_is_active", True)
    new_active = not current_active
    save_module_config(module_id, saved_cfg, new_active)
    return {
        "status": "success",
        "module_id": module_id,
        "is_active": new_active,
        "message": f"Modul sikeresen {'bekapcsolva' if new_active else 'kikapcsolva'}."
    }

@app.post("/api/v1/modules/{module_id}/test")
async def test_module(module_id: str, request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    
    # Ha üres, töltsük be az alapértelmezett teszt payload-ot
    if not body:
        m = get_module_by_id(module_id)
        if m and m.get("test_payload"):
            body = m["test_payload"]

    res = await dispatch_event(module_id, body)
    return res

@app.post("/api/v1/webhook/{module_id}")
async def receive_webhook(module_id: str, request: Request):
    try:
        payload = await request.json()
    except Exception:
        payload = {"raw_body": (await request.body()).decode("utf-8", errors="ignore")}

    res = await dispatch_event(module_id, payload)
    return res

@app.get("/api/v1/logs")
async def get_logs(limit: int = 50, module_id: Optional[str] = None):
    return get_recent_logs(limit=limit, module_id=module_id)

@app.get("/api/v1/stats")
async def get_dashboard_stats():
    return get_stats()

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print(">>> AI AUTOMATION HUB INDUL...")
    print(">>> Nyissa meg a bongeszoben: http://localhost:8000")
    print(">>> Swagger API Dokumentacio: http://localhost:8000/docs")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
